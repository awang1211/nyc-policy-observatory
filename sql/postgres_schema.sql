CREATE SCHEMA IF NOT EXISTS nyc_observatory;

CREATE TABLE IF NOT EXISTS nyc_observatory.source_artifact (
  artifact_id text PRIMARY KEY,
  url text NOT NULL,
  retrieved_at timestamptz NOT NULL,
  sha256 text NOT NULL,
  path text NOT NULL,
  content_type text,
  UNIQUE (url, sha256)
);

CREATE TABLE IF NOT EXISTS nyc_observatory.ingestion_run (
  run_id text PRIMARY KEY,
  source text NOT NULL,
  started_at timestamptz NOT NULL,
  finished_at timestamptz,
  status text NOT NULL CHECK (status IN ('running','complete','partial','failed')),
  row_count bigint NOT NULL DEFAULT 0,
  detail jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS nyc_observatory.service_request (
  request_id text PRIMARY KEY,
  created_at timestamptz NOT NULL,
  closed_at timestamptz,
  agency text NOT NULL,
  service text NOT NULL,
  borough text NOT NULL,
  community_district text NOT NULL,
  incident_zip text,
  status text,
  artifact_id text NOT NULL REFERENCES nyc_observatory.source_artifact(artifact_id)
);
CREATE INDEX IF NOT EXISTS service_request_created_idx
  ON nyc_observatory.service_request(created_at);

CREATE TABLE IF NOT EXISTS nyc_observatory.policy_candidate (
  source_id text PRIMARY KEY,
  title text NOT NULL,
  event_date date,
  domain text NOT NULL,
  source_url text NOT NULL,
  source_type text NOT NULL,
  artifact_id text NOT NULL REFERENCES nyc_observatory.source_artifact(artifact_id),
  disposition text NOT NULL DEFAULT 'unreviewed'
);

CREATE TABLE IF NOT EXISTS nyc_observatory.policy (
  policy_id text PRIMARY KEY,
  title text NOT NULL,
  domain text NOT NULL,
  agency text NOT NULL,
  announcement_date date,
  enactment_date date,
  implementation_date date,
  verified_status text NOT NULL
    CHECK (verified_status IN ('announced','enacted','implementation_verified')),
  evidence_date date NOT NULL,
  source_url text NOT NULL,
  evidence_quote text NOT NULL,
  reviewer text NOT NULL,
  artifact_id text NOT NULL REFERENCES nyc_observatory.source_artifact(artifact_id)
);

CREATE TABLE IF NOT EXISTS nyc_observatory.policy_evidence (
  evidence_id text PRIMARY KEY,
  policy_id text NOT NULL REFERENCES nyc_observatory.policy(policy_id),
  evidence_type text NOT NULL
    CHECK (evidence_type IN ('announced','enacted','implementation_verified')),
  event_date date NOT NULL,
  source_url text NOT NULL,
  evidence_quote text NOT NULL,
  reviewer text NOT NULL,
  artifact_id text NOT NULL REFERENCES nyc_observatory.source_artifact(artifact_id),
  UNIQUE (policy_id, evidence_type, event_date, source_url)
);

CREATE TABLE IF NOT EXISTS nyc_observatory.policy_service_link (
  policy_id text NOT NULL REFERENCES nyc_observatory.policy(policy_id),
  agency text NOT NULL,
  service text NOT NULL,
  rationale text NOT NULL,
  reviewer text NOT NULL,
  PRIMARY KEY (policy_id, agency, service)
);

CREATE TABLE IF NOT EXISTS nyc_observatory.socioeconomic (
  vintage text NOT NULL,
  county_fips text NOT NULL,
  borough text NOT NULL,
  population bigint,
  poverty_universe bigint,
  poverty_count bigint,
  median_household_income double precision,
  artifact_id text NOT NULL REFERENCES nyc_observatory.source_artifact(artifact_id),
  PRIMARY KEY (vintage, county_fips)
);

CREATE TABLE IF NOT EXISTS nyc_observatory.agency_performance (
  indicator_id text NOT NULL,
  agency text NOT NULL,
  indicator text NOT NULL,
  period_start date NOT NULL,
  period_end date NOT NULL,
  value double precision NOT NULL,
  unit text NOT NULL,
  direction text NOT NULL
    CHECK (direction IN ('higher_is_better','lower_is_better','context')),
  source_url text NOT NULL,
  artifact_id text NOT NULL REFERENCES nyc_observatory.source_artifact(artifact_id),
  PRIMARY KEY (indicator_id, period_start, period_end)
);

CREATE TABLE IF NOT EXISTS nyc_observatory.service_metrics (
  metric_id text PRIMARY KEY,
  period text NOT NULL CHECK (period IN ('baseline','study')),
  month text NOT NULL,
  agency text NOT NULL,
  service text NOT NULL,
  borough text NOT NULL,
  community_district text NOT NULL,
  requests bigint NOT NULL CHECK (requests >= 0),
  eligible_30d bigint NOT NULL CHECK (eligible_30d >= 0),
  closed_30d bigint NOT NULL CHECK (closed_30d >= 0),
  unresolved_asof bigint NOT NULL CHECK (unresolved_asof >= 0),
  invalid_closure bigint NOT NULL CHECK (invalid_closure >= 0),
  closed_observed bigint NOT NULL CHECK (closed_observed >= 0),
  closed_hours_sum double precision NOT NULL CHECK (closed_hours_sum >= 0),
  median_closed_hours double precision,
  p90_closed_hours double precision,
  UNIQUE (period, month, agency, service, borough, community_district),
  CHECK (closed_30d <= eligible_30d),
  CHECK (eligible_30d <= requests),
  CHECK (unresolved_asof <= requests),
  CHECK (invalid_closure <= requests)
);

