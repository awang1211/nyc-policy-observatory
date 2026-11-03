# Methodology

## Population, time and geography

Study interval `[2025-10-01, 2026-10-01)`; seasonal baseline `[2024-10-01, 2025-10-01)`, New York civil time. A selected study month compares to the same month one year earlier. Fix an analysis cutoff (this build: 27 October 2026 midnight New York time) separately from retrieval time. Current mutable 311 rows are not historical snapshots.

Units: unique 311 request; agency × complaint type × community district × calendar month for operational cells. Community districts are administrative neighborhoods, not NTAs, tracts or ZIPs. Unspecified and unknown assignments remain visible. Profile their shares before district comparisons.

## Policy/legislative implementation evidence: out of scope

This project previously attempted to build its own policy-evidence registry
(formerly "RQ1"): reviewing Council laws/bills, Mayor announcements, budget
commitments and agency delivery reports, and staging them into `policies.csv`
and `policy_service_links.csv` for import. That attempt is retired. The
accessible Council Open Data asset ends 27 February 2025 (before the study
year) and automated Mayor/agency publication retrieval is blocked, so the
in-house pipeline could never clear its own coverage bar.

Rather than keep investing in that registry, this project points to sources
that already do it rigorously: the
[NYCuriosity Obligations Tracker](https://data.nycuriosity.com/civic_reference/legislation_implementation_tracker/)
reads enacted local-law text directly from NYC Legistar and extracts
agency-level obligations and deadlines with mechanically-verified quotations,
updated monthly and covering 2014–present (so it does not share the Council
Open Data lag). The
[NYC Mayor's Management Report](https://www.nyc.gov/site/operations/reports/mmr.page)
covers official agency performance reporting. Connecting either of those
sources to this project's 311/operational layer, for a single well-chosen
case, is a possible future direction, not a current deliverable. The staging
contracts (`data/inputs/policies.csv`, `policy_service_links.csv`) and the
`discover-policies`/`import-policies` CLI commands remain in the repository as
reference code, unused in the current scope.

## Metrics

Interpret floating 311 timestamps in `America/New_York`, convert to UTC, and calculate elapsed hours. Daylight-saving days are not always 24 elapsed hours.

| Metric | Definition |
|---|---|
| Volume | Unique request IDs created in the selected period and by cutoff |
| Matched mature cohort | Study request, or baseline request's study-year local timestamp counterpart, at least 720 elapsed hours before cutoff |
| Eligible 30-day denominator | Matched mature requests excluding negative closure durations |
| Closed within 30 days | Eligible request with closure ≥creation, ≤creation+720 hours and ≤cutoff |
| 30-day rate | Sum(closed-within-30-day)/Sum(eligible); zero denominator is unavailable |
| Rate change | 100 × (study rate − baseline rate), percentage points |
| Unresolved as of cutoff | No valid observed closure by cutoff; invalid closures remain in a separate quality count |
| Closed-time mean | Sum(valid observed closure hours)/Count(valid observed closures) |
| Closed-time median/p90 | Linear-interpolated individual closed-duration quantile within the exact cell |

Closed-time distributions exclude open requests and have selection bias. Cell medians/p90 cannot be averaged for larger populations; Cube and headline comparisons omit them. Closure may mean routing or administrative disposition rather than service resolution. Reopened events, deleted rows and historical statuses cannot be reconstructed from a latest-row extract.

At the initial cutoff, late September requests lack 30-day follow-up. Retain them in volume; exclude them and their baseline counterparts from the closure-rate denominator. Regenerate all tables/exports for a changed cutoff. Volume and closure follow-up coverage are distinct populations.

Compare the same agency/service across districts where possible. Mixed-service rates reflect service mix and do not establish neighborhood treatment differences or efficiency. Reporting propensity, repeat reports, category/routing changes, changed reporting channels and boundary changes affect comparability. The initial build does not standardize service mix, infer unique incidents, or adjust for demographics. Unresolved mappings must remain explicit.

ACS 2024 five-year estimates supply fixed-vintage **borough** population, poverty universe/count and median household income. These are pooled 2020–2024 estimates, not 2026 observations. County FIPS maps exactly to boroughs. No community-district population or geographic crosswalk is loaded. ZIP is not joined to ZCTA. Suppress borough per-capita denominators when a district filter is applied. A neighborhood socioeconomic extension needs official geography-compatible estimates/crosswalks, margins of error and allocation uncertainty. Do not imply the current borough context answers within-borough socioeconomic disparities.

Priority flags require complete source-count reconciliation, ≥30 eligible requests in each period and ≥10 percentage-point closure decline. Both thresholds are adjustable. Sort flagged rows first and then by decline. Flags are investigation thresholds, not risk probabilities, significance tests or confirmed agency failures. Review service mix, denominator sizes, missingness, closure practices, repeat incidents and corroborating staffing/budget/agency evidence. No multiple-comparison correction or interval estimate is supplied; sensitivity review is necessary before consequential allocation decisions.

## Agency indicators and fiscal alignment

MMR fiscal years run July–June. FY2026 overlaps nine study months; FY2027 Q1 covers July–September 2026 only if published and separately retrieved. Retain exact periods/units/direction. Do not add annual averages/medians to partial-year values or label FY2026 as the October–September outcome. Indicators remain context unless comparable monthly records allow recomposition.

## Quality and evidentiary limits

Archive URL, UTC retrieval time and SHA-256 for each response. Validate Socrata fields, keyset pagination, request-key upserts, monthly source counts, run status, keys and foreign keys. A latest failed/partial refresh prevents an older success from silently granting readiness. Investigate stale/deleted records rather than automatically deleting them. Multi-page downloads are not atomic snapshots.

Independent SQL reconciles request counts, denominators, closed-within-30-day, invalid closures and unresolved counts to metric cells. Known synthetic boundary fixtures separately verify software behavior. After real retrieval, additionally assess source freshness, missingness, invalid timestamps, outlier durations, geographic coverage and category drift. Empty-data checks verify structure only. Policy registry completeness and source review are independent gates from 311 completion.

No causal effects are estimated. Confounding, reporting access, concurrent initiatives, source revisions and service mix limit interpretation. The descriptive findings use a complete, monthly reconciled 311 production load and independent aggregate checks. Socioeconomic equity conclusions require geography-compatible denominators and uncertainty information that are not currently loaded. Policy implementation evidence is out of scope for this project (see above); any future linkage to it would still need its own study-year source review before supporting a responsiveness claim.
