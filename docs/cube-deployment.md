# Cube deployment

Cube workspace: `https://anruow.cubecloud.dev/d/1`.

Cube Cloud is connected to the GitHub `main` branch. The `nyc_observatory`
PostgreSQL source points to Neon, and Cube reads semantic definitions from
`model/cubes/`. Git pushes deploy the hosted semantic layer automatically.

## Published analysis views

- `ResearchSummaryView`: baseline and study-period headline totals.
- `BoroughComparisonView`: comparable borough totals and closure rates.
- `OperationalPrioritiesView`: 50 ranked investigation leads.
- `ResearchDataStatusView`: explicit source coverage and limitations.
- `ServiceMetricsView`: month, agency, service, borough and community-district
  detail.
- Policy, evidence, link, socioeconomic and agency-performance views are also
  available, but may be empty where source coverage is incomplete.

`Publish Cube models` compiles all ten query views before Cube Cloud deploys the
Git commit. Native page layouts are built in the signed-in interface using
`docs/cube-dashboard-guide.md`.

## Reconciliation targets

| Metric | Expected value |
|---|---:|
| Baseline requests | 3,595,690 |
| Study requests | 3,963,901 |
| Baseline 30-day closure | 91.0042% |
| Study 30-day closure | 90.3500% |
| Operational priority rows | 50 |

The rates are administrative closure measures. They do not establish service
quality, policy effectiveness or causation.
