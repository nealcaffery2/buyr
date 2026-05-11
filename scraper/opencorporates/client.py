"""
OpenCorporates API client.
Free tier: 500 requests/day. Paid: unlimited.
Endpoint: GET /v0.4/companies/search
"""
import logging
import httpx
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

BASE = "https://api.opencorporates.com/v0.4"

STATE_JURISDICTION = {
    "AL": "us_al", "AK": "us_ak", "AZ": "us_az", "AR": "us_ar", "CA": "us_ca",
    "CO": "us_co", "CT": "us_ct", "DE": "us_de", "FL": "us_fl", "GA": "us_ga",
    "HI": "us_hi", "ID": "us_id", "IL": "us_il", "IN": "us_in", "IA": "us_ia",
    "KS": "us_ks", "KY": "us_ky", "LA": "us_la", "ME": "us_me", "MD": "us_md",
    "MA": "us_ma", "MI": "us_mi", "MN": "us_mn", "MS": "us_ms", "MO": "us_mo",
    "MT": "us_mt", "NE": "us_ne", "NV": "us_nv", "NH": "us_nh", "NJ": "us_nj",
    "NM": "us_nm", "NY": "us_ny", "NC": "us_nc", "ND": "us_nd", "OH": "us_oh",
    "OK": "us_ok", "OR": "us_or", "PA": "us_pa", "RI": "us_ri", "SC": "us_sc",
    "SD": "us_sd", "TN": "us_tn", "TX": "us_tx", "UT": "us_ut", "VT": "us_vt",
    "VA": "us_va", "WA": "us_wa", "WV": "us_wv", "WI": "us_wi", "WY": "us_wy",
}


@dataclass
class LLCInfo:
    name: str
    state: str
    registered_agent: Optional[str] = None
    agent_address: Optional[str] = None
    officers: list = None
    opencorporates_url: Optional[str] = None


async def lookup_company(
    company_name: str,
    state: str,
    api_key: str = "",
) -> LLCInfo:
    """
    Search OpenCorporates for the LLC and return registered agent + officers.
    Caches nothing here — caller should cache in Supabase.
    """
    jurisdiction = STATE_JURISDICTION.get(state.upper(), f"us_{state.lower()}")
    params: dict = {
        "q": company_name,
        "jurisdiction_code": jurisdiction,
        "fields": "registered_agent_name,registered_agent_address,officers",
    }
    if api_key:
        params["api_token"] = api_key

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(f"{BASE}/companies/search", params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("OpenCorporates lookup failed for %r (%s): %s", company_name, state, exc)
            return LLCInfo(name=company_name, state=state)

    companies = data.get("results", {}).get("companies", [])
    if not companies:
        return LLCInfo(name=company_name, state=state)

    company = companies[0].get("company", {})
    officers = []
    for officer in company.get("officers", []):
        o = officer.get("officer", {})
        officers.append({
            "name": o.get("name"),
            "role": o.get("position"),
        })

    agent = company.get("registered_agent", {})
    agent_name = (
        agent.get("name")
        if isinstance(agent, dict)
        else company.get("registered_agent_name")
    )
    agent_addr = (
        agent.get("address")
        if isinstance(agent, dict)
        else company.get("registered_agent_address")
    )

    return LLCInfo(
        name=company.get("name", company_name),
        state=state,
        registered_agent=agent_name,
        agent_address=agent_addr,
        officers=officers,
        opencorporates_url=company.get("opencorporates_url"),
    )
