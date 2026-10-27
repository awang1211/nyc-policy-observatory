import calendar
import csv
import hashlib
import io
import json
import os
import re
import uuid
from datetime import date
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse, urljoin, urlunparse
from .config import ROOT, BASELINE_START, STUDY_END, STUDY_START, COUNTIES, domain_for
from .http import fetch_json, fetch, SourceError
from .storage import archive, now

SOCRATA = 'https://data.cityofnewyork.us'
LEGISTAR = 'https://webapi.legistar.com/v1/nyc'

def months(start, end):
    current = date.fromisoformat(start)
    stop = date.fromisoformat(end)
    while current < stop:
        nxt = date(current.year + (current.month == 12), current.month % 12 + 1, 1)
        yield current.isoformat(), min(nxt, stop).isoformat()
        current = nxt

def run_source(db, source, operation):
    run_id = str(uuid.uuid4())
    db.execute('INSERT INTO ingestion_run(run_id,source,started_at,status) VALUES (?,?,?,?)',
               (run_id, source, now(), 'running'))
    db.commit()
    try:
        count, detail = operation()
        status = 'complete' if detail.get('complete', True) else 'partial'
    except Exception as error:
        db.execute('UPDATE ingestion_run SET finished_at=?,status=?,detail=? WHERE run_id=?',
                   (now(), 'failed', json.dumps({'error_type': type(error).__name__}), run_id))
        db.commit()
        raise
    db.execute('UPDATE ingestion_run SET finished_at=?,status=?,row_count=?,detail=? WHERE run_id=?',
               (now(), status, count, json.dumps(detail), run_id))
    db.commit()
    return {'run_id': run_id, 'status': status, 'rows': count, **detail}

def ingest_311(db, max_pages=None, page_size=10000):
    """Keyset pagination in monthly partitions. Reruns upsert current source rows.

    No offsets, personal addresses, coordinates, caller data, or descriptions.
    A complete run means all pages were read, not an immutable source snapshot.
    """
    def operation():
        metadata, _ = fetch_json(db, SOCRATA + '/api/views/erm2-nwe9.json')
        fields = {col['fieldName'] for col in metadata['columns']}
        requested = ['unique_key', 'created_date', 'closed_date', 'agency',
                     'complaint_type', 'borough', 'community_board', 'incident_zip', 'status']
        if not set(requested) <= fields:
            raise SourceError('311 schema drift: required fields absent; inspect archived metadata')
        headers = {'X-App-Token': os.environ['SOCRATA_APP_TOKEN']} if os.getenv('SOCRATA_APP_TOKEN') else {}
        count = pages = 0
        reconciliation = []
        for start, end in months(BASELINE_START, STUDY_END):
            cursor = None
            while True:
                where = f"created_date >= '{start}T00:00:00' AND created_date < '{end}T00:00:00'"
                if cursor:
                    # IDs/dates originate from the source; quote literals safely.
                    d, k = [str(v).replace("'", "''") for v in cursor]
                    where += f" AND (created_date > '{d}' OR (created_date = '{d}' AND unique_key > '{k}'))"
                query = {'$select': ','.join(requested), '$where': where,
                         '$order': 'created_date ASC,unique_key ASC', '$limit': page_size}
                rows, artifact = fetch_json(db, SOCRATA + '/resource/erm2-nwe9.json?' + urlencode(query), headers)
                if not isinstance(rows, list):
                    raise SourceError('311 did not return a row array')
                if not rows:
                    break
                for row in rows:
                    db.execute('INSERT INTO service_request VALUES (?,?,?,?,?,?,?,?,?,?) '
                               'ON CONFLICT(request_id) DO UPDATE SET '
                               'closed_at=excluded.closed_at,agency=excluded.agency,service=excluded.service,'
                               'borough=excluded.borough,community_district=excluded.community_district,'
                               'incident_zip=excluded.incident_zip,status=excluded.status,artifact_id=excluded.artifact_id',
                               (str(row['unique_key']), row['created_date'], row.get('closed_date'),
                                row.get('agency') or 'UNKNOWN', row.get('complaint_type') or 'UNKNOWN',
                                row.get('borough') or 'UNKNOWN', row.get('community_board') or 'UNKNOWN',
                                row.get('incident_zip'), row.get('status'), artifact))
                db.commit()
                count += len(rows)
                pages += 1
                nxt = rows[-1]['created_date'], str(rows[-1]['unique_key'])
                if nxt == cursor:
                    raise SourceError('311 cursor did not advance')
                cursor = nxt
                print(f'311 {start}: {count:,} rows fetched', flush=True)
                if max_pages and pages >= max_pages:
                    return count, {'complete': False, 'pages': pages, 'reason': 'page limit',
                                   'start': BASELINE_START, 'end_exclusive': STUDY_END}
            totals, _ = fetch_json(db, SOCRATA + '/resource/erm2-nwe9.json?' + urlencode({
                '$select': 'count(*) AS n', '$where':
                f"created_date >= '{start}T00:00:00' AND created_date < '{end}T00:00:00'"}), headers)
            expected = int(totals[0]['n'])
            actual = db.execute('SELECT COUNT(*) FROM service_request WHERE created_at>=? AND created_at<?',
                                (start,end)).fetchone()[0]
            reconciliation.append({'month_start':start,'source_rows':expected,'database_rows':actual})
            if expected != actual:
                raise SourceError('311 monthly source/database row counts differ; inspect late changes or stale rows')
        return count, {'complete': True, 'pages': pages, 'start': BASELINE_START,
                       'end_exclusive': STUDY_END, 'dataset_id': 'erm2-nwe9',
                       'monthly_reconciliation': reconciliation}
    return run_source(db, '311', operation)

