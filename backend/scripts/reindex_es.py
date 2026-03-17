"""
Reindex Elasticsearch with updated Vietnamese analyzer settings.

Use this script when analyzer settings (synonyms, stopwords, tokenizer) change.
For search-time synonym updates only, use update_synonyms_es.py instead.

Usage: python -m scripts.reindex_es
"""
import asyncio
import sys

from app.search.es_client import es_client
from app.search.indexing import ADS_INDEX_SETTINGS
from app.config import settings


async def reindex():
    await es_client.initialize()
    es = es_client.client

    old_index = settings.es_ads_index
    new_index = f"{old_index}_v2"

    # Check if old index exists
    if not await es.indices.exists(index=old_index):
        print(f"Index '{old_index}' does not exist. Nothing to reindex.")
        await es_client.close()
        return

    # Delete new index if it exists (from a previous failed attempt)
    if await es.indices.exists(index=new_index):
        print(f"Deleting existing '{new_index}'...")
        await es.indices.delete(index=new_index)

    # Create new index with updated settings
    print(f"Creating '{new_index}' with updated analyzer settings...")
    await es.indices.create(
        index=new_index,
        settings=ADS_INDEX_SETTINGS["settings"],
        mappings=ADS_INDEX_SETTINGS["mappings"],
    )

    # Reindex data
    print(f"Reindexing '{old_index}' → '{new_index}'...")
    result = await es.reindex(
        body={
            "source": {"index": old_index},
            "dest": {"index": new_index},
        },
        wait_for_completion=True,
    )
    total = result.get("total", 0)
    print(f"Reindexed {total} documents.")

    # Delete old index and recreate with old name
    print(f"Deleting old '{old_index}'...")
    await es.indices.delete(index=old_index)

    print(f"Reindexing '{new_index}' → '{old_index}'...")
    await es.indices.create(
        index=old_index,
        settings=ADS_INDEX_SETTINGS["settings"],
        mappings=ADS_INDEX_SETTINGS["mappings"],
    )
    await es.reindex(
        body={
            "source": {"index": new_index},
            "dest": {"index": old_index},
        },
        wait_for_completion=True,
    )

    # Cleanup temp index
    await es.indices.delete(index=new_index)
    print(f"Done. '{old_index}' has been reindexed with updated settings.")

    await es_client.close()


async def update_search_synonyms():
    """
    Update search-time synonyms without reindexing.
    Only works because synonyms are in the search_analyzer (not index_analyzer).
    """
    await es_client.initialize()
    es = es_client.client

    index = settings.es_ads_index

    # Close index to update settings
    print(f"Closing index '{index}'...")
    await es.indices.close(index=index)

    # Update synonym filter
    synonym_filter = ADS_INDEX_SETTINGS["settings"]["analysis"]["filter"]["vietnamese_synonym"]
    print("Updating synonym filter...")
    await es.indices.put_settings(
        index=index,
        body={
            "analysis": {
                "filter": {
                    "vietnamese_synonym": synonym_filter,
                },
            },
        },
    )

    # Reopen index
    print(f"Opening index '{index}'...")
    await es.indices.open(index=index)
    print("Synonyms updated successfully (no reindex needed).")

    await es_client.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--synonyms-only":
        asyncio.run(update_search_synonyms())
    else:
        asyncio.run(reindex())
