"""
PublicSearch.us adapter — covers Dallas TX and Bexar TX.
Uses the JSON REST API that backs the search UI; no browser needed.
"""
import httpx
from ..base import CountyScraper, Transaction


class PublicSearchScraper(CountyScraper):
    requires_browser = False

    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        results: list[Transaction] = []
        page = 1
        async with httpx.AsyncClient(headers=self._headers, timeout=30) as client:
            while True:
                try:
                    resp = await client.get(
                        f"{self.base_url}/api/search",
                        params={
                            "searchType": "name",
                            "q": grantor_name,
                            "docGroup": "DEED",
                            "page": page,
                            "perPage": 100,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception:
                    break

                hits = data.get("hits", data.get("results", []))
                if not hits:
                    break

                for doc in hits:
                    parties = doc.get("parties", [])
                    grantor = next(
                        (p.get("name", "") for p in parties if p.get("type", "").upper() == "GRANTOR"),
                        grantor_name,
                    )
                    grantee = next(
                        (p.get("name", "") for p in parties if p.get("type", "").upper() == "GRANTEE"),
                        "",
                    )
                    if not grantee:
                        continue

                    price = doc.get("salePrice") or doc.get("docAmount")
                    try:
                        price = float(price) if price else None
                    except (ValueError, TypeError):
                        price = None

                    results.append(
                        Transaction(
                            grantor_name=grantor,
                            grantee_name=grantee,
                            property_address=doc.get("propertyAddress", ""),
                            county=self.county,
                            state=self.state,
                            sale_date=doc.get("fileDate") or doc.get("recordedDate"),
                            sale_price=price,
                            deed_type=doc.get("docType", ""),
                            source_url=f"{self.base_url}/search/advanced",
                        )
                    )

                total = data.get("total")
                # If total is absent or we've fetched all pages, stop
                if total is None or len(hits) < 100 or page * 100 >= total:
                    break
                page += 1
                await self._sleep_random(0.5, 1.5)

        return results
