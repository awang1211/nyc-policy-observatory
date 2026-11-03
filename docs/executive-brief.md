# NYC Policy Implementation Observatory
## Executive brief

Study: October 2025–September 2026. Seasonal baseline: October 2024–September 2025. Updated 3 November 2026.

### Scope

This project monitors NYC 311 service demand and administrative closure
performance, and screens for agency-service-district combinations worth a
closer look. It does not track or verify policy/legislative implementation
itself. For that layer, see the
[NYCuriosity Obligations Tracker](https://data.nycuriosity.com/civic_reference/legislation_implementation_tracker/)
(enacted local laws mapped to agency obligations, updated monthly) or the
[NYC Mayor's Management Report](https://www.nyc.gov/site/operations/reports/mmr.page).
An earlier version of this brief treated policy-implementation tracking as a
primary research question; that scope is retired here.

### What the available evidence shows

The validated NYC 311 extract contains 3,595,690 baseline requests and 3,963,901
study-period requests, an increase of 10.2%. The weighted share of mature requests
with an administrative closure recorded within 30 days moved from 91.0% to 90.4%,
a decline of 0.65 percentage points. Unresolved-as-of-cutoff records increased by
83,031. These measures describe reported demand and administrative processing;
they do not prove unmet need, service resolution or agency effectiveness.

Request volume increased in every named borough. The 30-day closure rate declined
by 1.80 percentage points in the Bronx and 1.19 points in Brooklyn, changed little
in Queens, and increased slightly in Manhattan and Staten Island. Fifty comparable
agency-service-community-district combinations were retained for investigation,
each with at least 30 mature requests in both periods. Several DOB boiler cells
show large declines, but classification or workflow changes must be checked before
interpreting them as operational deterioration.

### What this project does not answer

Policy and legislative implementation evidence is out of scope for this
project's own pipeline. An earlier attempt to build an in-house registry
stalled because the accessible Council Open Data asset ends 27 February 2025
(before the study year) and automated Mayor/agency publication retrieval is
blocked. Rather than keep investing in that registry, the project points to
external sources that already cover it well (NYCuriosity, DMMR) and treats
connecting those sources to the 311/operational layer below as a possible
future collaboration, not a current deliverable.

Socioeconomic context is also incomplete. Community-district population, poverty
and income denominators have not been accepted into the production model. Current
results compare service records across administrative geographies and must not be
described as a full socioeconomic equity assessment.

---

## Operational use and next release

### Dashboard pages

**Neighborhood Equity** shows baseline/study totals, monthly trends and borough
comparisons. **Operational Priorities** provides the 50-row investigation queue
with agency, service, district, volume and closure-rate change. These two pages
are this project's current scope. A third page, **Policy Responsiveness**, is a
holdover from the retired policy-registry attempt; it honestly shows an empty
table rather than fabricate coverage, but it is being dropped from the active
demo rotation or repointed to NYCuriosity/DMMR rather than presented as an
in-house capability.

### Controls on interpretation

Rates are recomputed from summed numerators and denominators. Both periods use
seasonally matched months and comparable 30-day maturity. Small cells are excluded
from the investigation queue. Median and percentile durations are not averaged
across cells. No causal effect, significance test, agency ranking or risk
probability is supplied.

### Release sequence

The complete 311 data, analysis tables and Cube semantic models are deployed to
Neon/Cube. The next release step is native Cube Dashboard authoring and visual
reconciliation against the independent totals. A socioeconomic extension would be
added only if official geography-compatible denominators are verified. Policy
implementation evidence is not planned as an in-house extension; if pursued, it
would take the form of linking to an external source such as NYCuriosity rather
than rebuilding one.
