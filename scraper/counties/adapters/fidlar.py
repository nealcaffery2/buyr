"""
Fidlar Technologies adapter — Marion IN.
Attempts JSON API first; falls back to Playwright on 403/failure.
"""
import logging
import httpx
from playwright.async_api import async_playwright
from ..base import CountyScraper, Transaction

logger = logging.getLogger(__name__)


class FidlarScraper(CountyScraper):
    requires_browser = False

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        base = self.base_url.rstrip("/")
        results = await self._try_api(base, grantor_name)
        if results is None:
            logger.warning("Fidlar API failed for %s — falling back to Playwright", grantor_name)
            results = await self._try_browser(base, grantor_name)
        return results

    async def _try_api(self, base: str, grantor_name: str) -> list[Transaction] | None:
        async with httpx.AsyncClient(headers=self._headers, timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    f"{base}/INMarion/DirectSearch/api/search",
                    params={
                        "searchType": "name",
                        "grantorName": grantor_name,
                        "docType": "DEED",
                        "pageSize": 100,
                        "pageIndex": 0,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as exc:
                logger.warning("Fidlar API HTTP %s for %s", exc.response.status_code, grantor_name)
                return None
            except Exception as exc:
                logger.warning("Fidlar API error for %s: %s", grantor_name, exc)
                return None

        results: list[Transaction] = []
        for doc in data.get("results", []):
            parties = doc.get("parties", [])
            grantee = next(
                (p.get("name") for p in parties if "GRANTEE" in p.get("type", "").upper()),
                "",
            )
            if not grantee:
                continue
            price_raw = doc.get("documentAmount", "")
            try:
                price = float(str(price_raw).replace("$", "").replace(",", "")) if price_raw else None
            except ValueError:
                price = None
            results.append(Transaction(
                grantor_name=grantor_name,
                grantee_name=grantee,
                property_address=doc.get("address", ""),
                county=self.county,
                state=self.state,
                sale_date=doc.get("recordedDate") or doc.get("fileDate"),
                sale_price=price,
                deed_type=doc.get("documentType", "DEED"),
                source_url=f"{base}/INMarion/DirectSearch/#/search",
            ))
        return results

    async def _try_browser(self, base: str, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(f"{base}/INMarion/DirectSearch/#/search", timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=20000)
                name_input = await page.query_selector("input[placeholder*='Grantor'], input[id*='grantor']")
                if name_input:
                    await name_input.fill(grantor_name)
                    await page.keyboard.press("Enter")
                    await page.wait_for_load_state("networkidle", timeout=20000)
                rows = await page.query_selector_all("table tbody tr")
                for row in rows:
                    cells = await row.query_selector_all("td")
                    texts = [await c.inner_text() for c in cells]
                    if len(texts) < 3:
                        continue
                    grantee = texts[1].strip() if len(texts) > 1 else ""
                    if not grantee:
                        continue
                    results.append(Transaction(
                        grantor_name=grantor_name,
                        grantee_name=grantee,
                        property_address=texts[2].strip() if len(texts) > 2 else "",
                        county=self.county,
                        state=self.state,
                        sale_date=texts[3].strip() if len(texts) > 3 else None,
                        sale_price=None,
                        deed_type="DEED",
                        source_url=page.url,
                    ))
            except Exception as exc:
                logger.error("Fidlar Playwright fallback failed for %s: %s", grantor_name, exc)
            finally:
                await browser.close()
        return results
