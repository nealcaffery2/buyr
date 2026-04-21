"""
GSCCCA adapter — Georgia Superior Court Clerks' Cooperative Authority.
Covers Fulton GA and Chatham GA (same platform, different county param).
Uses POST form submission; no browser needed.
"""
import httpx
from bs4 import BeautifulSoup
from ..base import CountyScraper, Transaction

BASE = "https://search.gsccca.org/RealEstate"

COUNTY_CODES = {
    "fulton": "60",
    "chatham": "26",
    "dekalb": "44",
    "gwinnett": "67",
    "cobb": "33",
    "cherokee": "21",
}


class GSCCCAScraper(CountyScraper):
    requires_browser = False

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        county_code = COUNTY_CODES.get(self.county.lower(), "")
        results: list[Transaction] = []
        page = 1

        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            # GSCCCA requires an initial GET to get session cookie
            await client.get(f"{BASE}/namesearch.asp")

            while True:
                try:
                    resp = await client.post(
                        f"{BASE}/namesearch.asp",
                        data={
                            "NameToSearch": grantor_name,
                            "NameType": "Grantor",
                            "County": county_code,
                            "RecordType": "Deed",
                            "SearchType": "Name",
                            "txtPage": str(page),
                            "cmdSearch": "Search",
                        },
                    )
                    resp.raise_for_status()
                except Exception:
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                rows = soup.select("table.results tr:not(:first-child)")
                if not rows:
                    break

                for row in rows:
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) < 5:
                        continue
                    grantor_cell = cells[0]
                    grantee_cell = cells[1]
                    if not grantee_cell:
                        continue

                    price_raw = cells[4].replace("$", "").replace(",", "").strip()
                    try:
                        price = float(price_raw) if price_raw and price_raw != "0" else None
                    except ValueError:
                        price = None

                    results.append(
                        Transaction(
                            grantor_name=grantor_cell or grantor_name,
                            grantee_name=grantee_cell,
                            property_address=cells[2] if len(cells) > 2 else "",
                            county=self.county,
                            state=self.state,
                            sale_date=cells[3] if len(cells) > 3 else None,
                            sale_price=price,
                            deed_type="DEED",
                            source_url=f"{BASE}/namesearch.asp",
                        )
                    )

                # Check if there's a next page
                next_btn = soup.find("input", {"name": "cmdNext"})
                if not next_btn:
                    break
                page += 1
                await self._sleep_random(1.0, 2.0)

        return results
