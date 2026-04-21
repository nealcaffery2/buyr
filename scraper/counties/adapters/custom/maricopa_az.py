"""Maricopa County AZ Recorder — uses their public document search API."""
import httpx
from ...base import CountyScraper, Transaction

BASE = "https://recorder.maricopa.gov"


class MaricopaAZScraper(CountyScraper):
    requires_browser = False
    base_url = BASE

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    f"{BASE}/webrecordingSearch/search.aspx",
                    params={
                        "searchtype": "name",
                        "name": grantor_name,
                        "grantor_grantee": "grantor",
                    },
                )
                resp.raise_for_status()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "lxml")
                for row in soup.select("table#grdResults tr:not(:first-child)"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) < 4:
                        continue
                    grantee = cells[2] if len(cells) > 2 else ""
                    if not grantee:
                        continue
                    price_raw = cells[5].replace("$", "").replace(",", "") if len(cells) > 5 else ""
                    try:
                        price = float(price_raw) if price_raw else None
                    except ValueError:
                        price = None
                    results.append(Transaction(
                        grantor_name=cells[1] or grantor_name,
                        grantee_name=grantee,
                        property_address=cells[3] if len(cells) > 3 else "",
                        county="maricopa",
                        state="AZ",
                        sale_date=cells[0],
                        sale_price=price,
                        deed_type=cells[4] if len(cells) > 4 else "DEED",
                        source_url=f"{BASE}/webrecordingSearch/search.aspx",
                    ))
            except Exception:
                pass
        return results
