"""Initialize Elasticsearch indices with Vietnamese analyzer."""
import asyncio

from app.search.es_client import es_client
from app.search.indexing import create_ads_index


async def main():
    await es_client.initialize()
    await create_ads_index(es_client.client)
    await es_client.close()
    print("Elasticsearch initialization complete.")


if __name__ == "__main__":
    asyncio.run(main())
