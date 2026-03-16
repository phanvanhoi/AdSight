"""Initialize Elasticsearch indices with Vietnamese analyzer.

Usage:
    python -m scripts.init_es              # Create index if not exists
    python -m scripts.init_es --recreate   # Delete and recreate index
    python scripts/init_es.py              # Same as above
"""
import argparse
import asyncio

from app.config import settings
from app.search.es_client import es_client
from app.search.indexing import ADS_INDEX_SETTINGS


async def main(recreate: bool = False):
    await es_client.initialize()
    es = es_client.client
    index = settings.es_ads_index

    exists = await es.indices.exists(index=index)

    if exists and recreate:
        await es.indices.delete(index=index)
        print(f"Deleted existing index '{index}'")
        exists = False

    if not exists:
        await es.indices.create(
            index=index,
            settings=ADS_INDEX_SETTINGS["settings"],
            mappings=ADS_INDEX_SETTINGS["mappings"],
        )
        print(f"Created index '{index}' with Vietnamese analyzer")
    else:
        print(f"Index '{index}' already exists (use --recreate to rebuild)")

    await es_client.close()
    print("Elasticsearch initialization complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Elasticsearch indices")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the index (WARNING: destroys existing data)",
    )
    args = parser.parse_args()
    asyncio.run(main(recreate=args.recreate))
