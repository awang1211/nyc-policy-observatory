# Cube dashboard build guide

User-confirmed existing draft:
https://anruow.cubecloud.dev/d/1/dashboard/KNqY4COMgche.
Inspect and extend this draft rather than creating a duplicate. This document
defines target acceptance, not the currently observed online layout.

The semantic layer and reviewed PostgreSQL tables are already deployed from the
`main` branch. This guide defines the native Cube dashboard layout and prevents
the authoring step from changing metric definitions or presenting a gap as a
finding.

## Shared rules

- Study period: October 2025 through September 2026.
- Seasonal baseline: October 2024 through September 2025.
- Use only the query views named below.
- Show 30-day closure as an administrative processing measure. Do not label it
  service quality, resolution, effectiveness or causation.
- Keep `Unspecified` in city totals and exclude it only from borough comparison
  charts where the title says so.
- Never replace missing policy or socioeconomic data with estimates.

## Page 1: Policy Responsiveness

1. Table from `ResearchDataStatusView`: `Dataset`, `Status`, `Usable For`,
   `Coverage`, `Limitation`.
2. Table from `PoliciesView`: `Title`, `Domain`, `Agency`, `Verified Status`,
   `Evidence Date`, `Source URL`, `Evidence Quote`.
3. Table from `PolicyEvidenceView`: `Policy ID`, `Evidence Type`, `Event Date`,
   `Source URL`, `Evidence Quote`.
4. Filters: `Domain`, `Agency`, `Verified Status`.
5. Visible note: "The accessible Council dataset ends before the study period.
   Announcements, enactment and verified implementation are kept separate. RQ1
   coverage is incomplete."

Do not add a headline policy count unless reviewed study-period policy records
exist. An empty table is an honest coverage result.

## Page 2: Neighborhood Service Performance

Use this descriptive title while socioeconomic context is missing. The earlier
name, Neighborhood Equity, exceeds what the available evidence supports.

1. Four KPI cards from `ResearchSummaryView`, filtered to `Period = study`:
   `Requests`, `Eligible 30d`, `Closed 30d`, `Closure 30d Rate`.
2. Grouped bar chart from `BoroughComparisonView`: dimension `Borough`, series
   `Period`, measure `Requests`.
3. Grouped bar chart from `BoroughComparisonView`: dimension `Borough`, series
   `Period`, measure `Closure 30d Rate`.
4. Monthly line charts from `ServiceMetricsView`: dimension `Month`, series
   `Period`, measures `Requests` and `Closure 30d Rate`.
   For seasonal overlap, derive a shared October–September month axis; actual
   year-month values with Period series do not align matching months. If that
   transformation is unavailable, show a clearly labeled continuous 24-month
   trend and do not call it an overlaid seasonal comparison.
5. Detail table from `ServiceMetricsView`: `Agency`, `Service`, `Borough`,
   `Community District`, `Period`, `Requests`, `Eligible 30d`, `Closed 30d`,
   `Closure 30d Rate`.
6. Filters: `Period`, `Month`, `Borough`, `Agency`, `Service`,
   `Community District`.

Exclude `Borough = Unspecified` from borough charts, but not citywide KPI cards.

## Page 3: Operational Priorities

1. Table from `OperationalPrioritiesView`, sorted by `Priority Rank` ascending,
   with every dimension except `Row Count`.
2. Bar chart: `Agency` with measure `Row Count`.
3. Bar chart: `Borough` with measure `Row Count`.
4. Filters: `Agency`, `Service`, `Borough`, `Community District`.
5. Visible note: "Priority rows are investigation leads based on volume and
   change in administrative closure. They are not findings of agency failure or
   policy effects."

Keep the table limited to the published 50 rows. Do not recompute ranking in Cube.

## Acceptance checks

- study requests: **3,963,901**;
- baseline requests: **3,595,690**;
- study 30-day closure: **90.3500%**;
- baseline 30-day closure: **91.0042%**;
- priority table: **50** rows;
- Policy Responsiveness visibly states the source gap;
- every page has working filters and a source/limitation note.

Compare Cube output with `reports/current-analysis.json`.
