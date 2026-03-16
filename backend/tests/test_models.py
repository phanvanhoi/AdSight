"""Tests for SQLAlchemy model constraints."""
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.board import Board
from app.models.board_ad import BoardAd
from app.models.user import User
from app.core.security import hash_password


@pytest.mark.asyncio
class TestAdUniqueConstraint:
    async def test_duplicate_platform_ad_id_raises(self, db: AsyncSession):
        ad1 = Ad(
            platform="meta",
            platform_ad_id="dup_123",
            ad_type="image",
        )
        db.add(ad1)
        await db.commit()

        ad2 = Ad(
            platform="meta",
            platform_ad_id="dup_123",
            ad_type="video",
        )
        db.add(ad2)
        with pytest.raises(IntegrityError):
            await db.commit()

    async def test_same_id_different_platform_ok(self, db: AsyncSession):
        ad1 = Ad(platform="meta", platform_ad_id="shared_id", ad_type="image")
        ad2 = Ad(platform="tiktok", platform_ad_id="shared_id", ad_type="video")
        db.add_all([ad1, ad2])
        await db.commit()  # should not raise


@pytest.mark.asyncio
class TestBoardCascadeDelete:
    async def test_delete_board_cascades_to_board_ads(self, db: AsyncSession):
        # Create user
        user = User(
            email="cascade@test.com",
            hashed_password=hash_password("testpass123"),
            full_name="Cascade Test",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Create ad
        ad = Ad(platform="meta", platform_ad_id="cascade_ad", ad_type="image")
        db.add(ad)
        await db.commit()
        await db.refresh(ad)

        # Create board
        board = Board(name="Will Delete", user_id=user.id)
        db.add(board)
        await db.commit()
        await db.refresh(board)

        # Create board_ad link
        ba = BoardAd(board_id=board.id, ad_id=ad.id)
        db.add(ba)
        await db.commit()
        ba_id = ba.id

        # Delete board
        await db.delete(board)
        await db.commit()

        # BoardAd should be gone
        result = await db.execute(select(BoardAd).where(BoardAd.id == ba_id))
        assert result.scalar_one_or_none() is None

        # Ad should still exist
        result = await db.execute(select(Ad).where(Ad.id == ad.id))
        assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
class TestAdJsonbDefaults:
    async def test_jsonb_fields_default_none(self, db: AsyncSession):
        ad = Ad(
            platform="meta",
            platform_ad_id="defaults_test",
            ad_type="image",
        )
        db.add(ad)
        await db.commit()
        await db.refresh(ad)

        assert ad.media_urls is None
        assert ad.media_s3_keys is None
        assert ad.target_countries is None
        assert ad.target_interests is None
        assert ad.tags is None

    async def test_jsonb_fields_not_shared_across_instances(self, db: AsyncSession):
        """Two ads with default JSONB should not share the same object."""
        ad1 = Ad(platform="meta", platform_ad_id="share_1", ad_type="image")
        ad2 = Ad(platform="meta", platform_ad_id="share_2", ad_type="image")
        # Both should be None (independent), not a shared mutable list
        assert ad1.media_urls is None
        assert ad2.media_urls is None
        assert ad1.tags is None
        assert ad2.tags is None
