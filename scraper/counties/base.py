from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import asyncio
import random


@dataclass
class Transaction:
    grantor_name: str
    grantee_name: str
    property_address: str
    county: str
    state: str
    sale_date: Optional[str] = None
    sale_price: Optional[float] = None
    deed_type: Optional[str] = None
    source_url: str = ""


class CountyScraper(ABC):
    county: str = ""
    state: str = ""
    base_url: str = ""
    requires_browser: bool = True

    def __init__(self, county: str, state: str):
        self.county = county
        self.state = state

    @abstractmethod
    async def search_grantor(self, grantor_name: str) -> list[Transaction]:
        pass

    async def _sleep_random(self, lo: float = 1.0, hi: float = 3.0):
        await asyncio.sleep(random.uniform(lo, hi))

    @property
    def _headers(self) -> dict:
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        ]
        return {
            "User-Agent": random.choice(agents),
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }
