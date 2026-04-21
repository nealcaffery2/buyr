"""
BatchData API client.

Docs: https://docs.batchdata.com
Auth: Bearer token (Authorization header).

Endpoints used:
  POST /api/v1/property/search       — find properties by owner / last-sale filters
  POST /api/v1/property/skip-trace   — skip trace a person or LLC

Response shapes defensively parsed; BatchData has tweaked field names over time.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.batchdata.com/api/v1"
DEFAULT_TIMEOUT = 30.0


@dataclass
class Transfer:
    grantor_name: str
    grantee_name: str
    property_address: str
    county: Optional[str] = None
    state: Optional[str] = None
    sale_date: Optional[str] = None
    sale_price: Optional[float] = None
    deed_type: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class OwnerInfo:
    name: str
    state: str
    mailing_address: Optional[str] = None
    phones: list[dict] = field(default_factory=list)
    emails: list[dict] = field(default_factory=list)
    associated_people: list[dict] = field(default_factory=list)
    dnc_flagged: bool = False
    litigator_flagged: bool = False


def _dig(obj: Any, *keys: str, default: Any = None) -> Any:
    """Walk nested dicts; return default if any key is missing."""
    cur = obj
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def _first_nonempty(*values: Any) -> Any:
    for v in values:
        if v:
            return v
    return None


class BatchDataClient:
    def __init__(self, api_key: str, base_url: str = BASE_URL):
        if not api_key:
            raise ValueError("BatchData API key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, headers=self.headers) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def find_properties_sold_by(
        self,
        grantor_name: str,
        state: str,
        limit: int = 50,
    ) -> list[Transfer]:
        """
        Find recent property transfers where `grantor_name` sold in `state`.
        Uses property/search with a grantor-name filter on the last sale.
        """
        payload = {
            "searchCriteria": {
                "query": grantor_name,
                "compAddress": {"state": state.upper()},
                "quickLists": ["recent-seller"],
                "generalSearch": grantor_name,
            },
            "options": {"take": limit, "skip": 0, "useCache": True},
        }
        try:
            data = await self._post("/property/search", payload)
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "BatchData property/search %s failed for %r (%s): %s",
                exc.response.status_code, grantor_name, state, exc.response.text[:300],
            )
            return []
        except Exception as exc:
            logger.warning("BatchData property/search error for %r (%s): %s", grantor_name, state, exc)
            return []

        properties = (
            _dig(data, "results", "properties")
            or _dig(data, "data", "properties")
            or _dig(data, "properties")
            or []
        )

        transfers: list[Transfer] = []
        for prop in properties:
            address = prop.get("address", {}) or {}
            sale = prop.get("sale") or prop.get("lastSale") or prop.get("deed") or {}
            owner = prop.get("owner") or prop.get("currentOwner") or {}

            grantee = _first_nonempty(
                _dig(owner, "fullName"),
                _dig(owner, "name"),
                _dig(prop, "owner1FullName"),
                _dig(sale, "granteeName"),
                "UNKNOWN",
            )

            formatted = _first_nonempty(
                address.get("formattedAddress"),
                address.get("fullAddress"),
                ", ".join(
                    part for part in [
                        address.get("street"),
                        address.get("city"),
                        address.get("state"),
                        address.get("zip") or address.get("zipCode"),
                    ] if part
                ),
                "",
            )

            price_raw = _first_nonempty(
                sale.get("salePrice"),
                sale.get("price"),
                sale.get("amount"),
                prop.get("lastSalePrice"),
            )
            try:
                price = float(price_raw) if price_raw not in (None, "") else None
            except (TypeError, ValueError):
                price = None

            transfers.append(Transfer(
                grantor_name=grantor_name,
                grantee_name=(grantee or "").strip(),
                property_address=formatted,
                county=address.get("county"),
                state=address.get("state") or state.upper(),
                sale_date=_first_nonempty(
                    sale.get("saleDate"),
                    sale.get("recordingDate"),
                    prop.get("lastSaleDate"),
                ),
                sale_price=price,
                deed_type=_first_nonempty(
                    sale.get("documentType"),
                    sale.get("deedType"),
                ),
                source_url=_first_nonempty(prop.get("detailUrl"), prop.get("url")),
            ))

        return transfers

    async def skip_trace_entity(self, name: str, state: str) -> OwnerInfo:
        """
        Skip-trace an LLC / business / individual.
        BatchData distinguishes business vs. consumer skip trace; we try business first.
        """
        payload = {
            "requests": [
                {
                    "propertyAddress": None,
                    "person": {
                        "fullName": name,
                        "state": state.upper(),
                    },
                }
            ],
            "options": {"skipTraceType": "business"},
        }
        try:
            data = await self._post("/property/skip-trace", payload)
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "BatchData skip-trace %s failed for %r (%s): %s",
                exc.response.status_code, name, state, exc.response.text[:300],
            )
            return OwnerInfo(name=name, state=state)
        except Exception as exc:
            logger.warning("BatchData skip-trace error for %r (%s): %s", name, state, exc)
            return OwnerInfo(name=name, state=state)

        persons = (
            _dig(data, "results", "persons")
            or _dig(data, "results", "people")
            or _dig(data, "persons")
            or _dig(data, "data")
            or []
        )
        if not persons:
            return OwnerInfo(name=name, state=state)

        person = persons[0] if isinstance(persons, list) else persons

        mailing = _first_nonempty(
            _dig(person, "address", "formattedAddress"),
            _dig(person, "mailingAddress", "formattedAddress"),
            _dig(person, "address", "fullAddress"),
        )

        phones_raw = person.get("phoneNumbers") or person.get("phones") or []
        phones = [
            {
                "number": p.get("number") or p.get("phone"),
                "type": p.get("type"),
                "dnc": bool(p.get("dnc") or p.get("doNotCall")),
            }
            for p in phones_raw
            if (p.get("number") or p.get("phone"))
        ]

        emails_raw = person.get("emails") or person.get("emailAddresses") or []
        emails = [
            {"email": e.get("email") or e.get("address"), "type": e.get("type")}
            for e in emails_raw
            if (e.get("email") or e.get("address"))
        ]

        associated = []
        for a in (person.get("associatedPeople") or person.get("relatives") or []):
            associated.append({
                "name": a.get("fullName") or a.get("name"),
                "relationship": a.get("relationship") or a.get("type"),
            })

        return OwnerInfo(
            name=_first_nonempty(person.get("fullName"), person.get("name"), name),
            state=state,
            mailing_address=mailing,
            phones=phones,
            emails=emails,
            associated_people=associated,
            dnc_flagged=bool(person.get("dnc") or person.get("dncFlagged")),
            litigator_flagged=bool(person.get("litigator") or person.get("litigatorFlagged")),
        )
