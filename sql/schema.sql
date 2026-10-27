PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS source_artifact (
 artifact_id TEXT PRIMARY KEY, url TEXT NOT NULL, retrieved_at TEXT NOT NULL,
 sha256 TEXT NOT NULL, path TEXT NOT NULL, content_type TEXT,
 UNIQUE(url,sha256)
);
CREATE TABLE IF NOT EXISTS ingestion_run (
 run_id TEXT PRIMARY KEY, source TEXT NOT NULL, started_at TEXT NOT NULL,
 finished_at TEXT, status TEXT NOT NULL, row_count INTEGER DEFAULT 0,
 detail TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS service_request (
 request_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, closed_at TEXT,
 agency TEXT NOT NULL, service TEXT NOT NULL, borough TEXT NOT NULL,
 community_district TEXT NOT NULL, incident_zip TEXT, status TEXT,
 artifact_id TEXT NOT NULL REFERENCES source_artifact(artifact_id)
);
CREATE INDEX IF NOT EXISTS request_created ON service_request(created_at);
CREATE TABLE IF NOT EXISTS policy_candidate (
 source_id TEXT PRIMARY KEY, title TEXT NOT NULL, event_date TEXT,
 domain TEXT NOT NULL, source_url TEXT NOT NULL, source_type TEXT NOT NULL,
 artifact_id TEXT NOT NULL REFERENCES source_artifact(artifact_id),
 disposition TEXT NOT NULL DEFAULT 'unreviewed'
);
CREATE TABLE IF NOT EXISTS policy (
 policy_id TEXT PRIMARY KEY, title TEXT NOT NULL, domain TEXT NOT NULL,
 agency TEXT NOT NULL, announcement_date TEXT, enactment_date TEXT,
 implementation_date TEXT, verified_status TEXT NOT NULL,
 evidence_date TEXT NOT NULL, source_url TEXT NOT NULL,
 evidence_quote TEXT NOT NULL, reviewer TEXT NOT NULL,
 artifact_id TEXT NOT NULL REFERENCES source_artifact(artifact_id),
 CHECK(verified_status IN ('announced','enacted','implementation_verified'))
);
CREATE TABLE IF NOT EXISTS policy_evidence (
 evidence_id TEXT PRIMARY KEY, policy_id TEXT NOT NULL REFERENCES policy(policy_id),
 evidence_type TEXT NOT NULL, event_date TEXT NOT NULL, source_url TEXT NOT NULL,
 evidence_quote TEXT NOT NULL, reviewer TEXT NOT NULL,
 artifact_id TEXT NOT NULL REFERENCES source_artifact(artifact_id),
 UNIQUE(policy_id,evidence_type,event_date,source_url)
);
CREATE TABLE IF NOT EXISTS policy_service_link (
 policy_id TEXT NOT NULL REFERENCES policy(policy_id), agency TEXT NOT NULL,
 service TEXT NOT NULL, rationale TEXT NOT NULL, reviewer TEXT NOT NULL,
 PRIMARY KEY(policy_id,agency,service)
);
CREATE TABLE IF NOT EXISTS socioeconomic (
 vintage TEXT NOT NULL, county_fips TEXT NOT NULL, borough TEXT NOT NULL,
 population INTEGER, poverty_universe INTEGER, poverty_count INTEGER,
 median_household_income REAL, artifact_id TEXT NOT NULL REFERENCES source_artifact(artifact_id),
 PRIMARY KEY(vintage,county_fips)
);
CREATE TABLE IF NOT EXISTS agency_performance (
 indicator_id TEXT NOT NULL, agency TEXT NOT NULL, indicator TEXT NOT NULL,
 period_start TEXT NOT NULL, period_end TEXT NOT NULL, value REAL NOT NULL,
 unit TEXT NOT NULL, direction TEXT NOT NULL, source_url TEXT NOT NULL,
 artifact_id TEXT NOT NULL REFERENCES source_artifact(artifact_id),
 PRIMARY KEY(indicator_id,period_start,period_end)
);
CREATE TABLE IF NOT EXISTS service_metrics (
 metric_id TEXT PRIMARY KEY, period TEXT NOT NULL, month TEXT NOT NULL,
 agency TEXT NOT NULL, service TEXT NOT NULL, borough TEXT NOT NULL,
 community_district TEXT NOT NULL, requests INTEGER NOT NULL,
 eligible_30d INTEGER NOT NULL, closed_30d INTEGER NOT NULL,
 unresolved_asof INTEGER NOT NULL, invalid_closure INTEGER NOT NULL,
 closed_observed INTEGER NOT NULL, closed_hours_sum REAL NOT NULL,
 median_closed_hours REAL, p90_closed_hours REAL,
 UNIQUE(period,month,agency,service,borough,community_district)
);
