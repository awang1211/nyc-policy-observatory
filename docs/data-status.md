# Data status

| Dataset | Intended use | Status | Decision |
|---|---|---|---|
| NYC 311, October 2024–September 2026 | Demand, service performance and operational screening | Complete and validated | Analyze now |
| Community district and NTA geography | Neighborhood labels and boundaries | Official assets identified | Integrate into dashboard |
| ACS population, poverty and income | Socioeconomic context and denominators | Not loaded | Record as a material gap; do not infer equity from 311 alone |
| Council bills and local laws | Policy/implementation evidence (out of scope) | Official Open Data ends February 2025 | Retired as an in-house source; policy evidence layer pending (reference: NYC Legistar) |
| Mayor and agency policy publications | Policy/implementation evidence (out of scope) | Automated sites block hosted retrieval | Retired as an in-house source; point to the NYC Mayor's Management Report instead |
| Agency performance indicators | Cross-check operational performance | Current candidate assets under review | Load only if 2025–2026 fields are verified |

The project proceeds with a complete descriptive analysis from validated 311
records: demand, closure performance and an investigation-screening queue.
Policy/legislative implementation evidence is out of scope for this project's
own pipeline; rather than keep sourcing and reviewing it in-house, the project
treats it as a pending layer, with public government sources (NYC Legistar,
NYC Mayor's Management Report) as reference points. Missing
sources are never replaced with estimates, inferred policy status, or
unsupported causal claims.
