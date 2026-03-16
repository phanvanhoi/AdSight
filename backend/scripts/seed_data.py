"""Seed sample ads for development/testing."""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from app.core.database import async_session
from app.models.ad import Ad
from app.search.es_client import es_client
from app.search.indexing import bulk_index_ads, create_ads_index

SAMPLE_ADS = [
    {
        "platform": "meta",
        "platform_ad_id": f"meta_sample_{i}",
        "advertiser_name": name,
        "ad_type": ad_type,
        "headline": headline,
        "body_text": body,
        "cta_type": cta,
        "target_countries": ["VN"],
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "category": cat,
        "language": "vi",
        "is_active": True,
    }
    for i, (name, ad_type, headline, body, cta, likes, comments, shares, cat) in enumerate([
        ("Beauty Store VN", "image", "Kem chống nắng SPF50+ giảm 50%",
         "Kem chống nắng hàng đầu Hàn Quốc, bảo vệ da 12 giờ. Mua ngay hôm nay giảm 50% chỉ còn 199K!",
         "shop_now", 5200, 340, 120, "beauty"),
        ("Fashion Hub", "video", "BST Áo thun mới 2026 - Freeship toàn quốc",
         "Áo thun unisex cotton 100%, form rộng cực thoải mái. Đặt hàng ngay, giao trong 24h!",
         "shop_now", 3100, 210, 88, "fashion"),
        ("TechWorld VN", "image", "iPhone 16 Pro Max - Trả góp 0%",
         "iPhone 16 Pro Max chính hãng Apple. Trả góp 0% qua thẻ tín dụng. Bảo hành 24 tháng.",
         "learn_more", 8900, 560, 230, "technology"),
        ("Foodie Express", "video", "Gà rán Hàn Quốc - Đặt ngay giảm 30%",
         "Gà rán giòn tan kiểu Hàn Quốc, combo 6 miếng chỉ 99K. Đặt qua app giảm thêm 30K!",
         "order_now", 4500, 890, 340, "food"),
        ("SkinCare Pro", "carousel", "Serum Vitamin C - Trắng sáng sau 7 ngày",
         "Tinh chất Vitamin C 20% từ Nhật Bản. Da trắng sáng, mờ thâm nám chỉ sau 7 ngày sử dụng.",
         "shop_now", 6700, 420, 190, "beauty"),
        ("Travel VN", "image", "Tour Đà Nẵng 3N2Đ chỉ 2.999K",
         "Tour Đà Nẵng - Hội An - Bà Nà Hills 3 ngày 2 đêm. Khách sạn 4 sao, xe đưa đón tận nơi.",
         "book_now", 2300, 150, 67, "travel"),
        ("Edu Smart", "video", "Khóa học IELTS 7.0+ cam kết đầu ra",
         "Luyện thi IELTS cùng giáo viên bản ngữ. Cam kết 7.0+ hoặc hoàn tiền 100%. Học thử miễn phí!",
         "sign_up", 1800, 290, 110, "education"),
        ("Shopee Mall", "image", "Flash Sale 12.12 - Giảm đến 70%",
         "Siêu sale 12.12 trên Shopee Mall. Hàng chính hãng giảm đến 70%. Freeship đơn từ 0đ!",
         "shop_now", 12000, 1200, 890, "ecommerce"),
        ("Gym Fitness VN", "video", "Đăng ký Gym 12 tháng chỉ 99K/tháng",
         "Phòng gym tiêu chuẩn 5 sao, đầy đủ thiết bị nhập khẩu. PT hướng dẫn miễn phí tháng đầu.",
         "sign_up", 950, 80, 35, "fitness"),
        ("Pet Shop Sài Gòn", "image", "Thức ăn cho mèo Royal Canin giảm 25%",
         "Royal Canin chính hãng nhập khẩu Pháp. Giảm 25% tất cả dòng thức ăn hạt cho mèo. Giao nhanh 2h.",
         "shop_now", 1500, 190, 55, "pets"),
    ])
]


async def main():
    await es_client.initialize()
    es = es_client.client
    await create_ads_index(es)

    now = datetime.now(timezone.utc)
    ads_for_es = []

    async with async_session() as db:
        for i, ad_data in enumerate(SAMPLE_ADS):
            ad_id = uuid.uuid4()
            first_seen = now - timedelta(days=30 - i * 2)
            ad = Ad(
                id=ad_id,
                platform=ad_data["platform"],
                platform_ad_id=ad_data["platform_ad_id"],
                advertiser_name=ad_data["advertiser_name"],
                ad_type=ad_data["ad_type"],
                headline=ad_data["headline"],
                body_text=ad_data["body_text"],
                cta_type=ad_data["cta_type"],
                target_countries=ad_data["target_countries"],
                likes=ad_data["likes"],
                comments=ad_data["comments"],
                shares=ad_data["shares"],
                category=ad_data["category"],
                language=ad_data["language"],
                is_active=ad_data["is_active"],
                first_seen=first_seen,
                last_seen=now,
            )
            db.add(ad)

            es_doc = {
                **ad_data,
                "id": str(ad_id),
                "first_seen": first_seen.isoformat(),
                "last_seen": now.isoformat(),
            }
            ads_for_es.append(es_doc)

        await db.commit()
        print(f"Inserted {len(SAMPLE_ADS)} sample ads into PostgreSQL")

    await bulk_index_ads(es, ads_for_es)
    print(f"Indexed {len(ads_for_es)} ads into Elasticsearch")
    await es_client.close()


if __name__ == "__main__":
    asyncio.run(main())
