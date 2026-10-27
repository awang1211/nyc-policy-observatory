# Data dictionary

Null means unknown/unavailable, not zero. Periods have inclusive starts/exclusive ends. Raw/processed files are excluded from Git.

| Table / grain | Fields and meaning | Constraints / provenance |
|---|---|---|
| `source_artifact`: exact response | `artifact_id` = URL/content hash identity; `url`; UTC `retrieved_at`; `sha256`; relative `path`; `content_type` | Immutable bytes, unique URL/hash |
| `ingestion_run`: source attempt | UUID `run_id`; `source`; start/finish UTC; `status`; `row_count`; JSON `detail` | Running/complete/partial/failed; 311 monthly source reconciliation |
| `service_request`: 311 request | `request_id`=unique_key; `created_at`=created_date; `closed_at`=closed_date; `agency`; `service`=complaint_type; `borough`; `community_district`=community_board; `incident_zip`; latest `status`; `artifact_id` | Unique request; missing labels UNKNOWN; no caller/address/free text; mutable source |
| `policy_candidate`: discovered source event | `source_id`; `title`; `event_date`; intake `domain`; `source_url`; `source_type`; `disposition`; `artifact_id` | Not a unique-policy inventory; provisional title tags |
| `policy`: canonical initiative | `policy_id`; `title`; primary `domain`; lead `agency`; earliest announcement/enactment/implementation dates; `verified_status`; highest-stage `evidence_date`, `source_url`, `evidence_quote`, `reviewer`, `artifact_id` | Highest evidenced stage; selected into study by a study-year evidence event |
| `policy_evidence`: evidence event | Hash `evidence_id`; `policy_id`; `evidence_type`; `event_date`; `source_url`; `evidence_quote`; `reviewer`; `artifact_id` | Unique policy/type/date/URL; all historical evidence retained |
| `policy_service_link`: reviewed mapping | Composite `policy_id`,`agency`,`service`; `rationale`; `reviewer` | Exact service labels; many policies may overlap; no automatic fanout joins |
| `socioeconomic`: county/vintage | Composite `vintage`,`county_fips`; `borough`; `population` B01003_001E; `poverty_universe` B17001_001E; `poverty_count` B17001_002E; `median_household_income` B19013_001E; `artifact_id` | Negative Census sentinels→null; income in vintage dollars; no district estimates or MOEs |
| `agency_performance`: indicator/period | Composite `indicator_id`,`period_start`,`period_end`; `agency`; `indicator`; numeric `value`; `unit`; `direction`; `source_url`; `artifact_id` | Direction higher_is_better/lower_is_better/context; actual fiscal period; quote checked at import |
| `service_metrics`: monthly cell | Hash `metric_id`; `period` study/baseline; `month` YYYY-MM; agency/service/borough/community district | Unique tuple; regenerated for one explicit cutoff |

| Metric field | Unit / definition | Aggregation |
|---|---|---|
| `requests` | Unique requests | Sum disjoint cells |
| `eligible_30d` | Matched mature requests minus negative durations | Sum |
| `closed_30d` | Eligible valid closure ≤720 elapsed hours | Sum; subset of eligible |
| `unresolved_asof` | No valid observed closure by cutoff | Sum |
| `invalid_closure` | Negative closure duration | Sum, quality flag |
| `closed_observed` | Valid recorded closures by cutoff | Sum |
| `closed_hours_sum` | Elapsed hours of observed closures | Sum |
| `median_closed_hours`, `p90_closed_hours` | Exact-cell closed-only quantiles | **Not additive: recompute from raw request grain** |
| `closure_30d_rate` | Closed_30d / eligible_30d | Ratio of summed counts |
| `mean_closed_hours` | Hours sum / closed observed | Ratio of sums |
| `closure_change_pp` | 100 × (study rate − baseline rate) | Recompute after filtering |

`dashboard.json` carries study boundaries, explicit cutoff, generation timestamp, source status, readiness, metric cells, registry/evidence/links, ACS, agency indicators, source URL/hash metadata and limitations. Default priorities are a convenience; interactive thresholds recompute from metric counts. CSV files preserve artifact IDs. The browser receives only the export/API, not database credentials. Cube mode replaces metric rows only after key-level count reconciliation; registry and provenance remain from the same local export.
