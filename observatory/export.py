import csv
import json
from collections import defaultdict
from .config import ROOT, STUDY_START, STUDY_END, BASELINE_START
from .metrics import build_metrics, aggregate, ratio
from .storage import write_json, now

def export(db, as_of):
    build_metrics(db, as_of)
    metrics = [dict(r) for r in db.execute('SELECT * FROM service_metrics ORDER BY month,agency,service,community_district')]
    policies = [dict(r) for r in db.execute(
        'SELECT p.* FROM policy p WHERE EXISTS (SELECT 1 FROM policy_evidence e '
        'WHERE e.policy_id=p.policy_id AND e.event_date>=? AND e.event_date<?) ORDER BY domain,title',
        (STUDY_START, STUDY_END))]
    runs = [dict(r) for r in db.execute('SELECT * FROM ingestion_run ORDER BY started_at')]
    # Latest attempt governs readiness; a stale prior success cannot hide a failed refresh.
    latest = {r['source']: r for r in runs}
    source_status = {s: latest[s]['status'] if s in latest else 'not_loaded'
                     for s in ('311', 'acs', 'legislation_candidates')}
    full_311 = source_status['311'] == 'complete'
    # Recompute comparison from additive counts, never subgroup medians.
    groups = defaultdict(lambda: defaultdict(list))
    for row in metrics:
        groups[(row['agency'], row['service'], row['borough'], row['community_district'])][row['period']].append(row)
    priorities = []
    for dims, periods in groups.items():
        study = aggregate(periods['study'])
        baseline = aggregate(periods['baseline'])
        if not study['requests']:
            continue
        s, b = study['closure_30d_rate'], baseline['closure_30d_rate']
        change = (s - b) * 100 if s is not None and b is not None else None
        sufficient = full_311 and study['eligible_30d'] >= 30 and baseline['eligible_30d'] >= 30
        # Transparent queue; no opaque composite ranking or causal attribution.
        flag = 'review' if sufficient and change is not None and change <= -10 else (
            'no_threshold_flag' if sufficient else 'insufficient_coverage')
        priorities.append(dict(zip(('agency','service','borough','community_district'), dims)) |
                          {'study': study, 'baseline': baseline, 'closure_change_pp': change,
                           'request_change_pct': (study['requests']/baseline['requests']-1)*100 if baseline['requests'] else None,
                           'flag': flag})
    priorities.sort(key=lambda r: (r['flag'] != 'review', r['closure_change_pp'] is None,
                                   r['closure_change_pp'] or 0, -r['study']['requests']))
    counts = {table: db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] for table in
              ('policy_candidate','policy','policy_evidence','policy_service_link','service_request','agency_performance')}
    evidence = [dict(r) for r in db.execute('SELECT * FROM policy_evidence ORDER BY policy_id,event_date')]
    artifacts = [dict(r) for r in db.execute('SELECT artifact_id,url,retrieved_at,sha256,path FROM source_artifact')]
    snapshot = {
        'title': 'NYC Policy Implementation Observatory', 'study_start': STUDY_START,
        'study_end_exclusive': STUDY_END, 'baseline_start': BASELINE_START, 'as_of': as_of,
        'generated_at': now(), 'source_status': source_status, 'counts': counts,
        'readiness': 'source_backed' if full_311 else 'incomplete_source_coverage',
        'metrics': metrics, 'policies': policies, 'policy_evidence': evidence,
        'policy_links': [dict(r) for r in db.execute('SELECT * FROM policy_service_link')],
        'socioeconomic': [dict(r) for r in db.execute('SELECT * FROM socioeconomic')],
        'agency_performance': [dict(r) for r in db.execute('SELECT * FROM agency_performance')],
        'priorities': priorities, 'artifacts': artifacts, 'runs': runs,
        'limitations': [
            '311 reports measure reported demand, not all needs or unique incidents.',
            'Closure is an administrative event and does not establish resolution.',
            '30-day rates use matched mature cohorts; recent requests remain in volume counts.',
            'Historical status, reopened events, deleted records, and past extracts cannot be reconstructed from current rows.',
            'Community districts are operational neighborhoods; ACS values apply only to boroughs.',
            'No community-district population denominator or verified geographic crosswalk is loaded.',
            'Policy inventory completeness requires review across mayoral, Council, budget, and agency sources.',
            'Policy-service links describe reviewed topical alignment, not policy effects.',
            'Agency fiscal-year indicators are context and are not silently aligned to the October–September study year.',
            'Investigative flags are descriptive thresholds, not statistical significance or agency failure findings.'
        ]}
    write_json(ROOT / 'data/processed/dashboard.json', snapshot)
    for table in ('service_metrics','policy','policy_evidence','policy_service_link','socioeconomic','agency_performance','source_artifact'):
        cursor = db.execute(f'SELECT * FROM {table}')
        with (ROOT / f'data/processed/{table}.csv').open('w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow([col[0] for col in cursor.description])
            writer.writerows(cursor)
    return snapshot
