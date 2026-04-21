"""Orange County FL — ocpaweb.ocpafl.org"""
import httpx
from bs4 import BeautifulSoup
from ...base import CountyScraper, Transaction

BASE = "https://ocpaweb.ocpafl.org"


class OrangeFLScraper(CountyScraper):
    requires_browser = False
    base_url = BASE

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    f"{BASE}/advancedsearch",
                    params={"ownerName": grantor_name, "searchType": "owner"},
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                for row in soup.select("table tbody tr"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) < 2:
                        continue
                    owner = cells[0]
                    addr = cells[1] if len(cells) > 1 else ""
                    if not owner or owner.upper() == grantor_name.upper():
                        continue
                    results.append(Transaction(
                        grantor_name=grantor_name,
                        grantee_name=owner,
                        property_address=addr,
                        county="orange",
                        state="FL",
                        sale_date=cells[3] if len(cells) > 3 else None,
                        sale_price=None,
                        deed_type="DEED",
                        source_url=f"{BASE}/advancedsearch",
                    ))
            except Exception:
                pass
        return results
