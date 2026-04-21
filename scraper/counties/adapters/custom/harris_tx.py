"""
Harris County TX — Harris County District Clerk real property search.
https://www.cclerk.hctx.net/applications/websearch/RP.aspx
Uses Playwright — the site requires form interaction.
"""
from playwright.async_api import async_playwright
from ...base import CountyScraper, Transaction

URL = "https://www.cclerk.hctx.net/applications/websearch/RP.aspx"


class HarrisTXScraper(CountyScraper):
    requires_browser = True
    base_url = URL

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(URL, timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=15000)

                # Fill grantor name
                await page.fill("input[id*='grantor'], input[name*='grantor'], input[placeholder*='Grantor']", grantor_name)

                # Select deed document types
                deed_sel = await page.query_selector("select[id*='docType'], select[name*='docType']")
                if deed_sel:
                    await deed_sel.select_option(label="DEED")

                await page.click("input[type='submit'], button:has-text('Search')")
                await page.wait_for_load_state("networkidle", timeout=20000)

                rows = await page.query_selector_all("table tbody tr")
                for row in rows:
                    cells = await row.query_selector_all("td")
                    texts = [await c.inner_text() for c in cells]
                    if len(texts) < 4:
                        continue
                    grantee = texts[2].strip() if len(texts) > 2 else ""
                    if not grantee:
                        continue
                    price_raw = texts[5].replace("$", "").replace(",", "").strip() if len(texts) > 5 else ""
                    try:
                        price = float(price_raw) if price_raw else None
                    except ValueError:
                        price = None
                    results.append(Transaction(
                        grantor_name=texts[1].strip() if len(texts) > 1 else grantor_name,
                        grantee_name=grantee,
                        property_address=texts[3].strip() if len(texts) > 3 else "",
                        county="harris",
                        state="TX",
                        sale_date=texts[0].strip() if texts else None,
                        sale_price=price,
                        deed_type="DEED",
                        source_url=URL,
                    ))
            except Exception:
                pass
            finally:
                await browser.close()
        return results
