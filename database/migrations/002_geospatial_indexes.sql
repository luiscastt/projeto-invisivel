-- Execute after the API's first startup has created its tables.
ALTER TABLE reports ALTER COLUMN moderation_status TYPE varchar(32);
-- Stored expression keeps a single authoritative latitude/longitude pair.
ALTER TABLE issues ADD COLUMN IF NOT EXISTS location geometry(Point,4326)
GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(longitude,latitude),4326)) STORED;
CREATE INDEX IF NOT EXISTS issues_location_gix ON issues USING gist(location);
CREATE INDEX IF NOT EXISTS issues_title_trgm_idx ON issues USING gin(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS issue_summary_trgm_idx ON issues USING gin(summary gin_trgm_ops);
