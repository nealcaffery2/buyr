"""
Parse a free-text address string into county + state.
Uses Google Maps Geocoding API if a key is provided;
falls back to heuristic state-from-text parsing.
"""
import httpx
import re

STATE_ABBRS = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE",
    "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC",
    "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR",
    "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
}

ABBR_SET = set(STATE_ABBRS.values())


async def parse_address(address: str, google_maps_key: str = "") -> tuple[str, str]:
    """
    Returns (county, state_abbr). Falls back to ("unknown", state) if county
    cannot be determined.
    """
    if google_maps_key:
        result = await _geocode_google(address, google_maps_key)
        if result:
            return result

    return _heuristic_parse(address)


async def _geocode_google(address: str, api_key: str) -> tuple[str, str] | None:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, params={"address": address, "key": api_key})
            data = resp.json()
        except Exception:
            return None

    results = data.get("results", [])
    if not results:
        return None

    county = ""
    state = ""
    for component in results[0].get("address_components", []):
        types = component.get("types", [])
        if "administrative_area_level_2" in types:
            county = component["long_name"].replace(" County", "").strip().lower()
        if "administrative_area_level_1" in types:
            state = component["short_name"].upper()

    if state:
        return (county or "unknown", state)
    return None


def _heuristic_parse(address: str) -> tuple[str, str]:
    """Extract state from last 2 tokens; county is unknown without geocoding."""
    tokens = address.upper().split()
    state = ""

    # Look for 2-letter state abbr at end (possibly followed by zip)
    for token in reversed(tokens):
        clean = re.sub(r"[^A-Z]", "", token)
        if clean in ABBR_SET:
            state = clean
            break

    if not state:
        lower = address.lower()
        for name, abbr in STATE_ABBRS.items():
            if name in lower:
                state = abbr
                break

    if not state:
        raise ValueError(f"Could not determine state from address: {address!r}")
    return ("unknown", state)
