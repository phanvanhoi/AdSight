"""Tests for cross-platform advertiser matching — 11 tests."""

import uuid
from datetime import datetime, timezone

import pytest

from app.enrichment.advertiser_matching import (
    extract_domain,
    match_advertisers,
    name_similarity,
    normalize_advertiser_name,
    remove_diacritics,
)
from app.models.ad import Ad


class TestNormalizeName:
    def test_remove_suffixes(self):
        # " official" and " vn" are removed, "shop" at start stays
        assert normalize_advertiser_name("ABC Official VN") == "abc"

    def test_strip_and_collapse(self):
        result = normalize_advertiser_name("  Thời Trang VN  ")
        assert result == "thời trang"

    def test_empty(self):
        assert normalize_advertiser_name("") == ""


class TestRemoveDiacritics:
    def test_vietnamese(self):
        assert remove_diacritics("Mỹ Phẩm Hàn") == "my pham han"

    def test_already_ascii(self):
        assert remove_diacritics("hello world") == "hello world"


class TestNameSimilarity:
    def test_exact_match_after_normalize(self):
        # Both normalize to "abc" after removing suffixes
        assert name_similarity("ABC Official", "ABC VN") == 1.0

    def test_token_overlap(self):
        score = name_similarity("Shop ABC", "ABC Shop")
        assert score >= 0.8  # Contains each other after normalize

    def test_low_score(self):
        score = name_similarity("Beauty Store Official", "Food Market Official")
        assert score < 0.7

    def test_empty_strings(self):
        assert name_similarity("", "") == 0.0
        assert name_similarity("Test", "") == 0.0


class TestExtractDomain:
    def test_normal_url(self):
        assert extract_domain("https://www.example.com/path") == "example.com"

    def test_skip_platform_domains(self):
        assert extract_domain("https://facebook.com/page123") is None
        assert extract_domain("https://tiktok.com/@user") is None

    def test_none_url(self):
        assert extract_domain(None) is None

    def test_empty_url(self):
        assert extract_domain("") is None


class TestMatchAdvertisers:
    @pytest.mark.asyncio
    async def test_cross_platform_group_created(self, db):
        """Two advertisers with same name on different platforms → 1 group."""
        ad1 = Ad(
            id=uuid.uuid4(),
            platform="meta",
            platform_ad_id="m_001",
            advertiser_id="meta_page_1",
            advertiser_name="Beauty Shop VN",
            ad_type="image",
            is_active=True,
        )
        ad2 = Ad(
            id=uuid.uuid4(),
            platform="tiktok",
            platform_ad_id="t_001",
            advertiser_id="tiktok_adv_1",
            advertiser_name="Beauty Shop VN",
            ad_type="video",
            is_active=True,
        )
        db.add_all([ad1, ad2])
        await db.commit()

        result = await match_advertisers(db)
        assert result["groups_created"] == 1
        assert result["ads_matched"] == 2

    @pytest.mark.asyncio
    async def test_single_platform_no_group(self, db):
        """Single platform advertiser → no group created."""
        ad1 = Ad(
            id=uuid.uuid4(),
            platform="meta",
            platform_ad_id="m_010",
            advertiser_id="meta_page_10",
            advertiser_name="Solo Brand",
            ad_type="image",
            is_active=True,
        )
        ad2 = Ad(
            id=uuid.uuid4(),
            platform="meta",
            platform_ad_id="m_011",
            advertiser_id="meta_page_10",
            advertiser_name="Solo Brand",
            ad_type="image",
            is_active=True,
        )
        db.add_all([ad1, ad2])
        await db.commit()

        result = await match_advertisers(db)
        assert result["groups_created"] == 0
