import logging

from elasticsearch import AsyncElasticsearch

from app.config import settings

logger = logging.getLogger(__name__)


class ESClient:
    def __init__(self):
        self._client = None

    async def initialize(self):
        self._client = AsyncElasticsearch(
            hosts=[settings.elasticsearch_url],
            request_timeout=30,
        )
        # Health check on initialization
        try:
            info = await self._client.info()
            logger.info(f"Connected to Elasticsearch {info['version']['number']}")
        except Exception as e:
            logger.error(f"Elasticsearch connection failed: {e}")
            raise

    @property
    def client(self) -> AsyncElasticsearch:
        if self._client is None:
            raise RuntimeError("Elasticsearch not initialized. Call initialize() first.")
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()


es_client = ESClient()


async def get_es() -> AsyncElasticsearch | None:
    """Return ES client or None if ES is not available."""
    try:
        return es_client.client
    except RuntimeError:
        return None