def ingest_acs(db):
    # One vintage for both periods prevents denominator-vintage drift.
    def operation():
        fields = ['NAME', 'B01003_001E', 'B17001_001E', 'B17001_002E', 'B19013_001E']
        url = 'https://api.census.gov/data/2024/acs/acs5?' + urlencode({
            'get': ','.join(fields), 'for': 'county:*', 'in': 'state:36'})
        try:
            rows, artifact = fetch_json(db, url)
            records = [dict(zip(rows[0], values)) for values in rows[1:]]
            source_mode = 'Census API'
        except SourceError:
            # api.census.gov sometimes serves an HTML denial page to hosted
            # runners. The table-based ACS summary files are an independent
            # official Census distribution channel for the same estimates.
            base = ('https://www2.census.gov/programs-surveys/acs/summary_file/'
                    '2024/table-based-SF/data/5YRData/')
            table_fields = {
                'b01003': ('B01003_001E',),
                'b17001': ('B17001_001E', 'B17001_002E'),
                'b19013': ('B19013_001E',),
            }
            merged = {}
            artifacts = []
            for table, wanted in table_fields.items():
                bulk_url = base + f'acsdt5y2024-{table}.dat'
                body, mime = fetch(bulk_url, {'Accept': 'text/csv,text/plain,*/*'})
                artifacts.append(archive(db, bulk_url, body, mime))
                reader = csv.DictReader(io.StringIO(body.decode('utf-8-sig')))
                for item in reader:
                    geoid = item.get('GEO_ID', '')
                    if not geoid.startswith('0500000US36'):
                        continue
                    county = geoid[-3:]
                    if county not in COUNTIES:
                        continue
                    row = merged.setdefault(county, {'county': county, 'NAME': item.get('NAME', '')})
                    for key in wanted:
                        row[key] = item.get(key)
            records = list(merged.values())
            artifact = artifacts[0]
            source_mode = 'Census table-based summary files'
        count = 0
        for row in records:
            if row['county'] not in COUNTIES:
                continue
            def number(key):
                val = row.get(key)
                return int(val) if val is not None and int(val) >= 0 else None
            db.execute('INSERT OR REPLACE INTO socioeconomic VALUES (?,?,?,?,?,?,?,?)',
                       ('2024 ACS 5-year', row['county'], COUNTIES[row['county']],
                        number('B01003_001E'), number('B17001_001E'), number('B17001_002E'),
                        number('B19013_001E'), artifact))
            count += 1
        if count != 5:
            raise SourceError('ACS did not return all five NYC counties')
        db.commit()
        return count, {'complete': True, 'geography': 'county/borough',
                       'vintage': '2024 ACS 5-year', 'distribution': source_mode}
    return run_source(db, 'acs', operation)

