import logging

from elasticsearch import AsyncElasticsearch

from app.config import settings

logger = logging.getLogger(__name__)


class ESClient:
    def __init__(self):
        self._client = None

    async def initialize(self):
        client = AsyncElasticsearch(
            hosts=[settings.elasticsearch_url],
            request_timeout=10,
        )
        # Health check — only set _client if ES is reachable
        try:
            info = await client.info()
            self._client = client
            logger.info(f"Connected to Elasticsearch {info['version']['number']}")
        except Exception as e:
            await client.close()
            logger.warning(f"Elasticsearch unavailable: {e}")
            self._client = None

    @property
    def client(self) -> AsyncElasticsearch | None:
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()


es_client = ESClient()


async def get_es() -> AsyncElasticsearch | None:
    """Return ES client or None if ES is not available."""
    return es_client.client
