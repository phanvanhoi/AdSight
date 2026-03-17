"""Tests for ad data lifecycle management."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

from app.models.ad import Ad
from app.models.board import Board
from app.models.board_ad import BoardAd
from app.models.user import User
from app.core.security import hash_password

from tests.conftest import TestSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_ad(db: AsyncSession, **overrides) -> Ad:
    defaults = {
        "platform": "meta",
        "platform_ad_id": f"ad_{uuid.uuid4().hex[:8]}",
        "advertiser_name": "Test",
        "ad_type": "image",
        "headline": "Test ad",
        "body_text": "Body text",
        "is_active": True,
        "likes": 100,
        "comments": 10,
        "shares": 5,
        "last_seen": datetime.now(timezone.utc),
        "first_seen": datetime.now(timezone.utc) - timedelta(days=30),
    }
    defaults.update(overrides)
    ad = Ad(**defaults)
    db.add(ad)
    return ad


# ---------------------------------------------------------------------------
# 1. Mark expired ads
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestMarkExpiredAds:
    async def test_marks_old_ads_inactive(self, db: AsyncSession):
        from app.services.lifecycle import mark_expired_ads

        _make_ad(db, platform_ad_id="old_1",
                 last_seen=datetime.now(timezone.utc) - timedelta(days=10))
        _make_ad(db, platform_ad_id="recent_1",
                 last_seen=datetime.now(timezone.utc) - timedelta(days=2))
        await db.commit()

        result = await mark_expired_ads(db, expire_days=7)
        assert result["expired"] == 1

        old = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "old_1")
        )).scalar_one()
        assert old.is_active is False

        recent = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "recent_1")
        )).scalar_one()
        assert recent.is_active is True

    async def test_no_expired_ads(self, db: AsyncSession):
        from app.services.lifecycle import mark_expired_ads

        _make_ad(db, last_seen=datetime.now(timezone.utc))
        await db.commit()

        result = await mark_expired_ads(db)
        assert result["expired"] == 0


# ---------------------------------------------------------------------------
# 2. Update hot ads
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestUpdateHotAds:
    async def test_high_engagement_becomes_hot(self, db: AsyncSession):
        from app.services.lifecycle import update_hot_ads

        _make_ad(db, platform_ad_id="viral_1",
                 likes=5000, comments=200, shares=100,
                 last_seen=datetime.now(timezone.utc))
        await db.commit()

        result = await update_hot_ads(db, hot_threshold=50.0)
        assert result["updated"] >= 1

        ad = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "viral_1")
        )).scalar_one()
        assert ad.is_hot is True
        assert ad.viral_score is not None
        assert ad.viral_score >= 50.0

    async def test_low_engagement_not_hot(self, db: AsyncSession):
        from app.services.lifecycle import update_hot_ads

        _make_ad(db, platform_ad_id="boring_1",
                 likes=5, comments=0, shares=0,
                 last_seen=datetime.now(timezone.utc))
        await db.commit()

        await update_hot_ads(db, hot_threshold=50.0)

        ad = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "boring_1")
        )).scalar_one()
        assert ad.is_hot is False

    async def test_recency_decay(self, db: AsyncSession):
        from app.services.lifecycle import update_hot_ads

        _make_ad(db, platform_ad_id="recent_ad",
                 likes=3000, comments=100, shares=50,
                 last_seen=datetime.now(timezone.utc))
        _make_ad(db, platform_ad_id="old_ad",
                 likes=3000, comments=100, shares=50,
                 last_seen=datetime.now(timezone.utc) - timedelta(days=15))
        await db.commit()

        await update_hot_ads(db)

        recent = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "recent_ad")
        )).scalar_one()
        old = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "old_ad")
        )).scalar_one()
        assert recent.viral_score > old.viral_score


# ---------------------------------------------------------------------------
# 3. Archive stale ads (ES removal)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestArchiveStaleAds:
    async def test_removes_inactive_old_from_es(self, db: AsyncSession):
        from app.services.lifecycle import archive_stale_ads

        _make_ad(db, platform_ad_id="stale_1", is_active=False,
                 last_seen=datetime.now(timezone.utc) - timedelta(days=60))
        _make_ad(db, platform_ad_id="active_1", is_active=True,
                 last_seen=datetime.now(timezone.utc) - timedelta(days=60))
        await db.commit()

        mock_es = AsyncMock()
        mock_es.bulk = AsyncMock()

        result = await archive_stale_ads(db, mock_es, "ads", stale_days=30)

        assert result["archived"] == 1
        mock_es.bulk.assert_called_once()

    async def test_no_stale_ads(self, db: AsyncSession):
        from app.services.lifecycle import archive_stale_ads

        _make_ad(db, is_active=True, last_seen=datetime.now(timezone.utc))
        await db.commit()

        mock_es = AsyncMock()
        result = await archive_stale_ads(db, mock_es, "ads", stale_days=30)
        assert result["archived"] == 0


# ---------------------------------------------------------------------------
# 4. Dedupe ads
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestDedupeAds:
    async def test_dedupes_same_phash(self, db: AsyncSession):
        from app.services.lifecycle import dedupe_ads

        phash = "abc123def456"
        _make_ad(db, platform_ad_id="dupe_old", creative_phash=phash, likes=100,
                 first_seen=datetime.now(timezone.utc) - timedelta(days=30),
                 last_seen=datetime.now(timezone.utc) - timedelta(days=10))
        _make_ad(db, platform_ad_id="dupe_new", creative_phash=phash, likes=200,
                 first_seen=datetime.now(timezone.utc) - timedelta(days=5),
                 last_seen=datetime.now(timezone.utc))
        await db.commit()

        result = await dedupe_ads(db)
        assert result["merged"] == 1

        keeper = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "dupe_new")
        )).scalar_one()
        assert keeper.is_active is True
        assert keeper.likes == 200

        dupe = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "dupe_old")
        )).scalar_one()
        assert dupe.is_active is False

    async def test_different_phash_not_deduped(self, db: AsyncSession):
        from app.services.lifecycle import dedupe_ads

        _make_ad(db, platform_ad_id="unique_1", creative_phash="aaa")
        _make_ad(db, platform_ad_id="unique_2", creative_phash="bbb")
        await db.commit()

        result = await dedupe_ads(db)
        assert result["merged"] == 0

    async def test_cross_platform_not_deduped(self, db: AsyncSession):
        from app.services.lifecycle import dedupe_ads

        phash = "same_hash_123"
        _make_ad(db, platform="meta", platform_ad_id="meta_1", creative_phash=phash)
        _make_ad(db, platform="tiktok", platform_ad_id="tiktok_1", creative_phash=phash)
        await db.commit()

        result = await dedupe_ads(db)
        assert result["merged"] == 0


# ---------------------------------------------------------------------------
# 5. Cleanup incomplete ads
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestCleanupIncomplete:
    async def test_marks_incomplete_inactive(self, db: AsyncSession):
        from app.services.lifecycle import cleanup_incomplete

        _make_ad(db, platform_ad_id="incomplete_1",
                 headline=None, body_text=None, media_urls=None)
        _make_ad(db, platform_ad_id="complete_1",
                 headline="Has headline", body_text=None, media_urls=None)
        await db.commit()

        result = await cleanup_incomplete(db)
        assert result["cleaned"] == 1

        incomplete = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "incomplete_1")
        )).scalar_one()
        assert incomplete.is_active is False

        complete = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "complete_1")
        )).scalar_one()
        assert complete.is_active is True


# ---------------------------------------------------------------------------
# 6. Purge old ads
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestPurgeOldAds:
    async def test_purges_inactive_old_not_saved(self, db: AsyncSession):
        from app.services.lifecycle import purge_old_ads

        _make_ad(db, platform_ad_id="to_purge", is_active=False,
                 last_seen=datetime.now(timezone.utc) - timedelta(days=60))
        _make_ad(db, platform_ad_id="keep_active", is_active=True,
                 last_seen=datetime.now(timezone.utc) - timedelta(days=60))
        await db.commit()

        result = await purge_old_ads(db, purge_days=30)
        assert result["purged"] == 1

        purged = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "to_purge")
        )).scalar_one_or_none()
        assert purged is None

        kept = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "keep_active")
        )).scalar_one_or_none()
        assert kept is not None

    async def test_does_not_purge_saved_ads(self, db: AsyncSession):
        from app.services.lifecycle import purge_old_ads

        ad = _make_ad(db, platform_ad_id="saved_ad", is_active=False,
                      last_seen=datetime.now(timezone.utc) - timedelta(days=60))
        await db.flush()

        user = User(
            email="saver@example.com",
            hashed_password=hash_password("pass123"),
            full_name="Saver", is_active=True, tier="free",
        )
        db.add(user)
        await db.flush()

        board = Board(user_id=user.id, name="My Board")
        db.add(board)
        await db.flush()

        board_ad = BoardAd(board_id=board.id, ad_id=ad.id)
        db.add(board_ad)
        await db.commit()

        result = await purge_old_ads(db, purge_days=30)
        assert result["purged"] == 0

        saved = (await db.execute(
            select(Ad).where(Ad.platform_ad_id == "saved_ad")
        )).scalar_one_or_none()
        assert saved is not None

    async def test_no_ads_to_purge(self, db: AsyncSession):
        from app.services.lifecycle import purge_old_ads

        _make_ad(db, is_active=True, last_seen=datetime.now(timezone.utc))
        await db.commit()

        result = await purge_old_ads(db, purge_days=30)
        assert result["purged"] == 0
