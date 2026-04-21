"""Franklin/Hamilton/Montgomery County OH Recorder — Ohio county recorder platform."""
import httpx
from bs4 import BeautifulSoup
from ...base import CountyScraper, Transaction

COUNTY_URLS = {
    "franklin": "https://recorder.franklincountyohio.gov",
    "hamilton": "https://www.hamiltoncountyrecorder.org",
    "montgomery": "https://recorder.mcohio.org",
}


class FranklinOHScraper(CountyScraper):
    requires_browser = False

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        base = COUNTY_URLS.get(self.county.lower(), COUNTY_URLS["franklin"])
        results: list[Transaction] = []
        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    f"{base}/search",
                    params={"grantor": grantor_name, "docType": "DEED"},
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                for row in soup.select("table tbody tr"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) < 3:
                        continue
                    grantee = cells[1] if len(cells) > 1 else ""
                    if not grantee:
                        continue
                    price_raw = cells[4].replace("$", "").replace(",", "") if len(cells) > 4 else ""
                    try:
                        price = float(price_raw) if price_raw else None
                    except ValueError:
                        price = None
                    results.append(Transaction(
                        grantor_name=cells[0] or grantor_name,
                        grantee_name=grantee,
                        property_address=cells[2] if len(cells) > 2 else "",
                        county=self.county,
                        state="OH",
                        sale_date=cells[3] if len(cells) > 3 else None,
                        sale_price=price,
                        deed_type="DEED",
                        source_url=f"{base}/search",
                    ))
            except Exception:
                pass
        return results
