"""Run async tasks from CLI. Usage: python -m scripts.run_task <task_name>"""
import asyncio
import sys

from app.core.database import async_session


async def run_task(task_name: str):
    async with async_session() as db:
        if task_name == "crawl-pages":
            from app.enrichment.landing_page import crawl_landing_pages
            result = await crawl_landing_pages(db)
        elif task_name == "download-creatives":
            from app.enrichment.creative_downloader import download_creatives
            result = await download_creatives(db)
        elif task_name == "match-advertisers":
            from app.enrichment.advertiser_matching import match_advertisers
            result = await match_advertisers(db)
        else:
            print(f"Unknown task: {task_name}")
            sys.exit(1)

    print(f"Done: {result}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.run_task <task_name>")
        print("Tasks: crawl-pages, download-creatives, match-advertisers")
        sys.exit(1)
    asyncio.run(run_task(sys.argv[1]))