def ingest_legislation(db, max_pages=None):
    """Broad discovery of introductions, NOT an implementation registry.

    Existing bills adopted during the study year must additionally be captured
    from Council event records/official law lists during source review.
    """
    def operation():
        count = pages = skip = 0
        while True:
            query = {'$filter': f"MatterIntroDate ge datetime'{STUDY_START}T00:00:00' and MatterIntroDate lt datetime'{STUDY_END}T00:00:00'",
                     '$orderby': 'MatterId', '$top': 1000, '$skip': skip}
            rows, artifact = fetch_json(db, LEGISTAR + '/Matters?' + urlencode(query))
            if not isinstance(rows, list):
                raise SourceError('Legistar did not return a row array')
            if not rows:
                break
            for row in rows:
                title = row.get('MatterTitle') or row.get('MatterName') or 'Untitled matter'
                db.execute('INSERT OR REPLACE INTO policy_candidate '
                           '(source_id,title,event_date,domain,source_url,source_type,artifact_id) '
                           'VALUES (?,?,?,?,?,?,?)',
                           ('legistar:' + str(row['MatterId']), title, row.get('MatterIntroDate'),
                            domain_for(title), LEGISTAR + '/Matters/' + str(row['MatterId']),
                            'legislative_introduction', artifact))
            db.commit()
            count += len(rows)
            pages += 1
            skip += len(rows)
            if max_pages and pages >= max_pages:
                return count, {'complete': False, 'pages': pages}
        return count, {'complete': True, 'pages': pages, 'scope': 'introductions only; review required'}
    return run_source(db, 'legislation_candidates', operation)

def ingest_council_events(db, max_pages=None):
    """Event-year discovery also finds actions on bills introduced before the study."""
    def operation():
        count = pages = skip = 0
        while True:
            query = {'$filter': f"EventDate ge datetime'{STUDY_START}T00:00:00' and EventDate lt datetime'{STUDY_END}T00:00:00'",
                     '$orderby': 'EventId', '$top': 200, '$skip': skip}
            events, _ = fetch_json(db, LEGISTAR+'/Events?'+urlencode(query))
            if not events:
                break
            for event in events:
                url = LEGISTAR + '/Events/' + str(event['EventId']) + '/EventItems'
                items, artifact = fetch_json(db, url)
                for item in items:
                    matter_id = item.get('EventItemMatterId')
                    if not matter_id:
                        continue
                    source_id = 'legistar-event-item:'+str(item['EventItemId'])
                    title = item.get('EventItemTitle') or item.get('EventItemMatterName') or 'Council matter'
                    db.execute('INSERT OR IGNORE INTO policy_candidate '
                               '(source_id,title,event_date,domain,source_url,source_type,artifact_id) VALUES (?,?,?,?,?,?,?)',
                               (source_id,title,event.get('EventDate'),domain_for(title),
                                LEGISTAR+'/Matters/'+str(matter_id),'legislative_event_review_required',artifact))
                    count += 1
                db.commit()
            pages += 1
            skip += len(events)
            if max_pages and pages >= max_pages:
                return count, {'complete':False,'pages':pages}
        return count, {'complete':True,'pages':pages,'scope':'Council event items; agendas are not implementation evidence'}
    return run_source(db,'council_event_candidates',operation)

