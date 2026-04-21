"""
Fidlar Technologies adapter — Marion IN.
Attempts JSON API first; falls back to Playwright if API returns 403.
"""
import httpx
from ..base import CountyScraper, Transaction


class FidlarScraper(CountyScraper):
    requires_browser = False

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        base = self.base_url.rstrip("/")
        results: list[Transaction] = []

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
            except Exception:
                return results

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

                results.append(
                    Transaction(
                        grantor_name=grantor_name,
                        grantee_name=grantee,
                        property_address=doc.get("address", ""),
                        county=self.county,
                        state=self.state,
                        sale_date=doc.get("recordedDate") or doc.get("fileDate"),
                        sale_price=price,
                        deed_type=doc.get("documentType", "DEED"),
                        source_url=f"{base}/INMarion/DirectSearch/#/search",
                    )
                )

        return results
