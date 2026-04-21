"""Wake County NC Register of Deeds."""
import httpx
from bs4 import BeautifulSoup
from ...base import CountyScraper, Transaction

BASE = "https://services.wakegov.com/booksweb"


class WakeNCScraper(CountyScraper):
    requires_browser = False
    base_url = BASE

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.post(
                    f"{BASE}/NameSearch.asp",
                    data={
                        "SearchName": grantor_name,
                        "SearchType": "G",  # G = Grantor
                        "DOCTYPE": "DEED",
                        "Submit": "Search",
                    },
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                for row in soup.select("table tr:not(:first-child)"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) < 3:
                        continue
                    grantee = cells[1] if len(cells) > 1 else ""
                    if not grantee:
                        continue
                    results.append(Transaction(
                        grantor_name=cells[0] or grantor_name,
                        grantee_name=grantee,
                        property_address="",
                        county="wake",
                        state="NC",
                        sale_date=cells[2] if len(cells) > 2 else None,
                        sale_price=None,
                        deed_type="DEED",
                        source_url=f"{BASE}/NameSearch.asp",
                    ))
            except Exception:
                pass
        return results
