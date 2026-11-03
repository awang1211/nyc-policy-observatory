"""Independently reconcile saved aggregates; never claims raw/live validation."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(payload):
    checks = []

    def record(name, passed):
        checks.append({'check': name, 'passed': bool(passed)})

    overall = {row['period']: row for row in payload['overall']}
    record('exactly two unique overall periods',
           set(overall) == {'baseline', 'study'} and len(payload['overall']) == 2)
    for period in ('baseline', 'study'):
        row = overall[period]
        for section, expected in (('borough', 6), ('monthly', 12)):
            parts = [r for r in payload[section] if r['period'] == period]
            key = 'borough' if section == 'borough' else 'month'
            record(f'{period}: {section} unique coverage',
                   len(parts) == expected and len({r[key] for r in parts}) == expected)
            for field in ('requests', 'eligible_30d', 'closed_30d'):
                record(f'{period}: {section} {field} reconciles',
                       sum(r[field] for r in parts) == row[field])
            if section == 'monthly':
                start_year = 2024 if period == 'baseline' else 2025
                months = {f'{start_year}-{m:02d}' for m in (10, 11, 12)}
                months |= {f'{start_year+1}-{m:02d}' for m in range(1, 10)}
                record(f'{period}: exact monthly window', {r['month'] for r in parts} == months)
    for section in ('overall', 'borough', 'monthly'):
        for i, row in enumerate(payload[section]):
            n, d = row['closed_30d'], row['eligible_30d']
            record(f'{section}[{i}]: counts and weighted rate',
                   0 <= n <= d <= row['requests'] and d > 0 and
                   math.isclose(row['closure_30d_rate'], n / d, abs_tol=1e-12))
    priorities = payload['operational_priorities']
    record('50 unique priority combinations', len(priorities) == 50 and len({
        tuple(r[k] for k in ('agency', 'service', 'borough', 'community_district'))
        for r in priorities}) == 50)
    ordering = []
    for i, row in enumerate(priorities):
        record(f'priority[{i}]: maturity and arithmetic',
               all(30 <= row[f'{p}_eligible'] <= row[f'{p}_requests'] and
                   0 <= row[f'{p}_closed'] <= row[f'{p}_eligible'] and
                   math.isclose(row[f'{p}_rate'], row[f'{p}_closed'] / row[f'{p}_eligible'], abs_tol=1e-12)
                   for p in ('baseline', 'study')) and
               math.isclose(row['change_percentage_points'],
                            100 * (row['study_rate'] - row['baseline_rate']), abs_tol=1e-10) and
               math.isclose(row['request_change_percent'],
                            100 * (row['study_requests'] / row['baseline_requests'] - 1), abs_tol=1e-10))
        ordering.append((row['change_percentage_points'], -row['study_requests']))
    record('saved priority ordering', ordering == sorted(ordering))
    return checks


if __name__ == '__main__':
    source = ROOT / 'reports/current-analysis.json'
    payload = json.loads(source.read_text())
    checks = check(payload)
    periods = {r['period']: r for r in payload['overall']}
    baseline, study = periods['baseline'], periods['study']
    report = {
        'passed': all(c['passed'] for c in checks),
        'source': 'reports/current-analysis.json',
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'qualification': 'Saved aggregate consistency only. No raw requests, live Neon, source completeness or Cube UI were revalidated.',
        'findings': {
            'total_requests': baseline['requests'] + study['requests'],
            'request_increase': study['requests'] - baseline['requests'],
            'request_change_percent': 100 * (study['requests'] / baseline['requests'] - 1),
            'closure_change_percentage_points': 100 * (study['closure_30d_rate'] - baseline['closure_30d_rate']),
        },
        'checks': checks,
    }
    (ROOT / 'reports/saved-analysis-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'checks'}, indent=2))
    print(f"{sum(c['passed'] for c in checks)}/{len(checks)} checks passed")
    raise SystemExit(0 if report['passed'] else 1)
