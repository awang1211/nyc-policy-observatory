# NYC Policy Implementation Observatory

**Study:** October 2025–September 2026.  
**Seasonal baseline:** October 2024–September 2025.

**Research question**: How did NYC 311 service demand and administrative closure
performance differ across boroughs, agencies, services and community districts
between the study year and the seasonal baseline, and which agency–service–district
combinations merit a closer, manual investigation?

This project is a descriptive **monitoring and investigation-screening tool** for
NYC 311 service data. It does not itself track or verify city policy/legislative
implementation. For that layer, see external sources such as the
[NYCuriosity Obligations Tracker](https://data.nycuriosity.com/civic_reference/legislation_implementation_tracker/)
(enacted local laws mapped to agency obligations and deadlines, updated monthly)
and the [NYC Mayor's Management Report](https://www.nyc.gov/site/operations/reports/mmr.page)
(official agency performance reporting). A prior, broader version of this project
attempted to build its own policy-evidence registry (formerly "RQ1"); that attempt
is retired in favor of pointing to sources that already do it well, and possible
collaboration to connect the two layers.

## Delivery status

Current delivery notes (1 November 2026, New York): the user has an existing
[Cube dashboard draft](https://anruow.cubecloud.dev/d/1/dashboard/KNqY4COMgche).
Its live layout and filters still require inspection; earlier notes that native
pages do not exist are superseded. Start with the
[three-day roadmap](docs/delivery-roadmap.md),
[Cube platform guide](docs/cube-platform-guide.zh.md), and
[end-to-end demonstration](docs/workflow-demo.zh.md).
Recorded GitHub run/step evidence is in `reports/workflow-evidence.json`.
`reports/validation.json` is an older empty-data structural check, not production
validation evidence. Run `python3 scripts/check_saved_analysis.py` to reconcile
the saved aggregate results; this does not revalidate raw data or live Cube.

This repository now contains a validated 24-month NYC 311 pipeline, PostgreSQL
publication, independent analysis, fourteen Cube cubes/views, three interactive
local dashboard pages, tests, methodology, dictionary, source catalog and an
executive brief. Cube Cloud is connected to GitHub and Neon, and the deployed
semantic layer can query the complete 311 baseline and study periods.

The project has a source-backed descriptive result: 3,595,690 baseline requests and
3,963,901 study-period requests, with the weighted 30-day administrative closure
rate moving from 91.0% to 90.4%. Fifty agency-service-district combinations are
retained as investigation leads, ranked by volume and change in closure rate. These
are descriptive screening flags, not findings of agency failure, need, or policy
effect. Policy and socioeconomic evidence remain out of scope for this repository's
own pipeline; they are displayed as a coverage gap in the "Policy Responsiveness"
Cube page rather than filled with estimates, pending a decision on whether to
retire that page or repoint it to an external source.

## Run locally

Python 3.11+; Node 24 for frontend tests. Core execution uses Python's standard library; no package installation is necessary from this checkout.

```bash
cd /workspace/nyc-policy-observatory
python3 -m observatory.cli init
python3 -m observatory.cli export --as-of 2026-10-27T00:00:00-04:00
python3 -m observatory.cli serve --port 8000
```

Use the existing checkout: cloud tasks are already isolated; no worktree is needed. `.env.example` documents secure process bindings; the app does not automatically load `.env`.

## Populate after source access is enabled

The `ingest-311` and `ingest-acs` commands are the active pipeline for this
project's scope (311 demand/performance monitoring). The `discover-policies`,
`discover-events`, `discover-news` and `import-policies`/`import-links` commands
below are retained code for the retired policy-registry attempt; they are not
part of the current research question and do not need to run. Use
[NYCuriosity](https://data.nycuriosity.com/civic_reference/legislation_implementation_tracker/)
or the NYC Mayor's Management Report instead for policy/implementation evidence.

```bash
python3 scripts/probe_access.py
python3 -m observatory.cli ingest-311
python3 -m observatory.cli ingest-acs
python3 -m observatory.cli discover-policies       # retired scope, kept for reference
python3 -m observatory.cli discover-events          # retired scope, kept for reference
python3 -m observatory.cli discover-news --max-pages 200   # retired scope, kept for reference
# Review official candidates and populate the input CSV contracts before importing:
python3 -m observatory.cli import-policies --input data/inputs/policies.csv   # retired scope
python3 -m observatory.cli import-links --input data/inputs/policy_service_links.csv   # retired scope
python3 -m observatory.cli import-agency --input data/inputs/agency_performance.csv
python3 -m observatory.cli export --as-of 2026-10-27T00:00:00-04:00
python3 -m observatory.cli validate --as-of 2026-10-27T00:00:00-04:00
```

Full 311 ingestion spans 24 months and may require millions of rows, significant disk and time. It validates schema, uses keyset pagination, upserts IDs and reconciles monthly counts to the source. `--max-pages` creates an explicitly partial smoke run, which cannot enable priority flags. Reruns refresh mutable closures; stale/deleted source rows cause count failures for investigation rather than silent deletion. Downloads preserve HTTPS verification.

Discovery creates candidates, never implementation claims. Broad source review and deduplication follow [methodology](docs/methodology.md). News seed URLs are provisional acquisition targets, not verified working endpoints. The bounded news crawler always records incomplete coverage.

The former smoke workflow has been removed to avoid confusing a bounded test
with a research result. Formal analysis uses the complete production load. Store the
direct Neon connection string in the repository Actions secret
`NYC_DATABASE_URL`; workflows map it to `DATABASE_URL`. Never commit it.

## Cube deployment

See [deployment and feature inspection](docs/cube-deployment.md). Cube reads the
files under `model/cubes/` from the repository root. Reviewed analysis tables
provide dashboard-ready totals, borough comparisons, 50 operational priorities
and explicit source-coverage status.

The `Load production research data` GitHub Actions workflow retrieves the complete
October 2024 through September 2026 311 baseline and study window, performs monthly
source/database reconciliation, independently validates derived metrics, and then
publishes the validated aggregate tables to Neon. ACS and Council discovery report
their own outcomes and do not conceal or block the required 311 validation path.

Configure the exact `CUBE_API_URL` and a query token as `CUBE_API_TOKEN`, run `inspect-cube`, restart the server, then select **Cube REST**. Tokens stay server-side. The server rejects Cube metric counts that do not reconcile to the local evidence export. Registry/provenance still comes from that export and is labeled accordingly. A query token does not grant Cloud management permissions.

The local three-page application is separate from native Cube Dashboard objects.
The semantic models required for the three native pages are deployed according
to prior delivery records; a native dashboard draft also exists per the user.
Of the three pages, **Neighborhood Equity** and **Operational Priorities** are
the project's current scope. **Policy Responsiveness** reflects the retired
policy-registry attempt and currently shows an honest coverage gap (no rows);
pending a decision, it should either be dropped from the demo rotation or
relabeled to point at NYCuriosity/DMMR instead of implying in-house coverage.
Use the
[Cube dashboard build guide](docs/cube-dashboard-guide.md) for the exact native
page fields, filters, caveats and acceptance totals.

## Verify

```bash
python3 -m unittest discover -s tests -v
npm test
python3 -m observatory.cli validate --as-of 2026-10-27T00:00:00-04:00
```

Tests cover independent expected counts, 30-day boundaries, daylight saving, matched maturity, weighted rates, future/invalid closures, request upserts, policy evidence deduplication, quotation verification, ACS county grain and filter calculations. Validation independently reconciles SQL request grain to metric cells, hashes and foreign keys. Empty-data validation is explicitly **structural only**, not research validation.

## Structure

All repository directory and file names use English ASCII names. Documentation content may be Chinese.

`observatory/`: acquisition, storage, metrics, analysis and server. `sql/`:
tables/constraints. `model/cubes/`: PostgreSQL-backed cubes and query views.
`web/`: interactive pages. `data/inputs/`: review contracts. `docs/`: research
and deployment documentation. `reports/`: analysis and validation evidence.
`tests/`: isolated fixtures. `scripts/`: brief generation and model checks.

Do not commit secrets, caller data, addresses, large raw datasets, or synthetic
observations as research data.
