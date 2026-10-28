# Access and delivery status — 28 October 2026

Cube Cloud is connected to the repository `main` branch and to the Neon
PostgreSQL database. Git deployment has compiled and deployed the semantic
models. Neon contains the complete 24-month 311 aggregates and reviewed analysis
tables.

## Delivered

- Complete official 311 baseline and study-period load.
- Independently validated city, borough, month and neighborhood metrics.
- Dashboard-ready PostgreSQL analysis tables.
- Ten query-ready Cube views, including four reviewed analysis views.
- Three-page local application, reproducible pipeline, methods, dictionary,
  source catalog and executive brief.

## Remaining authenticated UI step

The native Cube page layouts must be created in the signed-in Cube interface.
Their exact fields, filters, notes and acceptance totals are specified in
`docs/cube-dashboard-guide.md`. This layout is not stored in the repository's
supported Cube semantic-model files.

## Evidence gaps

RQ1 is incomplete because the accessible Council dataset ends in February 2025
and automated study-period Mayor/agency publication retrieval is blocked. ACS
socioeconomic context is also unavailable from the hosted runner. These gaps
are displayed explicitly and are not replaced with estimates.
