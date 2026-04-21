"""Travis County TX — tccsearch.org"""
import httpx
from bs4 import BeautifulSoup
from ...base import CountyScraper, Transaction

BASE = "https://www.tccsearch.org"


class TravisTXScraper(CountyScraper):
    requires_browser = False
    base_url = BASE

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.post(
                    f"{BASE}/RealEstate/SearchEntry.aspx",
                    data={
                        "ctl00$ContentPlaceHolder1$txtGrantorName": grantor_name,
                        "ctl00$ContentPlaceHolder1$btnSearch": "Search",
                    },
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                rows = soup.select("table#dgResults tr:not(:first-child)")
                for row in rows:
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) < 4:
                        continue
                    grantee = cells[1] if len(cells) > 1 else ""
                    if not grantee:
                        continue
                    price_raw = cells[5].replace("$", "").replace(",", "") if len(cells) > 5 else ""
                    try:
                        price = float(price_raw) if price_raw else None
                    except ValueError:
                        price = None
                    results.append(Transaction(
                        grantor_name=cells[0] or grantor_name,
                        grantee_name=grantee,
                        property_address=cells[3] if len(cells) > 3 else "",
                        county="travis",
                        state="TX",
                        sale_date=cells[2] if len(cells) > 2 else None,
                        sale_price=price,
                        deed_type=cells[4] if len(cells) > 4 else "DEED",
                        source_url=f"{BASE}/RealEstate/SearchEntry.aspx",
                    ))
            except Exception:
                pass
        return results
