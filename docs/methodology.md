# Methodology

## Population, time and geography

Study interval `[2025-10-01, 2026-10-01)`; seasonal baseline `[2024-10-01, 2025-10-01)`, New York civil time. A selected study month compares to the same month one year earlier. Fix an analysis cutoff (this build: 27 October 2026 midnight New York time) separately from retrieval time. Current mutable 311 rows are not historical snapshots.

Units: unique 311 request; canonical municipal initiative; agency × complaint type × community district × calendar month for operational cells. Community districts are administrative neighborhoods, not NTAs, tracts or ZIPs. Unspecified and unknown assignments remain visible. Profile their shares before district comparisons.

## RQ1: policy responsiveness and implementation

Include municipal initiatives with at least one announcement, enactment or verified delivery event during the study year, including initiatives originating earlier. Cover housing, transportation, sanitation, health, environment, education, public safety, economic security, government access and parks/culture. The taxonomy is an intake aid, not observed coverage.

Review independent source strata: Council laws/bills/history/event items; Mayor announcements/executive orders; adopted budget/capital commitments; agency launch/delivery reports; MMR/PMMR and program performance publications. Introduction-only discovery misses older bills adopted during the year; the event-year connector supplies additional candidates. The news crawler is bounded and always marks coverage incomplete. The accessible Council Open Data asset ends on 27 February 2025, before the study year, while automated Mayor/agency publication retrieval remains blocked. RQ1 is therefore reported as incomplete rather than treated as a zero-policy year.

Maintain `coverage_review.csv` by stratum, domain, agency and study month: searched URLs, retrieval outcome, pagination, earliest/latest publication dates, candidate/included counts, duplicate groups, exclusions, gaps and reviewer. Prefer breadth across these strata to isolated case studies. Unsearched or inaccessible domains are **not covered**, not zero-policy domains. Candidate count does not establish inventory completeness.

Canonicalize aliases to stable `policy_id` values. A bill, mayoral announcement and agency launch can be evidence for one initiative. Document whether an omnibus package or its separately actionable components are the counted units; do not count both. Exact IDs deduplicate automatically; similar titles require review. Preserve exact official URL, substantive quotation, event date, reviewer and response hash for each event. The importer checks quotation presence, but **reviewers must verify meaning, dates and factual sufficiency**. PDF-only sources currently require an official text alternative; OCR cannot silently pass.

| Stage | Required evidence | Does not establish |
|---|---|---|
| Announced | Dated official commitment or program announcement | Authorization, spending or delivery |
| Enacted | Official enacted law/order or adopted authority | Service delivery or outcomes |
| Implementation verified | Official record explicitly documenting a delivered milestone or operating service | Completion of all milestones, effectiveness or equitable reach |

Status is the highest evidenced stage before study end. Implementation date is the earliest verified delivery milestone in the evidence set; retain all events. Do not infer action dates from crawl modification times. Missing implementation dates are censored/unknown, not zero-lag or failed policies. Stage distribution, missing-date shares and source coverage precede any implementation lag analysis. The initial dashboard does not estimate survival-adjusted implementation delays.

Responsiveness is **descriptive documented alignment**. Link initiatives to exact agency/service labels with a reviewed rationale. Compare linked demand/performance and preserve unmapped needs/policies. Deduplicate service cells within each initiative. Different initiatives may share service groups, so linked demand cannot be summed across policies. Topical overlap and later metric changes do not identify policy effects.

## RQ2: metrics

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

No causal effects are estimated. Confounding, reporting access, concurrent initiatives, source revisions and service mix limit interpretation. RQ2 descriptive findings use a complete, monthly reconciled 311 production load and independent aggregate checks. RQ1 conclusions still require a complete study-year policy source review. Socioeconomic equity conclusions require geography-compatible denominators and uncertainty information that are not currently loaded.
