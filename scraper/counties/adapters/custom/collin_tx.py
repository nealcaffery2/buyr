"""
Collin/Kaufman/Rockwall/Grayson TX — esearch CAD platform.
These counties share the same search platform structure.
"""
import httpx
from bs4 import BeautifulSoup
from ...base import CountyScraper, Transaction

CAD_URLS = {
    "collin": "https://esearch.collincad.org",
    "kaufman": "https://esearch.kaufman-cad.org",
    "rockwall": "https://www.rockwallcad.com",
    "grayson": "https://esearch.graysonappraisal.org",
}


class CollinTXScraper(CountyScraper):
    requires_browser = False

    @property
    def _cad_base(self) -> str:
        return CAD_URLS.get(self.county.lower(), CAD_URLS["collin"])

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        base = self._cad_base
        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    f"{base}/api/search",
                    params={"type": "owner", "q": grantor_name, "limit": 100},
                )
                if not resp.is_success:
                    # Try HTML form fallback
                    resp = await client.get(base + "/", params={"search": grantor_name})
                resp.raise_for_status()

                if "application/json" in resp.headers.get("content-type", ""):
                    data = resp.json()
                    for prop in data.get("data", data.get("results", [])):
                        owner = prop.get("ownerName", "")
                        if not owner or owner.upper() == grantor_name.upper():
                            continue
                        results.append(Transaction(
                            grantor_name=grantor_name,
                            grantee_name=owner,
                            property_address=prop.get("siteAddress", ""),
                            county=self.county,
                            state="TX",
                            sale_date=prop.get("lastSaleDate"),
                            sale_price=prop.get("lastSalePrice"),
                            deed_type="DEED",
                            source_url=base,
                        ))
                else:
                    soup = BeautifulSoup(resp.text, "lxml")
                    for row in soup.select("table tbody tr"):
                        cells = [td.get_text(strip=True) for td in row.find_all("td")]
                        if len(cells) < 2:
                            continue
                        grantee = cells[1]
                        if grantee and grantee.upper() != grantor_name.upper():
                            results.append(Transaction(
                                grantor_name=grantor_name,
                                grantee_name=grantee,
                                property_address=cells[2] if len(cells) > 2 else "",
                                county=self.county,
                                state="TX",
                                sale_date=None,
                                sale_price=None,
                                deed_type="DEED",
                                source_url=base,
                            ))
            except Exception:
                pass
        return results
