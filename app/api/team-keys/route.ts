import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const ALLOWED_FIELDS = [
  "batchdata_api_key",
  "propstream_email",
  "propstream_password",
  "dealmachine_api_key",
  "opencorporates_api_key",
  "google_maps_api_key",
] as const;

type AllowedField = (typeof ALLOWED_FIELDS)[number];

function serviceClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
}

export async function GET() {
  if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
    return NextResponse.json({}, { status: 200 });
  }
  const { data, error } = await serviceClient()
    .from("team_api_keys")
    .select(ALLOWED_FIELDS.join(","))
    .eq("id", "team")
    .single();

  if (error && error.code !== "PGRST116") {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json(data ?? {});
}

export async function POST(req: Request) {
  if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
    return NextResponse.json({ error: "Service role key not configured" }, { status: 503 });
  }

  const raw = await req.json();

  // Allowlist: only persist known key columns — nothing else
  const payload: Partial<Record<AllowedField, string>> = {};
  for (const field of ALLOWED_FIELDS) {
    if (typeof raw[field] === "string") {
      payload[field] = raw[field];
    }
  }

  const { error } = await serviceClient()
    .from("team_api_keys")
    .upsert(
      { id: "team", ...payload, updated_at: new Date().toISOString() },
      { onConflict: "id" }
    );

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ ok: true });
}
