# NYC Policy Implementation Observatory

**Study:** October 2025–September 2026. 
**Seasonal baseline:** October 2024–September 2025.

**RQ1**: How did municipal initiatives align with documented service needs, and what implementation evidence exists across domains?  
**RQ2**: How did neighborhood service performance differ, and which agency–service–district combinations merit investigation?

## Delivery status

This repository contains an executable pipeline, SQLite schema, PostgreSQL publication command, six Cube models, three interactive local dashboard pages, tests, methodology, dictionary, source catalog and two-page executive **readiness** brief. **Official observations and a verified policy registry are not loaded. Nothing has been deployed to Cube Cloud.** Current Cube connections, Workbooks and native Dashboard features could not be inspected.

On 27 October 2026 the environment proxy denied access to Cube and the official NYC/Census sources. Required domains are saved in the environment configuration draft; they are not active until settings are saved and the environment is published. Cube/database bindings are absent. No starter kit was attached or available locally. See [access and delivery status](docs/access-and-delivery.md).

The dashboard displays **Unavailable**, not fabricated research results. Synthetic observations exist only in tests.

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

```bash
python3 scripts/probe_access.py
python3 -m observatory.cli ingest-311
python3 -m observatory.cli ingest-acs
python3 -m observatory.cli discover-policies
python3 -m observatory.cli discover-events
python3 -m observatory.cli discover-news --max-pages 200
# Review official candidates and populate the input CSV contracts before importing:
python3 -m observatory.cli import-policies --input data/inputs/policies.csv
python3 -m observatory.cli import-links --input data/inputs/policy_service_links.csv
python3 -m observatory.cli import-agency --input data/inputs/agency_performance.csv
python3 -m observatory.cli export --as-of 2026-10-27T00:00:00-04:00
python3 -m observatory.cli validate --as-of 2026-10-27T00:00:00-04:00
```

Full 311 ingestion spans 24 months and may require millions of rows, significant disk and time. It validates schema, uses keyset pagination, upserts IDs and reconciles monthly counts to the source. `--max-pages` creates an explicitly partial smoke run, which cannot enable priority flags. Reruns refresh mutable closures; stale/deleted source rows cause count failures for investigation rather than silent deletion. Downloads preserve HTTPS verification.

Discovery creates candidates, never implementation claims. Broad source review and deduplication follow [methodology](docs/methodology.md). News seed URLs are provisional acquisition targets, not verified working endpoints. The bounded news crawler always records incomplete coverage.

For an end-to-end connectivity check, the manually dispatched GitHub Actions workflow `Load smoke data` retrieves ACS plus one bounded 311/Council page and publishes only derived tables to Neon. It is intentionally partial and must never be described as the completed study. Store the direct Neon connection string in the repository Actions secret `NYC_DATABASE_URL`; the workflow maps it to the application's `DATABASE_URL` process variable. Never commit it.

## Cube deployment

See [deployment and feature inspection](docs/cube-deployment.md). Securely configure an authorized `DATABASE_URL`; install `python3 -m pip install -e '.[postgres]'`; run `load-postgres`. This transactionally replaces only this project's derived tables in `nyc_observatory`; verify the destination first. Cube reads the six `model/cubes/*.yml` files from the repository root; preserve existing connections/models.

The `Load production research data` GitHub Actions workflow retrieves the complete
October 2024 through September 2026 311 baseline and study window, performs monthly
source/database reconciliation, independently validates derived metrics, and then
publishes the validated aggregate tables to Neon. ACS and Council discovery report
their own outcomes and do not conceal or block the required 311 validation path.

Configure the exact `CUBE_API_URL` and a query token as `CUBE_API_TOKEN`, run `inspect-cube`, restart the server, then select **Cube REST**. Tokens stay server-side. The server rejects Cube metric counts that do not reconcile to the local evidence export. Registry/provenance still comes from that export and is labeled accordingly. A query token does not grant Cloud management permissions.

The local three-page application is separate from native Cube Dashboard objects. Native Workbooks/Dashboards require authenticated feature inspection and authoring; they have not been created.

## Verify

```bash
python3 -m unittest discover -s tests -v
npm test
python3 -m observatory.cli validate --as-of 2026-10-27T00:00:00-04:00
```

Tests cover independent expected counts, 30-day boundaries, daylight saving, matched maturity, weighted rates, future/invalid closures, request upserts, policy evidence deduplication, quotation verification, ACS county grain and filter calculations. Validation independently reconciles SQL request grain to metric cells, hashes and foreign keys. Empty-data validation is explicitly **structural only**, not research validation.

## Structure

All repository directory and file names use English ASCII names. Documentation content may be Chinese.

`observatory/`: acquisition, storage, metrics, export and server. `sql/`: tables/constraints. `model/cubes/`: six PostgreSQL-backed facts without fanout joins. `web/`: interactive pages. `data/inputs/`: review contracts. `data/raw/` and `data/processed/`: ignored source files/database/exports. `docs/`: research and deployment documentation. `reports/`: validation evidence and executive PDF. `tests/`: isolated fixtures. `scripts/`: access probe, brief generation and semantic compiler check.

Do not commit secrets, caller data, addresses, large raw datasets, or synthetic observations as research data. GitHub push/publication has not been performed.
