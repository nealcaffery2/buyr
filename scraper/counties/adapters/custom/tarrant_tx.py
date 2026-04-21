"""Tarrant County TX — taxonline.tarrantcounty.com"""
import logging
import httpx
from bs4 import BeautifulSoup
from ...base import CountyScraper, Transaction

BASE = "https://taxonline.tarrantcounty.com"
logger = logging.getLogger(__name__)


class TarrantTXScraper(CountyScraper):
    requires_browser = False
    base_url = BASE

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    f"{BASE}/TaxPayer/search",
                    params={"searchText": grantor_name, "searchType": "name"},
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                for row in soup.select("table tbody tr"):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cells) < 3:
                        continue
                    grantee = cells[1] if len(cells) > 1 else ""
                    if not grantee or grantee.upper() == grantor_name.upper():
                        continue
                    results.append(Transaction(
                        grantor_name=grantor_name,
                        grantee_name=grantee,
                        property_address=cells[2] if len(cells) > 2 else "",
                        county="tarrant",
                        state="TX",
                        sale_date=cells[4] if len(cells) > 4 else None,
                        sale_price=None,
                        deed_type="DEED",
                        source_url=f"{BASE}/TaxPayer/search",
                    ))
            except Exception as exc:
                logger.error("TarrantTX scraper failed for %r: %s", grantor_name, exc)
        return results