class NewsHTML(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.dates=[]; self.canonical=None; self.title=[]; self.in_title=False
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='a' and attrs.get('href'): self.links.append(attrs['href'])
        if tag=='meta' and (attrs.get('property','').lower() in ('article:published_time','datepublished') or
                            attrs.get('name','').lower() in ('date','datepublished','dc.date','dcterms.created')):
            self.dates.append(attrs.get('content','')[:10])
        if tag=='time' and attrs.get('datetime'): self.dates.append(attrs['datetime'][:10])
        if tag=='link' and attrs.get('rel')=='canonical': self.canonical=attrs.get('href')
        if tag=='title':self.in_title=True
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
    def handle_data(self,text):
        if self.in_title:self.title.append(text)

def discover_official_news(db, seed_file, max_pages=200):
    """Bounded official archive traversal. Only dated articles become candidates.

    Never treats a publication as a policy or infers implementation from keywords.
    Coverage is recorded per seed; manual archive/pagination review is required.
    """
    def operation():
        queue=[]
        for row in csv_rows(seed_file):
            official_url(row['url']);queue.append((row['url'],0))
        seen=set(); failures=[]; count=0
        while queue and len(seen)<max_pages:
            url,depth=queue.pop(0)
            parsed=urlparse(url)
            url=urlunparse((parsed.scheme,parsed.netloc,parsed.path,'',parsed.query,''))
            if url in seen:continue
            seen.add(url)
            try:
                body,mime=fetch(url)
                artifact=archive(db,url,body,mime)
            except SourceError:
                failures.append(url);continue
            parser=NewsHTML();parser.feed(body.decode('utf-8',errors='replace'))
            published=next((d for d in parser.dates if re.fullmatch(r'\d{4}-\d{2}-\d{2}',d)),None)
            if published and STUDY_START<=published<STUDY_END:
                canonical=urljoin(url,parser.canonical) if parser.canonical else url
                official_url(canonical)
                title=' '.join(''.join(parser.title).split()) or canonical
                source_id='official-news:'+hashlib.sha256(canonical.encode()).hexdigest()
                db.execute('INSERT OR IGNORE INTO policy_candidate '
                           '(source_id,title,event_date,domain,source_url,source_type,artifact_id) VALUES (?,?,?,?,?,?,?)',
                           (source_id,title,published,domain_for(title),url,'official_publication_review_required',artifact))
                db.commit();count+=1
            if depth<1:
                for link in parser.links:
                    target=urljoin(url,link)
                    if urlparse(target).hostname==parsed.hostname and any(s in target.lower() for s in ('/news/','press','release')):
                        queue.append((target,depth+1))
        return count, {'complete':False,'pages':len(seen),'remaining_urls':len(queue),
                       'failed_urls':failures,'scope':'bounded discovery; pagination and article-date coverage not exhaustive'}
    return run_source(db,'official_news_candidates',operation)

def discover_open_data_catalog(db):
    """Find official NYC Open Data assets that can replace blocked source sites."""
    def operation():
        queries = [
            'American Community Survey borough poverty income',
            'City Council legislation',
            'Mayor policy initiatives',
            'agency performance indicators',
        ]
        assets = {}
        for query in queries:
            params = urlencode({'search_context': 'data.cityofnewyork.us',
                                'q': query, 'limit': 100})
            try:
                payload, _ = fetch_json(db, 'https://api.us.socrata.com/api/catalog/v1?' + params)
            except SourceError:
                payload, _ = fetch_json(db, 'https://data.cityofnewyork.us/api/catalog/v1?' + params)
            for item in payload.get('results', []):
                resource = item.get('resource', {})
                dataset_id = resource.get('id')
                if not dataset_id or resource.get('type') not in ('dataset', 'map', 'href'):
                    continue
                assets[dataset_id] = {
                    'id': dataset_id,
                    'name': resource.get('name'),
                    'description': resource.get('description'),
                    'updated_at': resource.get('updatedAt'),
                    'permalink': item.get('permalink'),
                    'publisher': item.get('classification', {}).get('domain_category'),
                }
        if not assets:
            raise SourceError('NYC Open Data catalog returned no candidate datasets')
        report = {'search_context': 'data.cityofnewyork.us',
                  'candidate_count': len(assets),
                  'candidates': sorted(assets.values(), key=lambda x: ((x['name'] or '').casefold(), x['id']))}
        from .storage import write_json
        write_json(ROOT / 'reports/open-data-catalog.json', report)
        # Surface a bounded, readable shortlist in GitHub's public run page so
        # source selection can be reviewed without exposing credentials.
        terms = ('american community survey', 'acs', 'poverty', 'income',
                 'council', 'legislation', 'performance', 'indicator')
        ranked = sorted(report['candidates'], key=lambda item: (
            -sum(term in ((item.get('name') or '') + ' ' +
                          (item.get('description') or '')).casefold() for term in terms),
            (item.get('name') or '').casefold()))
        for item in ranked[:10]:
            title = ' '.join((item.get('name') or 'Untitled dataset').split())[:180]
            print(f"::notice title=NYC Open Data candidate::{item['id']} — {title}")
        return len(assets), {'complete': True, 'queries': queries,
                             'report': 'reports/open-data-catalog.json'}
    return run_source(db, 'nyc_open_data_catalog', operation)

def inspect_open_data_sources(db):
    """Archive and expose schemas for selected official NYC Open Data assets."""
    selected = {
        '6ctv-n46c': 'City Council legislation',
        'gsj6-6rwm': 'Agency performance annual',
        'phxt-vb3r': 'Agency performance monthly',
        'xn3r-zk6y': 'Community district boundaries',
    }
    schemas = {}
    for dataset_id, label in selected.items():
        metadata, _ = fetch_json(db, f'{SOCRATA}/api/views/{dataset_id}.json')
        fields = [column.get('fieldName') for column in metadata.get('columns', [])
                  if column.get('fieldName')]
        if not fields:
            raise SourceError(f'Official dataset {dataset_id} has no machine-readable fields')
        schemas[dataset_id] = {'label': label, 'name': metadata.get('name'), 'fields': fields}
        safe_fields = ', '.join(fields[:35])
        print(f'::notice title={dataset_id} {label}::{safe_fields}')
    from .storage import write_json
    write_json(ROOT / 'reports/open-data-schemas.json', schemas)
    return {'datasets': len(schemas), 'report': 'reports/open-data-schemas.json'}

def official_url(url):
    parsed = urlparse(url)
    host = parsed.hostname or ''
    if parsed.scheme != 'https' or parsed.username or parsed.password or not (
        host == 'nyc.gov' or host.endswith('.nyc.gov') or
        host == 'legistar.com' or host.endswith('.legistar.com') or
        host in ('data.cityofnewyork.us', 'api.census.gov')):
        raise ValueError('Evidence must use an official HTTPS NYC/Census/Legistar source')

def normalized_text(body):
    text = body.decode('utf-8', errors='replace')
    text = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', ' ', text, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    return ' '.join(unescape(text).split())

def verify_quote(db, url, quote):
    official_url(url)
    if len(quote.strip()) < 20:
        raise ValueError('Provide a substantive exact evidence quotation (at least 20 characters)')
    body, mime = fetch(url)
    if ' '.join(quote.split()) not in normalized_text(body):
        raise ValueError('Evidence quotation not found in retrieved source; PDF sources need an official text alternative')
    return archive(db, url, body, mime)

def csv_rows(path):
    with open(path, newline='', encoding='utf-8') as handle:
        yield from csv.DictReader(handle)

def import_policies(db, path):
    count = 0
    for row in csv_rows(path):
        required = ['policy_id', 'title', 'domain', 'agency', 'evidence_type', 'event_date',
                    'source_url', 'evidence_quote', 'reviewer']
        if any(not row.get(key, '').strip() for key in required):
            raise ValueError('Policy evidence row has missing required fields')
        stage = row['evidence_type']
        if stage not in ('announced', 'enacted', 'implementation_verified'):
            raise ValueError('Unrecognized evidence type')
        date.fromisoformat(row['event_date'])
        if row['event_date'] >= STUDY_END:
            raise ValueError('Policy evidence after the study period is excluded')
        artifact = verify_quote(db, row['source_url'], row['evidence_quote'])
        old = db.execute('SELECT title,domain,agency FROM policy WHERE policy_id=?', (row['policy_id'],)).fetchone()
        if old and tuple(old) != tuple(row[k] for k in ('title','domain','agency')):
            raise ValueError('Conflicting policy identity; reconcile aliases before import')
        db.execute('INSERT OR IGNORE INTO policy VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                   (row['policy_id'], row['title'], row['domain'], row['agency'], None, None, None,
                    stage, row['event_date'], row['source_url'], row['evidence_quote'], row['reviewer'], artifact))
        # Explicit columns prevent schema drift from silently changing evidence.
        evidence_id = hashlib.sha256('|'.join(row[k] for k in
            ('policy_id','evidence_type','event_date','source_url')).encode()).hexdigest()
        db.execute('INSERT OR REPLACE INTO policy_evidence VALUES (?,?,?,?,?,?,?,?)',
                   (evidence_id, row['policy_id'], stage, row['event_date'], row['source_url'],
                    row['evidence_quote'], row['reviewer'], artifact))
        evidence = db.execute('SELECT * FROM policy_evidence WHERE policy_id=?', (row['policy_id'],)).fetchall()
        dates = {s: min((e['event_date'] for e in evidence if e['evidence_type'] == s), default=None)
                 for s in ('announced','enacted','implementation_verified')}
        highest = next(s for s in ('implementation_verified','enacted','announced') if dates[s])
        best = next(e for e in evidence if e['evidence_type'] == highest and e['event_date'] == dates[highest])
        db.execute('UPDATE policy SET announcement_date=?,enactment_date=?,implementation_date=?,verified_status=?, '
                   'evidence_date=?,source_url=?,evidence_quote=?,reviewer=?,artifact_id=? WHERE policy_id=?',
                   (dates['announced'], dates['enacted'], dates['implementation_verified'], highest,
                    best['event_date'], best['source_url'], best['evidence_quote'], best['reviewer'],
                    best['artifact_id'], row['policy_id']))
        db.commit()
        count += 1
    return count

