import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const scraperUrl = process.env.SCRAPER_API_URL;
  const secret = process.env.SCRAPER_API_SECRET;

  if (!scraperUrl || !secret) {
    return NextResponse.json(
      { error: "Scraper not configured" },
      { status: 503 }
    );
  }

  const body = await req.text();

  const res = await fetch(`${scraperUrl}/api/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Secret": secret,
    },
    body,
  });

  return new NextResponse(await res.text(), {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
