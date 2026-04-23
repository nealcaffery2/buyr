"""
Landmark Web adapter — covers Jefferson AL, Lee FL, St. Louis MO,
Richland SC, Pulaski AR, Wyandotte KS, and others on the Landmark platform.
"""
import httpx
from bs4 import BeautifulSoup
from ..base import CountyScraper, Transaction


class LandmarkScraper(CountyScraper):
    requires_browser = False

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        base = self.base_url.rstrip("/")

        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            # Initial GET to capture form tokens / session
            try:
                init = await client.get(f"{base}/search/index")
                soup = BeautifulSoup(init.text, "lxml")
                token = ""
                t = soup.find("input", {"name": "__RequestVerificationToken"})
                if t:
                    token = t.get("value", "")
            except Exception:
                return results

            page = 1
            while True:
                try:
                    resp = await client.post(
                        f"{base}/search/SearchResults",
                        data={
                            "__RequestVerificationToken": token,
                            "searchType": "name",
                            "grantorGrantee": "0",  # 0 = grantor
                            "lastName": grantor_name,
                            "firstName": "",
                            "page": str(page),
                        },
                    )
                    resp.raise_for_status()
                except Exception:
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                rows = soup.select("table tbody tr")
                if not rows:
                    break

                for row in rows:
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) < 4:
                        continue
                    grantor_cell = cells[0]
                    grantee_cell = cells[1]
                    if not grantee_cell:
                        continue

                    price_raw = cells[3].replace("$", "").replace(",", "").strip() if len(cells) > 3 else ""
                    try:
                        price = float(price_raw) if price_raw else None
                    except ValueError:
                        price = None

                    results.append(
                        Transaction(
                            grantor_name=grantor_cell or grantor_name,
                            grantee_name=grantee_cell,
                            property_address=cells[2] if len(cells) > 2 else "",
                            county=self.county,
                            state=self.state,
                            sale_date=cells[4] if len(cells) > 4 else None,
                            sale_price=price,
                            deed_type="DEED",
                            source_url=f"{base}/search/index",
                        )
                    )

                next_link = soup.find("a", string=lambda s: s and "Next" in s)
                if not next_link:
                    break
                page += 1
                await self._sleep_random(1.0, 2.0)

        return results
