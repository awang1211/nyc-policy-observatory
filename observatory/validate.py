import hashlib
from datetime import timedelta
from .config import ROOT, BASELINE_START, STUDY_START, STUDY_END
from .metrics import timestamp

def validate(db, as_of):
    errors = []
    cutoff = timestamp(as_of)
    # Independently aggregate request grain in SQL rather than reuse summarize().
    db.create_function('epoch', 1, lambda x: timestamp(x).timestamp() if x else None)
    def maturity(x):
        from zoneinfo import ZoneInfo
        dt = timestamp(x).astimezone(ZoneInfo('America/New_York'))
        if x[:10] < STUDY_START:
            dt = dt.replace(year=dt.year + 1)
        return dt.timestamp() + 30 * 86400 <= cutoff.timestamp()
    db.create_function('matched_mature', 1, maturity)
    sql = '''SELECT
       COUNT(*) requests,
       SUM(CASE WHEN closed_at IS NOT NULL AND epoch(closed_at)<epoch(created_at) THEN 1 ELSE 0 END) invalid,
       SUM(CASE WHEN matched_mature(created_at) AND (closed_at IS NULL OR epoch(closed_at)>=epoch(created_at)) THEN 1 ELSE 0 END) eligible,
       SUM(CASE WHEN matched_mature(created_at) AND epoch(closed_at)>=epoch(created_at)
          AND epoch(closed_at)-epoch(created_at)<=2592000 AND epoch(closed_at)<=? THEN 1 ELSE 0 END) closed30,
       SUM(CASE WHEN epoch(closed_at)>=epoch(created_at) AND epoch(closed_at)<=? THEN 0 ELSE 1 END) unresolved
       FROM service_request WHERE created_at>=? AND created_at<? AND epoch(created_at)<=?'''
    checks = []
    for period, start, end in [('baseline', BASELINE_START, STUDY_START), ('study', STUDY_START, STUDY_END)]:
        raw = dict(db.execute(sql, (cutoff.timestamp(), cutoff.timestamp(), start, end, cutoff.timestamp())).fetchone())
        agg = dict(db.execute('SELECT SUM(requests) requests,SUM(invalid_closure) invalid,'
                              'SUM(eligible_30d) eligible,SUM(closed_30d) closed30,'
                              'SUM(unresolved_asof) unresolved FROM service_metrics WHERE period=?', (period,)).fetchone())
        raw = {k: v or 0 for k, v in raw.items()}
        agg = {k: v or 0 for k, v in agg.items()}
        checks.append({'period': period, 'request_grain_sql': raw, 'metric_table': agg, 'passed': raw == agg})
        if raw != agg:
            errors.append(f'{period} independent SQL reconciliation failed')
    violations = db.execute('SELECT COUNT(*) FROM service_metrics WHERE closed_30d>eligible_30d OR '
                            'eligible_30d>requests OR unresolved_asof>requests OR invalid_closure>requests').fetchone()[0]
    if violations:
        errors.append('Metric subset constraints failed')
    for row in db.execute('SELECT * FROM source_artifact'):
        path = ROOT / row['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            errors.append('Source artifact checksum missing/mismatched: ' + row['artifact_id'])
    fk = [tuple(r) for r in db.execute('PRAGMA foreign_key_check')]
    if fk:
        errors.append('Foreign key integrity failed')
    records = db.execute('SELECT COUNT(*) FROM service_request').fetchone()[0]
    return {'passed': not errors, 'errors': errors, 'independent_checks': checks,
            'request_rows': records, 'data_validation_executed': records > 0,
            'qualification': 'Empty data: structural checks only; no research results validated' if not records else
                             'Reconciles loaded records; does not prove source completeness or research validity'}
