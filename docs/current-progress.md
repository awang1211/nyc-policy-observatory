# Current progress

Updated 28 October 2026.

| Work | Status |
|---|---|
| Complete 24-month 311 load | Complete: 7,559,591 requests across both periods |
| Independent metric validation | Complete |
| Neon publication | Complete |
| Cube semantic models and query views | Complete through Git deployment |
| Neighborhood Equity analysis | Complete; native Cube page layout remains |
| Operational Priorities analysis | Complete; 50 leads published; native page remains |
| Policy Responsiveness registry | Incomplete because official study-period sources remain unavailable |
| Methods, dictionary and executive brief | Complete and updated |

## Current stage

The project is in native Cube dashboard authoring. No further 311 collection is
needed for the current study. Use `docs/cube-dashboard-guide.md` to build and
accept the three pages from the deployed query views.

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
