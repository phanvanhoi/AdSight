import pytest


@pytest.fixture
def sample_ad_data():
    return {
        "platform": "meta",
        "platform_ad_id": "test_123",
        "advertiser_name": "Test Store",
        "ad_type": "image",
        "headline": "Test Ad",
        "body_text": "This is a test ad",
        "target_countries": ["VN"],
        "likes": 100,
        "comments": 10,
        "shares": 5,
        "is_active": True,
    }
