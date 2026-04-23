"""
Acclaim (Tulsa OK) adapter.
Public search — no login required for basic name search.
"""
import httpx
from bs4 import BeautifulSoup
from ..base import CountyScraper, Transaction

BASE = "https://acclaim.tulsacounty.org/AcclaimWeb"


class AcclaimScraper(CountyScraper):
    requires_browser = False

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []

        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    f"{BASE}/Search/SearchTypeName",
                    params={
                        "searchType": "name",
                        "grantorGranteeSearchType": "Grantor",
                        "lastName": grantor_name,
                        "firstName": "",
                        "documentTypeCode": "WD,SWD,QCD",
                    },
                )
                resp.raise_for_status()
            except Exception:
                return results

            soup = BeautifulSoup(resp.text, "lxml")
            rows = soup.select("table#searchResults tbody tr, table.result tbody tr")

            for row in rows:
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cells) < 4:
                    continue
                grantee = cells[1] if len(cells) > 1 else ""
                if not grantee:
                    continue

                price_raw = cells[4].replace("$", "").replace(",", "").strip() if len(cells) > 4 else ""
                try:
                    price = float(price_raw) if price_raw else None
                except ValueError:
                    price = None

                results.append(
                    Transaction(
                        grantor_name=cells[0] or grantor_name,
                        grantee_name=grantee,
                        property_address=cells[2] if len(cells) > 2 else "",
                        county=self.county,
                        state=self.state,
                        sale_date=cells[3] if len(cells) > 3 else None,
                        sale_price=price,
                        deed_type="DEED",
                        source_url=f"{BASE}/Search/SearchTypeName",
                    )
                )

        return results