def import_agency(db, path):
    count = 0
    for row in csv_rows(path):
        for key in ('indicator_id','agency','indicator','period_start','period_end','value','unit',
                    'direction','source_url','evidence_quote'):
            if not row.get(key):
                raise ValueError(f'Missing agency field: {key}')
        if row['direction'] not in ('higher_is_better','lower_is_better','context'):
            raise ValueError('Unknown indicator direction')
        start, end = date.fromisoformat(row['period_start']), date.fromisoformat(row['period_end'])
        if start >= end:
            raise ValueError('Indicator period must have positive length; end is exclusive')
        artifact = verify_quote(db, row['source_url'], row['evidence_quote'])
        db.execute('INSERT OR REPLACE INTO agency_performance VALUES (?,?,?,?,?,?,?,?,?,?)',
                   tuple(row[k] for k in ('indicator_id','agency','indicator','period_start','period_end')) +
                   (float(row['value']), row['unit'], row['direction'], row['source_url'], artifact))
        count += 1
    db.commit()
    return count

def import_links(db, path):
    count = 0
    for row in csv_rows(path):
        if any(not row.get(k) for k in ('policy_id','agency','service','rationale','reviewer')):
            raise ValueError('Policy-service links require an explicit reviewed rationale')
        db.execute('INSERT OR REPLACE INTO policy_service_link VALUES (?,?,?,?,?)',
                   tuple(row[k] for k in ('policy_id','agency','service','rationale','reviewer')))
        count += 1
    db.commit()
    return count
