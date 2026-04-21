"""
BatchData skip trace client — primary skip trace provider.
Docs: https://batchdata.com/docs/api
Endpoint: POST /api/v1/property/skip-trace
"""
import httpx
from dataclasses import dataclass
from typing import Optional

BASE = "https://api.batchdata.com/api/v1"


@dataclass
class SkipTraceResult:
    name: str
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    source: str = "batchdata"
    confidence: int = 85


async def skip_trace_name(
    full_name: str,
    address: str,
    api_key: str,
) -> list[SkipTraceResult]:
    """
    Skip trace a person by name + last known address.
    Returns up to 3 contacts ranked by confidence.
    """
    if not api_key:
        return []

    name_parts = full_name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    payload = {
        "requests": [
            {
                "firstName": first_name,
                "lastName": last_name,
                "address": address,
            }
        ]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{BASE}/property/skip-trace",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

    results: list[SkipTraceResult] = []
    for person in data.get("results", [{}])[0].get("persons", []):
        phones = person.get("phones", [])
        emails = person.get("emails", [])
        addr = person.get("addresses", [{}])
        addr_str = (
            f"{addr[0].get('address1', '')} {addr[0].get('city', '')} {addr[0].get('state', '')}"
            if addr
            else address
        )

        for phone_obj in phones[:2]:
            phone = phone_obj.get("phone") or phone_obj.get("number")
            if not phone:
                continue
            email = emails[0].get("email") if emails else None
            results.append(SkipTraceResult(
                name=full_name,
                phone=phone,
                email=email,
                address=addr_str,
                confidence=phone_obj.get("confidence", 80),
            ))

        if not phones and emails:
            for email_obj in emails[:2]:
                results.append(SkipTraceResult(
                    name=full_name,
                    phone=None,
                    email=email_obj.get("email"),
                    address=addr_str,
                    confidence=email_obj.get("confidence", 70),
                ))

    return results[:3]


async def skip_trace_llc(
    llc_name: str,
    state: str,
    api_key: str,
) -> list[SkipTraceResult]:
    """
    Skip trace an LLC by name to find associated persons.
    Uses BatchData's business/entity endpoint if available.
    """
    if not api_key:
        return []

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{BASE}/business/skip-trace",
                json={"businessName": llc_name, "state": state},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

    results: list[SkipTraceResult] = []
    for person in data.get("contacts", data.get("persons", [])):
        phone = person.get("phone") or person.get("phoneNumber")
        email = person.get("email") or person.get("emailAddress")
        name = person.get("name") or person.get("fullName", llc_name)
        results.append(SkipTraceResult(
            name=name,
            phone=phone,
            email=email,
            address=person.get("address", ""),
            confidence=person.get("confidence", 75),
        ))

    return results[:3]
