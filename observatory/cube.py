"""Cube REST integration. API token is server-only; never saved in reports."""
import json
import os
from urllib.parse import urlencode, urlparse
from .http import fetch, SourceError
from .storage import write_json
from .config import ROOT

def settings():
    base = os.getenv('CUBE_API_URL', '').rstrip('/')
    token = os.getenv('CUBE_API_TOKEN', '')
    if not base or not token:
        raise SourceError('Set CUBE_API_URL and CUBE_API_TOKEN securely from Cube deployment settings')
    if urlparse(base).scheme != 'https':
        raise SourceError('Cube remote endpoint must use HTTPS')
    return base, {'Authorization': token, 'Accept': 'application/json'}

def inspect_cube():
    base, headers = settings()
    body, _ = fetch(base + '/meta', headers)
    meta = json.loads(body)
    safe = {'endpoint_host': urlparse(base).hostname,
            'cubes': [{'name': c['name'], 'measures': [m['name'] for m in c.get('measures',[])],
                       'dimensions': [d['name'] for d in c.get('dimensions',[])]} for c in meta.get('cubes',[])],
            'limitations': 'REST meta does not inspect Cloud connections, Workbooks, or Dashboard feature entitlements.'}
    write_json(ROOT / 'reports/cube-inspection.json', safe)
    return safe

def service_metrics():
    base, headers = settings()
    dimensions = ['period','month','agency','service','borough','community_district']
    measures = ['requests','eligible_30d','closed_30d','unresolved_asof','invalid_closure',
                'closed_observed','closed_hours_sum']
    rows = []
    offset = 0
    while True:
        query = {'dimensions': ['ServiceMetrics.'+x for x in dimensions],
                 'measures': ['ServiceMetrics.'+x for x in measures], 'limit': 10000, 'offset': offset,
                 'order': [['ServiceMetrics.'+x, 'asc'] for x in dimensions]}
        body, _ = fetch(base + '/load?' + urlencode({'query': json.dumps(query)}), headers)
        result = json.loads(body)
        if result.get('error'):
            # Asynchronous preaggregation "Continue wait" is not empty data.
            raise SourceError('Cube load did not finish successfully; retry after deployment/preaggregation readiness')
        if 'data' not in result:
            raise SourceError('Cube response is missing data')
        page = result['data']
        for row in page:
            item = {x: row['ServiceMetrics.'+x] for x in dimensions}
            item.update({x: float(row['ServiceMetrics.'+x]) for x in measures})
            rows.append(item)
        if len(page) < 10000:
            return rows
        offset += len(page)

def load_postgres(db):
    try:
        import psycopg
        from psycopg import sql
    except ImportError:
        raise SourceError('Install optional postgres dependency: pip install -e ".[postgres]"') from None
    destination = os.getenv('DATABASE_URL')
    if not destination:
        raise SourceError('DATABASE_URL is missing')
    # One transaction, isolated namespace, no changes to other schemas.
    tables = ['source_artifact','ingestion_run','service_metrics','policy','policy_evidence',
              'policy_service_link','socioeconomic','agency_performance']
    with psycopg.connect(destination) as pg:
        pg.execute('CREATE SCHEMA IF NOT EXISTS nyc_observatory')
        for table in tables:
            cols = list(db.execute(f'PRAGMA table_info({table})'))
            definitions = []
            for c in cols:
                typ = {'TEXT':'text','INTEGER':'bigint','REAL':'double precision'}[c['type']]
                # Dates are text in SQLite, typed in Cube SQL to avoid migration ambiguity.
                definitions.append(sql.SQL('{} {}').format(sql.Identifier(c['name']), sql.SQL(typ)))
            ident = sql.Identifier('nyc_observatory', table)
            pg.execute(sql.SQL('CREATE TABLE IF NOT EXISTS {} ({})').format(ident, sql.SQL(',').join(definitions)))
            pg.execute(sql.SQL('DELETE FROM {}').format(ident))
            with pg.cursor().copy(sql.SQL('COPY {} ({}) FROM STDIN').format(ident, sql.SQL(',').join(
                    sql.Identifier(c['name']) for c in cols))) as copy:
                for row in db.execute(f'SELECT * FROM {table}'):
                    copy.write_row(tuple(row))
            pg.execute(sql.SQL('CREATE UNIQUE INDEX IF NOT EXISTS {} ON {} ({})').format(
                sql.Identifier('uq_'+table), ident, sql.SQL(',').join(sql.Identifier(c['name']) for c in cols if c['pk'])))
    return {'tables_loaded': tables, 'schema': 'nyc_observatory', 'transaction': 'committed'}
