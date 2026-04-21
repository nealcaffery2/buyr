"""
KoFile/CountyFusion adapter — Denver CO.
Requires Playwright to accept disclaimer and interact with search.
"""
from playwright.async_api import async_playwright
from ..base import CountyScraper, Transaction


class KofileScraper(CountyScraper):
    requires_browser = True

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        base = "https://countyfusion3.kofiletech.us/countyweb"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(user_agent=self._headers["User-Agent"])
            page = await ctx.new_page()

            try:
                await page.goto(f"{base}/disclaimer.do", timeout=30000)
                # Accept disclaimer if present
                accept_btn = await page.query_selector("input[value='Accept'], button:has-text('Accept')")
                if accept_btn:
                    await accept_btn.click()
                    await page.wait_for_load_state("networkidle", timeout=15000)

                # Fill grantor name
                await page.fill("input[name='grantorName'], input[name='lastName']", grantor_name)
                await page.click("input[type='submit'], button[type='submit']")
                await page.wait_for_load_state("networkidle", timeout=20000)

                rows = await page.query_selector_all("table.resultsTable tr:not(:first-child), table tbody tr")
                for row in rows:
                    cells = await row.query_selector_all("td")
                    if len(cells) < 3:
                        continue
                    texts = [await c.inner_text() for c in cells]
                    grantee = texts[1].strip() if len(texts) > 1 else ""
                    if not grantee:
                        continue

                    price_raw = texts[3].replace("$", "").replace(",", "").strip() if len(texts) > 3 else ""
                    try:
                        price = float(price_raw) if price_raw else None
                    except ValueError:
                        price = None

                    results.append(
                        Transaction(
                            grantor_name=texts[0].strip() or grantor_name,
                            grantee_name=grantee,
                            property_address=texts[2].strip() if len(texts) > 2 else "",
                            county=self.county,
                            state=self.state,
                            sale_date=texts[4].strip() if len(texts) > 4 else None,
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
