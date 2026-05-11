"""Oklahoma County OK Assessor — docs.oklahomacounty.org"""
import httpx
from bs4 import BeautifulSoup
from ...base import CountyScraper, Transaction

BASE = "https://docs.oklahomacounty.org/AssessorWP5"


class OklahomaOKScraper(CountyScraper):
    requires_browser = False
    base_url = BASE

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    f"{BASE}/DefaultSearch.asp",
                    params={"OwnerName": grantor_name, "SearchType": "owner"},
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                for row in soup.select("table#tblResults tr:not(:first-child), table tbody tr"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) < 2:
                        continue
                    owner = cells[0]
                    if not owner or owner.upper() == grantor_name.upper():
                        continue
                    results.append(Transaction(
                        grantor_name=grantor_name,
                        grantee_name=owner,
                        property_address=cells[1] if len(cells) > 1 else "",
                        county="oklahoma",
                        state="OK",
                        sale_date=cells[3] if len(cells) > 3 else None,
                        sale_price=None,
                        deed_type="DEED",
                        source_url=f"{BASE}/DefaultSearch.asp",
                    ))
            except Exception:
                pass
        return results
