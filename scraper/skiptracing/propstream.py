"""
PropStream skip trace client — secondary provider.
PropStream uses a session-based API. We authenticate once, cache the token,
then call the skip trace endpoint per person.
"""
import httpx
from dataclasses import dataclass
from typing import Optional

BASE = "https://api.propstream.com"
AUTH_URL = f"{BASE}/auth/login"
SKIP_URL = f"{BASE}/skiptracing/search"


@dataclass
class PropStreamContact:
    name: str
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    source: str = "propstream"
    confidence: int = 75


_token_cache: dict[str, str] = {}


async def _get_token(email: str, password: str) -> str:
    cache_key = f"{email}:{password}"
    if cache_key in _token_cache:
        return _token_cache[cache_key]

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(AUTH_URL, json={"username": email, "password": password})
        resp.raise_for_status()
        data = resp.json()
        token = data.get("token") or data.get("access_token") or data.get("jwt", "")
        _token_cache[cache_key] = token
        return token


async def skip_trace_person(
    full_name: str,
    address: str,
    email: str,
    password: str,
) -> list[PropStreamContact]:
    if not email or not password:
        return []

    try:
        token = await _get_token(email, password)
    except Exception:
        return []

    name_parts = full_name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                SKIP_URL,
                json={
                    "firstName": first_name,
                    "lastName": last_name,
                    "address": address,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

    results: list[PropStreamContact] = []
    contacts = data.get("contacts", data.get("results", []))
    for c in contacts[:3]:
        phone = c.get("phone") or c.get("phoneNumber") or c.get("mobilePhone")
        email_addr = c.get("email") or c.get("emailAddress")
        results.append(PropStreamContact(
            name=c.get("name", full_name),
            phone=phone,
            email=email_addr,
            address=c.get("address", address),
            confidence=c.get("confidence", 75),
        ))

    return results
