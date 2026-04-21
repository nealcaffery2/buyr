-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Wholesaler LLCs (user-uploaded + auto-discovered)
CREATE TABLE IF NOT EXISTS wholesalers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  state char(2) NOT NULL DEFAULT '',
  source text DEFAULT 'user_sheet',
  created_at timestamptz DEFAULT now(),
  UNIQUE (name, state)
);

-- LLC data from OpenCorporates
CREATE TABLE IF NOT EXISTS llc_entities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  state char(2),
  registered_agent text,
  agent_address text,
  officers jsonb DEFAULT '[]',
  opencorporates_url text,
  raw jsonb DEFAULT '{}',
  fetched_at timestamptz DEFAULT now(),
  UNIQUE (name, state)
);

-- Deed transactions from county recorders
-- grantor = wholesaler (seller), grantee = cash buyer (end buyer)
CREATE TABLE IF NOT EXISTS transactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  grantor_name text,
  grantee_name text,
  property_address text,
  county text,
  state char(2),
  sale_date date,
  sale_price numeric,
  deed_type text,
  source_county_url text,
  scraped_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_transactions_grantee ON transactions (grantee_name);
CREATE INDEX IF NOT EXISTS idx_transactions_grantor ON transactions (grantor_name);
CREATE INDEX IF NOT EXISTS idx_transactions_state ON transactions (state);
CREATE INDEX IF NOT EXISTS idx_transactions_sale_date ON transactions (sale_date DESC);

-- Contact info for buyer LLCs
CREATE TABLE IF NOT EXISTS llc_contacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  llc_name text NOT NULL,
  agent_name text,
  agent_address text,
  phone text,
  email text,
  source text,
  confidence int DEFAULT 0,
  fetched_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_llc_contacts_name ON llc_contacts (llc_name);

-- Per-user API keys (stored encrypted via Supabase Vault in production)
CREATE TABLE IF NOT EXISTS user_api_keys (
  user_id uuid PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
  batchdata_api_key text DEFAULT '',
  propstream_email text DEFAULT '',
  propstream_password text DEFAULT '',
  dealmachine_api_key text DEFAULT '',
  opencorporates_api_key text DEFAULT '',
  google_maps_api_key text DEFAULT '',
  updated_at timestamptz DEFAULT now()
);

-- Search log with Realtime progress tracking
CREATE TABLE IF NOT EXISTS searches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users ON DELETE SET NULL,
  input_address text,
  parsed_county text,
  parsed_state char(2),
  step text DEFAULT 'queued',
  percent int DEFAULT 0,
  results jsonb,
  error text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_searches_user ON searches (user_id, created_at DESC);

-- Seed: known wholesaler LLCs by state
INSERT INTO wholesalers (name, state, source) VALUES
  ('NEW WESTERN ACQUISITIONS LLC', 'TX', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'GA', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'NC', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'TN', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'FL', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'OH', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'MO', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'IN', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'OK', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'CO', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'AL', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'KY', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'SC', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'AR', 'seed'),
  ('NEW WESTERN ACQUISITIONS LLC', 'KS', 'seed'),
  ('HOMEVESTORS OF AMERICA INC', 'TX', 'seed'),
  ('HOMEVESTORS OF AMERICA INC', 'GA', 'seed'),
  ('HOMEVESTORS OF AMERICA INC', 'NC', 'seed'),
  ('HOMEVESTORS OF AMERICA INC', 'TN', 'seed'),
  ('HOMEVESTORS OF AMERICA INC', 'FL', 'seed'),
  ('OPENDOOR LABS INC', 'TX', 'seed'),
  ('OPENDOOR LABS INC', 'GA', 'seed'),
  ('OPENDOOR LABS INC', 'NC', 'seed'),
  ('OPENDOOR LABS INC', 'TN', 'seed'),
  ('OPENDOOR LABS INC', 'FL', 'seed'),
  ('OFFERPAD SPE BORROWER LLC', 'TX', 'seed'),
  ('OFFERPAD SPE BORROWER LLC', 'GA', 'seed'),
  ('OFFERPAD SPE BORROWER LLC', 'AZ', 'seed'),
  ('OFFERPAD SPE BORROWER LLC', 'FL', 'seed'),
  ('OFFERPAD SPE BORROWER LLC', 'NC', 'seed'),
  ('INVITATION HOMES TX LLC', 'TX', 'seed'),
  ('INVITATION HOMES GA LLC', 'GA', 'seed'),
  ('INVITATION HOMES FL LLC', 'FL', 'seed'),
  ('PROGRESS RESIDENTIAL LLC', 'TX', 'seed'),
  ('PROGRESS RESIDENTIAL LLC', 'GA', 'seed'),
  ('PROGRESS RESIDENTIAL LLC', 'AZ', 'seed'),
  ('PROGRESS RESIDENTIAL LLC', 'FL', 'seed'),
  ('WE BUY HOUSES LLC', 'TX', 'seed'),
  ('WE BUY HOUSES LLC', 'FL', 'seed'),
  ('WE BUY HOUSES LLC', 'GA', 'seed'),
  ('WHOLESALING INC LLC', 'TN', 'seed'),
  ('BPROPERTY LLC', 'TX', 'seed'),
  ('BUYPROPERLY LTD', 'TX', 'seed'),
  ('NOVATION REAL ESTATE LLC', 'TX', 'seed'),
  ('NOVATION REAL ESTATE LLC', 'GA', 'seed')
ON CONFLICT (name, state) DO NOTHING;

-- RLS policies
ALTER TABLE wholesalers ENABLE ROW LEVEL SECURITY;
ALTER TABLE llc_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE llc_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE searches ENABLE ROW LEVEL SECURITY;

-- Authenticated users can read shared data
CREATE POLICY "authenticated read wholesalers"
  ON wholesalers FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated read llc_entities"
  ON llc_entities FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated read transactions"
  ON transactions FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated read llc_contacts"
  ON llc_contacts FOR SELECT TO authenticated USING (true);

-- Users only see their own searches and API keys
CREATE POLICY "own searches"
  ON searches FOR ALL TO authenticated
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY "own api keys"
  ON user_api_keys FOR ALL TO authenticated
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- Service role can write everything (used by Python scraper)
CREATE POLICY "service write wholesalers"
  ON wholesalers FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "service write llc_entities"
  ON llc_entities FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "service upsert llc_entities"
  ON llc_entities FOR UPDATE TO service_role USING (true);

CREATE POLICY "service write transactions"
  ON transactions FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "service write llc_contacts"
  ON llc_contacts FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "service update searches"
  ON searches FOR UPDATE TO service_role USING (true);
