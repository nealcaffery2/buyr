"""Duval County FL — oncore.duvalclerk.com"""
import httpx
from bs4 import BeautifulSoup
from ...base import CountyScraper, Transaction

BASE = "https://oncore.duvalclerk.com"


class DuvalFLScraper(CountyScraper):
    requires_browser = False
    base_url = BASE

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    f"{BASE}/search/SearchTypeName",
                    params={"searchType": "name", "name": grantor_name, "grantorGrantee": "grantor"},
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                for row in soup.select("table.results tbody tr, table tbody tr"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) < 3:
                        continue
                    grantee = cells[2] if len(cells) > 2 else ""
                    if not grantee:
                        continue
                    results.append(Transaction(
                        grantor_name=cells[1] if len(cells) > 1 else grantor_name,
                        grantee_name=grantee,
                        property_address=cells[4] if len(cells) > 4 else "",
                        county="duval",
                        state="FL",
                        sale_date=cells[0],
                        sale_price=None,
                        deed_type=cells[3] if len(cells) > 3 else "DEED",
                        source_url=f"{BASE}/search/SearchTypeName",
                    ))
            except Exception:
                pass
        return results
