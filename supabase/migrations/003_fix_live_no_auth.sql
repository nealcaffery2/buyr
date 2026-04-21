-- Idempotent hotfix: brings a live DB (running at migration 001 or partial 002)
-- to the expected "no-auth + shared team api keys" state.
-- Safe to re-run.

-- 1. team_api_keys: single shared row, no user_id dependency -----------------
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

DROP POLICY IF EXISTS "anon read team_api_keys"   ON team_api_keys;
DROP POLICY IF EXISTS "anon upsert team_api_keys" ON team_api_keys;
DROP POLICY IF EXISTS "anon update team_api_keys" ON team_api_keys;
DROP POLICY IF EXISTS "service read team_api_keys" ON team_api_keys;

CREATE POLICY "anon read team_api_keys"
  ON team_api_keys FOR SELECT TO anon USING (true);

CREATE POLICY "anon upsert team_api_keys"
  ON team_api_keys FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon update team_api_keys"
  ON team_api_keys FOR UPDATE TO anon USING (true);

CREATE POLICY "service read team_api_keys"
  ON team_api_keys FOR SELECT TO service_role USING (true);

INSERT INTO team_api_keys (id) VALUES ('team') ON CONFLICT (id) DO NOTHING;

-- 2. searches: drop auth-scoped policy, allow anon -------------------------
DROP POLICY IF EXISTS "own searches" ON searches;
DROP POLICY IF EXISTS "anon insert searches" ON searches;
DROP POLICY IF EXISTS "anon select searches" ON searches;
DROP POLICY IF EXISTS "anon update searches" ON searches;

CREATE POLICY "anon insert searches"
  ON searches FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon select searches"
  ON searches FOR SELECT TO anon USING (true);

-- Needed so the scraper (via the anon key) can write progress updates; the
-- UI reads them through Supabase Realtime. The scraper should prefer the
-- service_role key in production.
CREATE POLICY "anon update searches"
  ON searches FOR UPDATE TO anon USING (true) WITH CHECK (true);

-- 3. wholesalers, llc_entities, transactions, llc_contacts: anon read/write ----
DROP POLICY IF EXISTS "authenticated read wholesalers"  ON wholesalers;
DROP POLICY IF EXISTS "anon read wholesalers"           ON wholesalers;
DROP POLICY IF EXISTS "anon upsert wholesalers"         ON wholesalers;
DROP POLICY IF EXISTS "anon update wholesalers"         ON wholesalers;

CREATE POLICY "anon read wholesalers"
  ON wholesalers FOR SELECT TO anon USING (true);

CREATE POLICY "anon upsert wholesalers"
  ON wholesalers FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon update wholesalers"
  ON wholesalers FOR UPDATE TO anon USING (true);

DROP POLICY IF EXISTS "authenticated read llc_entities" ON llc_entities;
DROP POLICY IF EXISTS "anon read llc_entities"          ON llc_entities;
CREATE POLICY "anon read llc_entities"
  ON llc_entities FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS "authenticated read transactions" ON transactions;
DROP POLICY IF EXISTS "anon read transactions"          ON transactions;
CREATE POLICY "anon read transactions"
  ON transactions FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS "authenticated read llc_contacts" ON llc_contacts;
DROP POLICY IF EXISTS "anon read llc_contacts"          ON llc_contacts;
CREATE POLICY "anon read llc_contacts"
  ON llc_contacts FOR SELECT TO anon USING (true);

-- 4. Drop orphaned per-user api_keys table ---------------------------------
DROP TABLE IF EXISTS user_api_keys CASCADE;

-- 5. Realtime: ensure searches emits UPDATE events -------------------------
-- (no-op if already added; wrap in DO block to ignore errors on re-run)
DO $$
BEGIN
  BEGIN
    EXECUTE 'ALTER PUBLICATION supabase_realtime ADD TABLE searches';
  EXCEPTION WHEN duplicate_object THEN
    NULL;
  END;
END $$;
