"""Hillsborough County FL Official Records."""
import logging
from playwright.async_api import async_playwright
from ...base import CountyScraper, Transaction

BASE = "https://pubrec.hillsclerk.com/oncore"
logger = logging.getLogger(__name__)


class HillsboroughFLScraper(CountyScraper):
    requires_browser = True
    base_url = BASE

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(f"{BASE}/search/SearchTypeName", timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=15000)
                await page.fill("input[name*='name'], input[placeholder*='Name']", grantor_name)
                await page.click("button:has-text('Search'), input[type='submit']")
                await page.wait_for_load_state("networkidle", timeout=20000)
                rows = await page.query_selector_all("table tbody tr")
                for row in rows:
                    cells = await row.query_selector_all("td")
                    texts = [await c.inner_text() for c in cells]
                    if len(texts) < 3:
                        continue
                    grantee = texts[2].strip() if len(texts) > 2 else ""
                    if not grantee:
                        continue
                    results.append(Transaction(
                        grantor_name=texts[1].strip() if len(texts) > 1 else grantor_name,
                        grantee_name=grantee,
                        property_address=texts[4].strip() if len(texts) > 4 else "",
                        county="hillsborough",
                        state="FL",
                        sale_date=texts[0].strip(),
                        sale_price=None,
                        deed_type=texts[3].strip() if len(texts) > 3 else "DEED",
                        source_url=page.url,
                    ))
            except Exception as exc:
                logger.error("HillsboroughFL scraper failed for %r: %s", grantor_name, exc)
            finally:
                await browser.close()
        return results
