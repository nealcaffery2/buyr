-- Fix P0: team_api_keys must not be readable or writable by the anon role.
-- The anon key is embedded in the client bundle, so anon SELECT/INSERT/UPDATE
-- would expose all API credentials to anyone who inspects the bundle.
-- Reads and writes now go through the /api/team-keys server route, which uses
-- the service_role key (server-only, never sent to the browser).

DROP POLICY IF EXISTS "anon read team_api_keys"   ON team_api_keys;
DROP POLICY IF EXISTS "anon upsert team_api_keys" ON team_api_keys;
DROP POLICY IF EXISTS "anon update team_api_keys" ON team_api_keys;
