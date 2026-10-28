"""Reproducible descriptive analysis over validated PostgreSQL aggregates."""
import json
import os
from pathlib import Path


def analyze_postgres(output_dir='reports'):
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        raise RuntimeError('Install the postgres project dependency') from None
    destination = os.getenv('DATABASE_URL')
    if not destination:
        raise RuntimeError('DATABASE_URL is missing')

    with psycopg.connect(destination, row_factory=dict_row) as pg:
        overall = pg.execute('''
            SELECT period, SUM(requests)::bigint AS requests,
                   SUM(eligible_30d)::bigint AS eligible_30d,
                   SUM(closed_30d)::bigint AS closed_30d,
                   SUM(unresolved_asof)::bigint AS unresolved_asof,
                   SUM(closed_30d)::double precision / NULLIF(SUM(eligible_30d),0) AS closure_30d_rate
            FROM nyc_observatory.service_metrics GROUP BY period ORDER BY period
        ''').fetchall()
        borough = pg.execute('''
            SELECT borough, period, SUM(requests)::bigint AS requests,
                   SUM(eligible_30d)::bigint AS eligible_30d,
                   SUM(closed_30d)::bigint AS closed_30d,
                   SUM(closed_30d)::double precision / NULLIF(SUM(eligible_30d),0) AS closure_30d_rate
            FROM nyc_observatory.service_metrics
            GROUP BY borough, period ORDER BY borough, period
        ''').fetchall()
        monthly = pg.execute('''
            SELECT period, month, SUM(requests)::bigint AS requests,
                   SUM(eligible_30d)::bigint AS eligible_30d,
                   SUM(closed_30d)::bigint AS closed_30d,
                   SUM(closed_30d)::double precision / NULLIF(SUM(eligible_30d),0) AS closure_30d_rate
            FROM nyc_observatory.service_metrics
            GROUP BY period, month ORDER BY month, period
        ''').fetchall()
        priorities = pg.execute('''
            WITH cells AS (
              SELECT agency, service, borough, community_district,
                SUM(requests) FILTER (WHERE period='baseline')::bigint AS baseline_requests,
                SUM(requests) FILTER (WHERE period='study')::bigint AS study_requests,
                SUM(eligible_30d) FILTER (WHERE period='baseline')::bigint AS baseline_eligible,
                SUM(eligible_30d) FILTER (WHERE period='study')::bigint AS study_eligible,
                SUM(closed_30d) FILTER (WHERE period='baseline')::bigint AS baseline_closed,
                SUM(closed_30d) FILTER (WHERE period='study')::bigint AS study_closed
              FROM nyc_observatory.service_metrics
              GROUP BY agency, service, borough, community_district
            )
            SELECT *,
              baseline_closed::double precision / NULLIF(baseline_eligible,0) AS baseline_rate,
              study_closed::double precision / NULLIF(study_eligible,0) AS study_rate,
              100.0 * (study_closed::double precision / NULLIF(study_eligible,0)
                - baseline_closed::double precision / NULLIF(baseline_eligible,0)) AS change_percentage_points,
              100.0 * (study_requests::double precision / NULLIF(baseline_requests,0) - 1) AS request_change_percent
            FROM cells
            WHERE baseline_eligible >= 30 AND study_eligible >= 30 AND study_requests > 0
            ORDER BY change_percentage_points ASC NULLS LAST, study_requests DESC
            LIMIT 50
        ''').fetchall()
        metric_rows = pg.execute('SELECT COUNT(*) AS n FROM nyc_observatory.service_metrics').fetchone()['n']

        # Publish compact, reviewed analysis tables for Cube. These contain no
        # addresses or raw request records and can be replaced transactionally.
        pg.execute('''CREATE TABLE IF NOT EXISTS nyc_observatory.research_summary (
            period text PRIMARY KEY, requests bigint NOT NULL, eligible_30d bigint NOT NULL,
            closed_30d bigint NOT NULL, unresolved_asof bigint NOT NULL,
            closure_30d_rate double precision)''')
        pg.execute('''CREATE TABLE IF NOT EXISTS nyc_observatory.borough_comparison (
            borough text NOT NULL, period text NOT NULL, requests bigint NOT NULL,
            eligible_30d bigint NOT NULL, closed_30d bigint NOT NULL,
            closure_30d_rate double precision, PRIMARY KEY (borough, period))''')
        pg.execute('''CREATE TABLE IF NOT EXISTS nyc_observatory.operational_priority (
            priority_rank bigint PRIMARY KEY, agency text NOT NULL, service text NOT NULL,
            borough text NOT NULL, community_district text NOT NULL,
            baseline_requests bigint, study_requests bigint,
            baseline_eligible bigint, study_eligible bigint,
            baseline_closed bigint, study_closed bigint,
            baseline_rate double precision, study_rate double precision,
            change_percentage_points double precision, request_change_percent double precision)''')
        pg.execute('''CREATE TABLE IF NOT EXISTS nyc_observatory.research_data_status (
            dataset text PRIMARY KEY, status text NOT NULL, usable_for text NOT NULL,
            coverage text NOT NULL, limitation text NOT NULL)''')
        for table in ('research_summary', 'borough_comparison', 'operational_priority', 'research_data_status'):
            pg.execute(f'DELETE FROM nyc_observatory.{table}')
        pg.executemany('INSERT INTO nyc_observatory.research_summary VALUES (%s,%s,%s,%s,%s,%s)', [
            (row['period'], row['requests'], row['eligible_30d'], row['closed_30d'],
             row['unresolved_asof'], row['closure_30d_rate']) for row in overall])
        pg.executemany('INSERT INTO nyc_observatory.borough_comparison VALUES (%s,%s,%s,%s,%s,%s)', [
            (row['borough'], row['period'], row['requests'], row['eligible_30d'],
             row['closed_30d'], row['closure_30d_rate']) for row in borough])
        pg.executemany('INSERT INTO nyc_observatory.operational_priority VALUES (' + ','.join(['%s'] * 15) + ')', [
            (rank, row['agency'], row['service'], row['borough'], row['community_district'],
             row['baseline_requests'], row['study_requests'], row['baseline_eligible'],
             row['study_eligible'], row['baseline_closed'], row['study_closed'],
             row['baseline_rate'], row['study_rate'], row['change_percentage_points'],
             row['request_change_percent']) for rank, row in enumerate(priorities, 1)])
        pg.executemany('INSERT INTO nyc_observatory.research_data_status VALUES (%s,%s,%s,%s,%s)', [
            ('NYC 311', 'complete', 'RQ2', 'October 2024–September 2026',
             'Reported demand and administrative closure do not prove need or resolution.'),
            ('Neighborhood geography', 'identified', 'RQ2 mapping', '2020 NTA and CDTA official assets',
             'Boundary integration remains pending.'),
            ('Socioeconomic context', 'missing', 'RQ2 equity context', 'No accepted study-period load',
             'Do not infer socioeconomic equity from 311 counts alone.'),
            ('Study-year policy registry', 'missing', 'RQ1', 'Council Open Data ends February 2025',
             'No complete October 2025–September 2026 registry is available.'),
            ('Implementation evidence', 'missing', 'RQ1', 'Automated official publication access blocked',
             'Announced policy must not be labeled implemented without reviewed evidence.'),
            ('Agency performance', 'under_review', 'RQ2 context', 'Current official candidates identified',
             'Use only after 2025–2026 coverage is verified.')])

    if not overall or sum(row['requests'] for row in overall) == 0:
        raise RuntimeError('Validated service metrics are empty')
    payload = {
        'scope': {'baseline': '2024-10-01 through 2025-09-30',
                  'study': '2025-10-01 through 2026-09-30',
                  'metric_rows': metric_rows},
        'overall': overall,
        'borough': borough,
        'monthly': monthly,
        'operational_priorities': priorities,
        'interpretation_limits': [
            '311 reports measure reported demand, not all public service need or unique incidents.',
            'Closure is an administrative event and does not prove that a problem was resolved.',
            'Priority rows are descriptive screening flags, not causal findings or agency rankings.',
            'Socioeconomic context and study-period policy implementation evidence are not yet available.'
        ]
    }
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    (target / 'current-analysis.json').write_text(json.dumps(payload, indent=2, default=str) + '\n')

    periods = {row['period']: row for row in overall}
    lines = ['# Current observatory analysis', '',
             '## Available evidence', '',
             f"Validated metric rows: {metric_rows:,}.", '']
    for key in ('baseline', 'study'):
        row = periods.get(key, {})
        rate = row.get('closure_30d_rate')
        lines.append(f"- {key.title()}: {int(row.get('requests', 0)):,} requests; "
                     f"30-day closure rate {rate:.1%}." if rate is not None else
                     f"- {key.title()}: {int(row.get('requests', 0)):,} requests; rate unavailable.")
    lines += ['', '## Operational screening', '',
              f"{len(priorities)} comparable agency-service-neighborhood combinations are retained, "
              'requiring at least 30 mature requests in both periods. The JSON file preserves the top 50.', '',
              '## Limits', ''] + [f'- {item}' for item in payload['interpretation_limits']]
    (target / 'current-analysis.md').write_text('\n'.join(lines) + '\n')
    return payload


if __name__ == '__main__':
    result = analyze_postgres()
    baseline = next(row for row in result['overall'] if row['period'] == 'baseline')
    study = next(row for row in result['overall'] if row['period'] == 'study')
    print(f"::notice title=311 analysis::Baseline {baseline['requests']:,} requests; "
          f"study {study['requests']:,} requests; {len(result['operational_priorities'])} priority rows saved")
