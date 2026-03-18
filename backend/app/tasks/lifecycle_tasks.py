"""Celery task wrappers for ad data lifecycle management.

Logic lives in app.services.lifecycle — these are thin Celery wrappers.
"""
import logging

from asgiref.sync import async_to_sync

from app.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(name="lifecycle.mark_expired_ads", time_limit=120, soft_time_limit=90)
def mark_expired_ads():
    from app.core.database import async_session
    from app.services.lifecycle import mark_expired_ads as _mark

    async def _run():
        async with async_session() as db:
            return await _mark(db)

    return async_to_sync(_run)()


@celery.task(name="lifecycle.update_hot_ads", time_limit=300, soft_time_limit=240)
def update_hot_ads():
    from app.core.database import async_session
    from app.services.lifecycle import update_hot_ads as _update

    async def _run():
        async with async_session() as db:
            return await _update(db)

    return async_to_sync(_run)()


@celery.task(name="lifecycle.archive_stale_ads", time_limit=120, soft_time_limit=90)
def archive_stale_ads():
    from app.config import settings
    from app.core.database import async_session
    from app.search.es_client import es_client
    from app.services.lifecycle import archive_stale_ads as _archive

    async def _run():
        async with async_session() as db:
            try:
                es = es_client.client
            except RuntimeError:
                es = None
            return await _archive(db, es, settings.es_ads_index)

    return async_to_sync(_run)()


@celery.task(name="lifecycle.dedupe_ads", time_limit=300, soft_time_limit=240)
def dedupe_ads():
    from app.core.database import async_session
    from app.services.lifecycle import dedupe_ads as _dedupe

    async def _run():
        async with async_session() as db:
            return await _dedupe(db)

    return async_to_sync(_run)()


@celery.task(name="lifecycle.cleanup_incomplete", time_limit=120, soft_time_limit=90)
def cleanup_incomplete():
    from app.core.database import async_session
    from app.services.lifecycle import cleanup_incomplete as _cleanup

    async def _run():
        async with async_session() as db:
            return await _cleanup(db)

    return async_to_sync(_run)()


@celery.task(name="lifecycle.purge_old_ads", time_limit=120, soft_time_limit=90)
def purge_old_ads():
    from app.core.database import async_session
    from app.services.lifecycle import purge_old_ads as _purge

    async def _run():
        async with async_session() as db:
            return await _purge(db)

    return async_to_sync(_run)()
