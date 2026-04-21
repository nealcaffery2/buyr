"""Jefferson County KY Deed Search — search.jeffersondeeds.com"""
import logging
import httpx
from bs4 import BeautifulSoup
from ...base import CountyScraper, Transaction

BASE = "https://search.jeffersondeeds.com"
logger = logging.getLogger(__name__)


class JeffersonKYScraper(CountyScraper):
    requires_browser = False
    base_url = BASE

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    f"{BASE}/name.php",
                    params={"name": grantor_name, "type": "grantor"},
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                for row in soup.select("table tbody tr"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) < 3:
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
                        grantor_name=cells[1] if len(cells) > 1 else grantor_name,
                        grantee_name=grantee,
                        property_address=cells[3] if len(cells) > 3 else "",
                        county="jefferson",
                        state="KY",
                        sale_date=cells[4] if len(cells) > 4 else None,
                        sale_price=price,
                        deed_type=cells[0],
                        source_url=f"{BASE}/name.php",
                    ))
            except Exception as exc:
                logger.error("JeffersonKY scraper failed for %r: %s", grantor_name, exc)
        return results
