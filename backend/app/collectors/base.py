import abc
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class BaseCollector(abc.ABC):
    """Abstract base for all platform data collectors."""

    def __init__(self, platform: str):
        self.platform = platform

    @abc.abstractmethod
    async def collect(self, params: dict) -> list[dict]:
        """Fetch raw ads from the platform. Returns list of raw ad dicts."""
        ...

    @abc.abstractmethod
    def normalize(self, raw_ad: dict) -> dict:
        """Convert platform-specific format to our internal Ad schema."""
        ...

    async def collect_and_normalize(self, params: dict) -> list[dict]:
        """Collect raw ads and normalize them."""
        raw_ads = await self.collect(params)
        logger.info(f"[{self.platform}] Collected {len(raw_ads)} raw ads")

        normalized = []
        for raw in raw_ads:
            try:
                ad = self.normalize(raw)
                normalized.append(ad)
            except Exception as e:
                logger.warning(f"[{self.platform}] Failed to normalize ad: {e}")
                continue

        logger.info(f"[{self.platform}] Normalized {len(normalized)} ads")
        return normalized

    async def collect_with_retry(self, params: dict, max_retries: int = 3) -> list[dict]:
        """Collect with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                return await self.collect_and_normalize(params)
            except Exception as e:
                wait = 2 ** attempt
                logger.error(
                    f"[{self.platform}] Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {wait}s..."
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"[{self.platform}] All retries exhausted")
                    raise
