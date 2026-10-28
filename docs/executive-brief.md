# NYC Policy Implementation Observatory
## Executive brief

Study: October 2025–September 2026. Seasonal baseline: October 2024–September 2025. Prepared 28 October 2026.

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

### What cannot yet be answered

RQ1 cannot be answered comprehensively. The accessible Council Open Data asset ends
on 27 February 2025, before the study year, and automated Mayor/agency publication
retrieval is blocked. No complete source-verified study-year policy registry or
implementation evidence set is available. The observatory therefore reports these
as missing evidence and does not infer implementation from announcements, topical
similarity or later 311 changes.

Socioeconomic context is also incomplete. Community-district population, poverty
and income denominators have not been accepted into the production model. Current
results compare service records across administrative geographies and must not be
described as a full socioeconomic equity assessment.

---

## Operational use and next release

### Three dashboard pages

**Neighborhood Equity** will show baseline/study totals, monthly trends and borough
comparisons. **Operational Priorities** will provide the 50-row investigation queue
with agency, service, district, volume and closure-rate change. **Policy
Responsiveness** will expose verified policy evidence when available and currently
shows explicit coverage gaps, preventing an incomplete registry from appearing
complete.

### Controls on interpretation

Rates are recomputed from summed numerators and denominators. Both periods use
seasonally matched months and comparable 30-day maturity. Small cells are excluded
from the investigation queue. Median and percentile durations are not averaged
across cells. No causal effect, significance test, agency ranking or risk
probability is supplied.

### Release sequence

The complete 311 data, analysis tables and Cube semantic models are deployed to
Neon/Cube. The next release step is native Cube Dashboard authoring and visual
reconciliation against the independent totals. Policy and socioeconomic extensions
will be added only when official coverage and geography are verified; they do not
block publication of the qualified RQ2 dashboard.
