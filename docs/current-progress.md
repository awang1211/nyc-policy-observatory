# Current progress

Updated 3 November 2026 (New York).

## Scope decision: RQ1 retired

As of 3 November 2026, the project drops the in-house policy-implementation
registry (formerly "RQ1") as an active research question. Reason: the
accessible Council Open Data asset ends February 2025 and automated Mayor/agency
retrieval is blocked, so the in-house pipeline could not clear its own coverage
bar. The project now
scopes itself to the 311 demand/closure monitoring and investigation-screening
layer (formerly "RQ2"). The policy evidence layer is pending; public government
sources (NYC Legistar, NYC Mayor's Management Report) are its reference points.
See `docs/data-status.md` and `docs/methodology.md` for the updated scope language.

## Resumed delivery

The user confirms a native Cube dashboard draft exists at
https://anruow.cubecloud.dev/d/1/dashboard/KNqY4COMgche. Its pages, controls and
live query results have not yet been inspected in this session: no connected
browser/Cube management tool is available. Earlier statements below about page
creation are superseded by this draft status.

Completed this session:

- Read GitHub run and job statuses: latest service load, production validation,
  Neon publication, analysis and model compilation succeeded on 28 October.
- Saved run/step evidence in `reports/workflow-evidence.json`; latest policy
  workflow failed at its real-record gate and skipped publication.
- Independently reconciled saved result arithmetic: 109/109 checks passed.
  This checks aggregate consistency, not raw/source/live completeness.
- Reran 12 Python tests and the frontend test command successfully.
- Added a three-day roadmap, Chinese Cube platform guide and demo script.

Remaining acceptance gates:

1. Inspect existing Cube draft and reconcile live metrics and filters.
2. Retrieve production validation artifact contents; the checked-in
   `reports/validation.json` contains zero rows and proves structure only.
3. Resolve midnight versus 18:20 analysis cutoff discrepancy between methods
   and production workflow using actual production provenance.
4. Review policy cases and geography-compatible context without claiming full
   registry coverage or causal effects.
5. Rehearse and preserve an access-tested demo/export backup.

See `delivery-roadmap.md`, `cube-platform-guide.zh.md` and `workflow-demo.zh.md`.

## Previous delivery record (28 October)

| Work | Status |
|---|---|
| Complete 24-month 311 load | Complete: 7,559,591 requests across both periods |
| Independent metric validation | Complete |
| Neon publication | Complete |
| Cube semantic models and query views | Complete through Git deployment |
| Neighborhood Equity analysis | Complete; native Cube page layout remains |
| Operational Priorities analysis | Complete; 50 leads published; native page remains |
| Policy Responsiveness registry | Retired from project scope (3 Nov 2026); policy evidence layer pending |
| Methods, dictionary and executive brief | Complete and updated |

## Current stage

The project is in native Cube dashboard completion and acceptance. A draft now
exists. No additional 311 collection is planned unless acceptance identifies
a material problem. Use `docs/cube-dashboard-guide.md` to complete and accept
the pages from the deployed query views.

## Formal workflows

The repository exposes five formal GitHub Actions workflows:

1. `Validate project` checks code, calculations and the local application.
2. `Load service data` retrieves and validates the complete 311 periods.
3. `Load policy and context data` attempts official policy/context retrieval and
   fails visibly when required study-period coverage is absent.
4. `Analyze research data` builds the reviewed analysis and Neon dashboard tables.
5. `Publish Cube models` compiles every dashboard query view; Cube Cloud then
   deploys `main` through its connected Git integration.

The former smoke workflow was removed because it was a development check and
could be confused with a complete research load.
