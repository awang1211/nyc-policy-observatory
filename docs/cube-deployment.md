# Cube inspection and deployment

Requested workspace: https://anruow.cubecloud.dev/d/1. Proxy denial occurred before an authentication response. Connections, deployed models, Workbooks and Dashboard feature availability **could not be inspected**. No Cube/database bindings were present. The web route is not evidence of a semantic REST endpoint or management permissions.

## Inspect once authenticated access is available

Record workspace/deployment identity, active branch/model version; connections, engines and read-only schemas; existing cubes/views, measures, joins, access controls and preaggregations; Workbook inventory; native Dashboard entitlement/authoring, filters/drilldowns and sharing. Preserve existing objects and avoid model-name collisions.

`inspect-cube` reads deployment REST `/meta` and saves safe cube/measure/dimension names. It does not inspect Cloud management objects, Workbooks or Dashboard features. A semantic query token is distinct from a Cloud management credential. Do not invent unsupported native object APIs.

## Publish project data and models

1. Enable source access in environment settings, save and publish, then retry actual operations.
2. Retrieve/review sources; export and validate at one cutoff.
3. Securely configure an authorized `DATABASE_URL` reachable by Cube. Install `python3 -m pip install -e '.[postgres]'`.
4. Run `python3 -m observatory.cli load-postgres`. It creates `nyc_observatory`, transactionally replaces only its project-derived tables and creates unique indexes. No raw request/address dataset is published. The loader has not been tested against a real destination. Give Cube SELECT access to project tables.
5. Cube reads `model/cubes/*.yml` from the repository root. Use the existing deployment's supported branch/development workflow and PostgreSQL connection; preserve existing models. Compile, deploy and inspect generated SQL.
6. Reconcile request/eligible/closure counts and rates with `service_metrics.csv` for the same cutoff. Never join policy links to operational facts and then sum without deduplication.
7. Configure the exact versioned REST base as `CUBE_API_URL` and a scoped query token as `CUBE_API_TOKEN`. Run `inspect-cube`; restart the local server to inherit bindings. Select **Cube REST**. Its count rows must exactly reconcile to the local export. Registry/provenance remain local and are labeled.
8. Create native Workbooks/Dashboard pages only through confirmed supported APIs/UI. Native deployment is outstanding until this succeeds.

| Page | Evidence and interaction |
|---|---|
| Policy Responsiveness | Domain/stage inventory, evidence drilldown, matched monthly demand, reviewed service links; citywide policy registry not geographically coded |
| Neighborhood Equity | District rates, paired denominators, borough ACS context; month/borough/agency/service/district filters; no borough denominator for a district |
| Operational Priorities | Agency/service/district comparisons, minimum denominator and decline thresholds, search, filtered JSON export and investigation detail; agency indicators retain actual periods |

The local application implements these three separate pages and shared controls. It is not a native Cube Dashboard object. Native domain/stage filters and source timelines must be authored after feature inspection. Six separate Cube facts avoid fanout; ratios use summed counts. Cell medians/p90 are not additive measures. Policies use a study-year evidence-existence filter. Evidence-event row counts must not be labeled unique policy counts.

Cloud feature inspection, database integration, runtime REST execution and native authoring remain unverified. Local compiler checks are separate evidence, not deployment readiness.
