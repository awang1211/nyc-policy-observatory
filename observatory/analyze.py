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
