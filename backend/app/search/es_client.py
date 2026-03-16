from elasticsearch import AsyncElasticsearch

from app.config import settings


class ESClient:
    def __init__(self):
        self._client = None

    async def initialize(self):
        self._client = AsyncElasticsearch(
            hosts=[settings.elasticsearch_url],
            request_timeout=30,
        )

    @property
    def client(self) -> AsyncElasticsearch:
        if self._client is None:
            raise RuntimeError("Elasticsearch not initialized. Call initialize() first.")
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()


es_client = ESClient()


async def get_es() -> AsyncElasticsearch:
    return es_client.client
