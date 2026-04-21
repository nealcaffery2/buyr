"""
Tyler Technologies / TylerHost adapter.
Covers Pima AZ, El Paso CO, Knox TN, Davidson TN, Hamilton TN.
Uses Playwright because the search is a React SPA.
"""
from playwright.async_api import async_playwright
from ..base import CountyScraper, Transaction


class TylerScraper(CountyScraper):
    requires_browser = True

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        base = self.base_url.rstrip("/")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=self._headers["User-Agent"],
                viewport={"width": 1280, "height": 800},
            )
            page = await ctx.new_page()

            try:
                await page.goto(f"{base}/web/search/DOCSEARCH55S6", timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=20000)

                # Fill name search field
                await page.fill("input[placeholder*='Last Name'], input[id*='lastName'], input[id*='name']", grantor_name)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle", timeout=20000)

                rows = await page.query_selector_all("table tbody tr, .result-row")
                for row in rows:
                    cells = await row.query_selector_all("td")
                    if len(cells) < 3:
                        continue
                    texts = [await c.inner_text() for c in cells]

                    grantor_cell = texts[0].strip()
                    grantee_cell = texts[1].strip() if len(texts) > 1 else ""
                    if not grantee_cell:
                        continue

                    price_raw = texts[4].replace("$", "").replace(",", "").strip() if len(texts) > 4 else ""
                    try:
                        price = float(price_raw) if price_raw else None
                    except ValueError:
                        price = None

                    results.append(
                        Transaction(
                            grantor_name=grantor_cell or grantor_name,
                            grantee_name=grantee_cell,
                            property_address=texts[2].strip() if len(texts) > 2 else "",
                            county=self.county,
                            state=self.state,
                            sale_date=texts[3].strip() if len(texts) > 3 else None,
                            sale_price=price,
                            deed_type="DEED",
                            source_url=page.url,
                        )
                    )

            except Exception:
                pass
            finally:
                await browser.close()

        return results
