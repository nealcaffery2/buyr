"""
SpatialEst adapter — Cleveland OK and Canadian OK.
Has a JSON API endpoint for property/owner search.
"""
import httpx
from ..base import CountyScraper, Transaction


class SpatialEstScraper(CountyScraper):
    requires_browser = False

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        base = self.base_url.rstrip("/")
        results: list[Transaction] = []

        async with httpx.AsyncClient(headers=self._headers, timeout=30) as client:
            try:
                resp = await client.get(
                    f"{base}/api/search",
                    params={"type": "name", "query": grantor_name, "limit": 100},
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                return results

            for prop in data.get("results", data.get("properties", [])):
                owner = prop.get("ownerName", "")
                address = prop.get("address", prop.get("propertyAddress", ""))
                sale_date = prop.get("lastSaleDate") or prop.get("saleDate")
                sale_price_raw = prop.get("lastSalePrice") or prop.get("salePrice")

                try:
                    sale_price = float(sale_price_raw) if sale_price_raw else None
                except (ValueError, TypeError):
                    sale_price = None

                if not owner or owner.upper().strip() == grantor_name.upper().strip():
                    continue

                results.append(
                    Transaction(
                        grantor_name=grantor_name,
                        grantee_name=owner,
                        property_address=address,
                        county=self.county,
                        state=self.state,
                        sale_date=sale_date,
                        sale_price=sale_price,
                        deed_type="DEED",
                        source_url=f"{base}/",
                    )
                )

        return results
