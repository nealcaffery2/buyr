"""
Buyr — Wholesaler Sniping Tool — FastAPI Backend
Run: uvicorn main:app --reload
"""
import asyncio
import logging
from datetime import date
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

from config import settings
from address_parser import parse_address
from batchdata import BatchDataClient, Transfer

app = FastAPI(title="Buyr Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)


def get_supabase_client() -> Client:
    return supabase


def verify_secret(x_api_secret: str = Header(default="")):
    if settings.api_secret and x_api_secret != settings.api_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")


class SearchRequest(BaseModel):
    address: str
    search_id: str
    user_id: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/search", dependencies=[Depends(verify_secret)])
async def run_search(req: SearchRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(pipeline, req)
    return {"status": "started", "search_id": req.search_id}


async def pipeline(req: SearchRequest):
    sid = req.search_id

    try:
        # ── Step 1: Parse address ──────────────────────────────────────────
        await _update(sid, "parsing_address", 8)
        county, state = await parse_address(req.address, settings.google_maps_api_key)
        await _update(sid, "parsing_address", 15, parsed_county=county, parsed_state=state)

        # ── Step 2: Get wholesalers for this state ─────────────────────────
        await _update(sid, "finding_wholesalers", 20)
        wholesalers = await _get_wholesalers(state)
        if not wholesalers:
            await _update(sid, "error", 20, error=f"No wholesalers found for state {state}")
            return

        # ── Step 3: BatchData client ───────────────────────────────────────
        if not settings.batch_data_api_key:
            await _update(sid, "error", 20, error="BATCH_DATA_API_KEY not configured")
            return
        bd = BatchDataClient(settings.batch_data_api_key)

        # ── Step 4: Find transfers per wholesaler ──────────────────────────
        await _update(sid, "searching_county_records", 30)
        all_transfers: list[Transfer] = []
        pct_per_ws = 25 / max(len(wholesalers), 1)
        for i, ws_name in enumerate(wholesalers):
            try:
                transfers = await bd.find_properties_sold_by(ws_name, state, limit=50)
                all_transfers.extend(transfers)
                if transfers:
                    supabase.table("transactions").upsert(
                        _transfers_to_rows(transfers, county)
                    ).execute()
            except Exception as exc:
                logger.warning("BatchData search failed for %r: %s", ws_name, exc)
            pct = 30 + int((i + 1) * pct_per_ws)
            await _update(sid, "searching_county_records", min(pct, 55))
            await asyncio.sleep(0.3)

        # ── Step 5: Rank top buyers ────────────────────────────────────────
        await _update(sid, "ranking_buyers", 60)
        top_buyers = _rank_buyers(all_transfers)[:10]

        if not top_buyers:
            await _update(sid, "complete", 100, results=[])
            return

        # ── Step 6: Skip trace each buyer (LLC contact info) ───────────────
        await _update(sid, "skip_tracing", 75)
        enriched: list[dict] = []
        pct_per_buyer = 20 / max(len(top_buyers), 1)
        for i, buyer in enumerate(top_buyers):
            try:
                owner = await bd.skip_trace_entity(buyer["name"], state)
            except Exception as exc:
                logger.warning("Skip trace failed for %r: %s", buyer["name"], exc)
                owner = None

            contacts: list[dict] = []
            if owner:
                for p in owner.phones:
                    contacts.append({
                        "name": owner.name,
                        "address": owner.mailing_address,
                        "phone": p.get("number"),
                        "email": None,
                        "source": "batchdata",
                        "confidence": 0.8 if not p.get("dnc") else 0.4,
                    })
                for e in owner.emails:
                    contacts.append({
                        "name": owner.name,
                        "address": owner.mailing_address,
                        "phone": None,
                        "email": e.get("email"),
                        "source": "batchdata",
                        "confidence": 0.75,
                    })
                for person in owner.associated_people:
                    contacts.append({
                        "name": person.get("name"),
                        "address": owner.mailing_address,
                        "phone": None,
                        "email": None,
                        "source": "batchdata_associated",
                        "confidence": 0.3,
                    })

            buyer["registered_agent"] = owner.name if owner else None
            buyer["agent_address"] = owner.mailing_address if owner else None
            buyer["officers"] = owner.associated_people if owner else []
            buyer["contacts"] = contacts

            # Cache in Supabase
            supabase.table("llc_entities").upsert({
                "name": buyer["name"],
                "state": state,
                "registered_agent": buyer["registered_agent"],
                "agent_address": buyer["agent_address"],
                "officers": buyer["officers"],
                "opencorporates_url": None,
            }, on_conflict="name,state").execute()

            for c in contacts:
                if not (c.get("phone") or c.get("email")):
                    continue
                supabase.table("llc_contacts").upsert({
                    "llc_name": buyer["name"],
                    "agent_name": c.get("name"),
                    "agent_address": c.get("address"),
                    "phone": c.get("phone"),
                    "email": c.get("email"),
                    "source": c.get("source"),
                    "confidence": c.get("confidence"),
                }).execute()

            enriched.append(buyer)
            pct = 75 + int((i + 1) * pct_per_buyer)
            await _update(sid, "skip_tracing", min(pct, 95))
            await asyncio.sleep(0.3)

        # Attach transactions to each buyer for UI drill-down
        txn_by_buyer: dict[str, list] = defaultdict(list)
        for t in all_transfers:
            txn_by_buyer[t.grantee_name.upper()].append({
                "grantor_name": t.grantor_name,
                "property_address": t.property_address,
                "sale_date": t.sale_date,
                "sale_price": t.sale_price,
                "deed_type": t.deed_type,
            })

        for buyer in enriched:
            buyer["transactions"] = txn_by_buyer.get(buyer["name"].upper(), [])[:20]

        # ── Done ───────────────────────────────────────────────────────────
        await _update(sid, "complete", 100, results=enriched)

    except Exception as exc:
        logger.exception("Pipeline failed")
        await _update(sid, "error", 0, error=str(exc))


def _transfers_to_rows(transfers: list[Transfer], county: str) -> list[dict]:
    rows = []
    for t in transfers:
        rows.append({
            "grantor_name": t.grantor_name,
            "grantee_name": t.grantee_name,
            "property_address": t.property_address,
            "county": t.county or county,
            "state": t.state,
            "sale_date": t.sale_date,
            "sale_price": t.sale_price,
            "deed_type": t.deed_type,
            "source_county_url": t.source_url,
        })
    return rows


def _rank_buyers(transfers: list[Transfer]) -> list[dict]:
    counts: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "dates": [], "prices": []}
    )
    for t in transfers:
        key = (t.grantee_name or "").upper().strip()
        if not key or key == "UNKNOWN":
            continue
        counts[key]["count"] += 1
        if t.sale_date:
            counts[key]["dates"].append(t.sale_date)
        if t.sale_price:
            counts[key]["prices"].append(float(t.sale_price))

    today = date.today()
    scored: list[dict] = []
    for name, data in counts.items():
        recency = 0.0
        last_purchase = None
        if data["dates"]:
            last_purchase = max(data["dates"])
            try:
                last_dt = date.fromisoformat(str(last_purchase)[:10])
                days_ago = (today - last_dt).days
                recency = max(0.0, 1.0 - days_ago / 365.0)
            except ValueError:
                pass

        avg_price = sum(data["prices"]) / len(data["prices"]) if data["prices"] else None
        score = round(data["count"] * 0.6 + recency * 40, 3)

        scored.append({
            "name": name,
            "purchase_count": data["count"],
            "last_purchase": str(last_purchase) if last_purchase else None,
            "avg_price": round(avg_price, 0) if avg_price else None,
            "score": score,
        })

    return sorted(scored, key=lambda x: x["score"], reverse=True)


async def _get_wholesalers(state: str) -> list[str]:
    resp = (
        supabase.table("wholesalers")
        .select("name")
        .eq("state", state.upper())
        .execute()
    )
    return [row["name"] for row in (resp.data or [])]


async def _update(
    search_id: str,
    step: str,
    percent: int,
    results: list | None = None,
    error: str | None = None,
    parsed_county: str | None = None,
    parsed_state: str | None = None,
):
    payload: dict[str, Any] = {"step": step, "percent": percent}
    if results is not None:
        payload["results"] = results
    if error:
        payload["error"] = error
    if parsed_county:
        payload["parsed_county"] = parsed_county
    if parsed_state:
        payload["parsed_state"] = parsed_state

    supabase.table("searches").update(payload).eq("id", search_id).execute()
