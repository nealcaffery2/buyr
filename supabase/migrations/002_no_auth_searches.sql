-- Remove auth requirement — tool is for internal team use only.

-- Allow anon to create and read searches (user_id stays NULL)
DROP POLICY IF EXISTS "own searches" ON searches;

CREATE POLICY "anon insert searches"
  ON searches FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon select searches"
  ON searches FOR SELECT TO anon USING (true);

-- Allow anon to upload wholesalers
DROP POLICY IF EXISTS "authenticated read wholesalers" ON wholesalers;

CREATE POLICY "anon read wholesalers"
  ON wholesalers FOR SELECT TO anon USING (true);

CREATE POLICY "anon upsert wholesalers"
  ON wholesalers FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon update wholesalers"
  ON wholesalers FOR UPDATE TO anon USING (true);

-- Allow anon to read LLC data
DROP POLICY IF EXISTS "authenticated read llc_entities" ON llc_entities;
DROP POLICY IF EXISTS "authenticated read transactions" ON transactions;
DROP POLICY IF EXISTS "authenticated read llc_contacts" ON llc_contacts;

CREATE POLICY "anon read llc_entities"
  ON llc_entities FOR SELECT TO anon USING (true);

CREATE POLICY "anon read transactions"
  ON transactions FOR SELECT TO anon USING (true);

CREATE POLICY "anon read llc_contacts"
  ON llc_contacts FOR SELECT TO anon USING (true);

-- Team API keys: single shared row, no user_id dependency
CREATE TABLE IF NOT EXISTS team_api_keys (
  id text PRIMARY KEY DEFAULT 'team',
  batchdata_api_key text DEFAULT '',
  propstream_email text DEFAULT '',
  propstream_password text DEFAULT '',
  dealmachine_api_key text DEFAULT '',
  opencorporates_api_key text DEFAULT '',
  google_maps_api_key text DEFAULT '',
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE team_api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon read team_api_keys"
  ON team_api_keys FOR SELECT TO anon USING (true);

CREATE POLICY "anon upsert team_api_keys"
  ON team_api_keys FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon update team_api_keys"
  ON team_api_keys FOR UPDATE TO anon USING (true);

-- Service role can read team keys (for scraper)
CREATE POLICY "service read team_api_keys"
  ON team_api_keys FOR SELECT TO service_role USING (true);

-- Seed empty team row so upsert works
INSERT INTO team_api_keys (id) VALUES ('team') ON CONFLICT (id) DO NOTHING;
