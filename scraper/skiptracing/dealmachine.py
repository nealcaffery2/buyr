"""
DealMachine skip trace client — tertiary provider.
Uses DealMachine's REST API with API key auth.
"""
import httpx
from dataclasses import dataclass
from typing import Optional

BASE = "https://api.dealmachine.com/v1"


@dataclass
class DealMachineContact:
    name: str
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    source: str = "dealmachine"
    confidence: int = 70


async def skip_trace_person(
    full_name: str,
    address: str,
    api_key: str,
) -> list[DealMachineContact]:
    if not api_key:
        return []

    name_parts = full_name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{BASE}/skip-trace",
                json={
                    "firstName": first_name,
                    "lastName": last_name,
                    "propertyAddress": address,
                },
                headers={
                    "X-API-Key": api_key,
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

    results: list[DealMachineContact] = []
    for person in data.get("people", data.get("results", [])):
        phones = person.get("phones", [person.get("phone")])
        emails = person.get("emails", [person.get("email")])

        phone = next((p for p in phones if p), None)
        email = next((e for e in emails if e), None)

        if not phone and not email:
            continue

        results.append(DealMachineContact(
            name=person.get("name", full_name),
            phone=phone,
            email=email,
            address=person.get("address", address),
            confidence=person.get("matchConfidence", 70),
        ))

    return results[:3]
