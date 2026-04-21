import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export const runtime = "nodejs";

function serviceClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { persistSession: false } }
  );
}

export async function POST(req: Request) {
  if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
    return NextResponse.json(
      { error: "SUPABASE_SERVICE_ROLE_KEY not configured" },
      { status: 503 }
    );
  }

  const scraperUrl = process.env.NEXT_PUBLIC_SCRAPER_API_URL;
  if (!scraperUrl) {
    return NextResponse.json(
      { error: "NEXT_PUBLIC_SCRAPER_API_URL not configured" },
      { status: 503 }
    );
  }

  let body: { address?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const address = (body.address ?? "").trim();
  if (!address) {
    return NextResponse.json({ error: "address is required" }, { status: 400 });
  }

  const { data: row, error: insertErr } = await serviceClient()
    .from("searches")
    .insert({ input_address: address, step: "queued", percent: 0 })
    .select("id")
    .single();

  if (insertErr || !row) {
    return NextResponse.json(
      { error: insertErr?.message ?? "Failed to create search row" },
      { status: 500 }
    );
  }

  const searchId = row.id as string;

  try {
    const res = await fetch(`${scraperUrl}/api/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-secret": process.env.SCRAPER_API_SECRET ?? "",
      },
      body: JSON.stringify({ address, search_id: searchId }),
    });
    if (!res.ok) {
      const detail = await res.text().catch(() => "");
      await serviceClient()
        .from("searches")
        .update({ step: "error", percent: 0, error: `scraper ${res.status}: ${detail.slice(0, 200)}` })
        .eq("id", searchId);
      return NextResponse.json(
        { search_id: searchId, error: `Scraper returned ${res.status}` },
        { status: 502 }
      );
    }
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    await serviceClient()
      .from("searches")
      .update({ step: "error", percent: 0, error: `scraper unreachable: ${message}` })
      .eq("id", searchId);
    return NextResponse.json(
      { search_id: searchId, error: "Scraper unreachable" },
      { status: 502 }
    );
  }

  return NextResponse.json({ search_id: searchId });
}
