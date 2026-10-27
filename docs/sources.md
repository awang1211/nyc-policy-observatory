# Official source catalog

These are acquisition targets, **not retrieved/verified evidence citations**. Initial probes were denied by the proxy on 27 October 2026. Individual policy citations require source retrieval and review.

| Source | Official entry point | Intended evidence / status |
|---|---|---|
| NYC 311 | https://data.cityofnewyork.us/ | `erm2-nwe9`; metadata `/api/views/erm2-nwe9.json`; SoQL `/resource/erm2-nwe9.json`; live title/schema/coverage unverified because access blocked |
| ACS | https://api.census.gov/data/2024/acs/acs5.html | 2024 five-year NYC county estimates: 36005,36047,36061,36081,36085; blocked |
| Council Legistar | https://webapi.legistar.com/v1/nyc/Matters | Matters, study-year Events/EventItems; recorded actions are not delivery; API fields need live confirmation; blocked |
| Council laws | https://council.nyc.gov/legislation/ | Enactment/law lists, including earlier introductions; not inspected |
| Mayor records | https://www.nyc.gov/mayors-office/news | Announcements, executive orders; blocked; archive route unverified |
| Agency delivery | https://www.nyc.gov/ | HPD,DOT,DSNY,DOHMH,DEP and others; blocked; seed paths provisional |
| Parks | https://www.nycgovparks.org/news | Parks/culture breadth; not inspected |
| Public Schools | https://www.schools.nyc.gov/about-us/news/announcements | Education breadth; not inspected |
| MMR | https://www.nyc.gov/site/operations/performance/mmr.page | FY2025/FY2026 and published FY2027 partial-year indicators; not retrieved |
| OMB | https://www.nyc.gov/site/omb/index.page | Adopted/capital budgets and commitment context; not retrieved |

Complete the `coverage_review.csv` contract for source stratum × agency/domain × study month. Record retrieved URLs, pagination, publication coverage, candidates, included policies, exclusions, duplicates, gaps and reviewer. Unsearched domains are not covered, not evidence of no policy. Registry quotations must distinguish action, publication and retrieval dates. Secondary reports may aid discovery but cannot alone verify implementation in this build.
