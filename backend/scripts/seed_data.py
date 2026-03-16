"""Seed sample ads and test users for development/testing.

Usage:
    python -m scripts.seed_data
    python scripts/seed_data.py

Creates:
    - 2 test users: demo@adsight.vn (free), pro@adsight.vn (pro)
    - 25 sample ads (VN market, mix meta + tiktok, mix image/video/carousel)
    - Indexes ads into Elasticsearch

Idempotent: skips if seed data already exists.
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import async_session
from app.core.security import hash_password
from app.models.ad import Ad
from app.models.user import User
from app.search.es_client import es_client
from app.search.indexing import bulk_index_ads, create_ads_index

# ---------------------------------------------------------------------------
# Test users
# ---------------------------------------------------------------------------
TEST_USERS = [
    {
        "email": "demo@adsight.vn",
        "password": "demo1234",
        "full_name": "Demo User",
        "tier": "free",
    },
    {
        "email": "pro@adsight.vn",
        "password": "pro12345",
        "full_name": "Pro User",
        "tier": "pro",
    },
]

# ---------------------------------------------------------------------------
# Sample ads — 25 ads, mix meta + tiktok, mix ad types
# ---------------------------------------------------------------------------
SAMPLE_ADS = [
    # Meta — Beauty
    ("meta", "image", "Beauty Store VN", "Kem chống nắng SPF50+ giảm 50%",
     "Kem chống nắng hàng đầu Hàn Quốc, bảo vệ da 12 giờ. Mua ngay hôm nay giảm 50% chỉ còn 199K!",
     "shop_now", "beauty", 5200, 340, 120),
    ("meta", "carousel", "SkinCare Pro", "Serum Vitamin C - Trắng sáng sau 7 ngày",
     "Tinh chất Vitamin C 20% từ Nhật Bản. Da trắng sáng, mờ thâm nám chỉ sau 7 ngày sử dụng.",
     "shop_now", "beauty", 6700, 420, 190),
    ("meta", "video", "Mỹ Phẩm Hàn", "Son môi MAC chính hãng - Mua 1 tặng 1",
     "Son MAC chính hãng 100%. Chương trình mua 1 tặng 1 chỉ trong tháng này. Freeship toàn quốc!",
     "shop_now", "beauty", 3400, 280, 95),

    # Meta — Fashion
    ("meta", "video", "Fashion Hub", "BST Áo thun mới 2026 - Freeship toàn quốc",
     "Áo thun unisex cotton 100%, form rộng cực thoải mái. Đặt hàng ngay, giao trong 24h!",
     "shop_now", "fashion", 3100, 210, 88),
    ("meta", "image", "Giày Sneaker VN", "Giày thể thao chính hãng giảm 40%",
     "Nike, Adidas, New Balance chính hãng. Giảm đến 40% cuối mùa. Bảo hành 12 tháng.",
     "shop_now", "fashion", 4200, 310, 145),

    # Meta — Tech
    ("meta", "image", "TechWorld VN", "iPhone 16 Pro Max - Trả góp 0%",
     "iPhone 16 Pro Max chính hãng Apple. Trả góp 0% qua thẻ tín dụng. Bảo hành 24 tháng.",
     "learn_more", "technology", 8900, 560, 230),
    ("meta", "carousel", "Điện Máy Online", "Laptop gaming giảm sốc đến 30%",
     "Laptop ASUS ROG, MSI, Lenovo Legion giảm đến 30%. Tặng kèm chuột gaming + balo.",
     "shop_now", "technology", 2100, 180, 67),

    # Meta — Food
    ("meta", "video", "Foodie Express", "Gà rán Hàn Quốc - Đặt ngay giảm 30%",
     "Gà rán giòn tan kiểu Hàn Quốc, combo 6 miếng chỉ 99K. Đặt qua app giảm thêm 30K!",
     "order_now", "food", 4500, 890, 340),
    ("meta", "image", "Trà Sữa TocoToco", "Trà sữa size L chỉ 29K - Mua 2 giảm 10K",
     "Trà sữa trân châu hoàng gia size L chỉ 29K. Mua 2 ly giảm ngay 10K. Đặt qua GrabFood!",
     "order_now", "food", 1800, 230, 78),

    # Meta — Others
    ("meta", "image", "Travel VN", "Tour Đà Nẵng 3N2Đ chỉ 2.999K",
     "Tour Đà Nẵng - Hội An - Bà Nà Hills 3 ngày 2 đêm. Khách sạn 4 sao, xe đưa đón tận nơi.",
     "book_now", "travel", 2300, 150, 67),
    ("meta", "video", "Edu Smart", "Khóa học IELTS 7.0+ cam kết đầu ra",
     "Luyện thi IELTS cùng giáo viên bản ngữ. Cam kết 7.0+ hoặc hoàn tiền 100%. Học thử miễn phí!",
     "sign_up", "education", 1800, 290, 110),
    ("meta", "image", "Shopee Mall", "Flash Sale 12.12 - Giảm đến 70%",
     "Siêu sale 12.12 trên Shopee Mall. Hàng chính hãng giảm đến 70%. Freeship đơn từ 0đ!",
     "shop_now", "ecommerce", 12000, 1200, 890),
    ("meta", "video", "Gym Fitness VN", "Đăng ký Gym 12 tháng chỉ 99K/tháng",
     "Phòng gym tiêu chuẩn 5 sao, đầy đủ thiết bị nhập khẩu. PT hướng dẫn miễn phí tháng đầu.",
     "sign_up", "fitness", 950, 80, 35),
    ("meta", "image", "Pet Shop Sài Gòn", "Thức ăn cho mèo Royal Canin giảm 25%",
     "Royal Canin chính hãng nhập khẩu Pháp. Giảm 25% tất cả dòng thức ăn hạt cho mèo. Giao nhanh 2h.",
     "shop_now", "pets", 1500, 190, 55),

    # TikTok — Beauty
    ("tiktok", "video", "Glow Up Studio", "Review kem nền che phủ tốt nhất 2026",
     "Kem nền Maybelline Fit Me che phủ hoàn hảo, không lộ vân. Giá chỉ 159K tại TikTok Shop!",
     "shop_now", "beauty", 15000, 2300, 890),
    ("tiktok", "video", "Skincare Daily", "Toner gạo lứt Cocoon - Hàng Việt chất lượng",
     "Toner gạo lứt Cocoon giúp se khít lỗ chân lông, da căng mịn. 100% thiên nhiên, made in Vietnam.",
     "shop_now", "beauty", 8900, 1200, 560),

    # TikTok — Fashion
    ("tiktok", "video", "Local Brand VN", "Áo hoodie oversize mùa đông - Chỉ 199K",
     "Áo hoodie nỉ bông dày dặn, form oversize unisex. Ship COD toàn quốc. Đổi trả 7 ngày!",
     "shop_now", "fashion", 7600, 890, 420),
    ("tiktok", "video", "Giày Đẹp Store", "Giày dép sandal nữ hot trend 2026",
     "Sandal quai ngang phong cách Hàn Quốc, đế êm siêu nhẹ. Chỉ 149K - mua 2 giảm 20%.",
     "shop_now", "fashion", 5400, 670, 310),

    # TikTok — Food
    ("tiktok", "video", "Bếp Nhà Mình", "Cách làm bánh mì Việt Nam tại nhà",
     "Hướng dẫn làm bánh mì giòn rụm cực đơn giản. Nguyên liệu dễ tìm, ai cũng làm được!",
     "learn_more", "food", 23000, 4500, 2100),
    ("tiktok", "video", "Snack Factory", "Khô gà lá chanh - Đặc sản Sài Gòn",
     "Khô gà lá chanh giòn rụm, vị cay nhẹ. Đặt 500g tặng 100g. Ship COD toàn quốc.",
     "shop_now", "food", 6200, 980, 450),

    # TikTok — Tech & Education
    ("tiktok", "video", "Tech Review VN", "Đánh giá Samsung Galaxy S26 Ultra",
     "Samsung S26 Ultra camera 200MP, pin 5000mAh, sạc nhanh 45W. So sánh chi tiết với iPhone 16 Pro Max.",
     "learn_more", "technology", 18000, 3200, 1500),
    ("tiktok", "video", "Học Lập Trình", "Học Python từ zero đến hero trong 30 ngày",
     "Khóa học Python miễn phí cho người mới bắt đầu. Học xong có thể làm data analyst, web dev.",
     "sign_up", "education", 11000, 1800, 890),

    # TikTok — Others
    ("tiktok", "video", "Nội Thất Decor", "Decor phòng ngủ aesthetic chỉ với 500K",
     "Biến phòng ngủ thành không gian Hàn Quốc với 500K. Đèn LED, rèm cửa, gối ôm fullset.",
     "shop_now", "home_decor", 9300, 1400, 670),
    ("tiktok", "video", "Baby Care VN", "Bỉm Merries nội địa Nhật - Giá sỉ",
     "Bỉm Merries nội địa Nhật chính hãng, giá sỉ lẻ tốt nhất. Mềm mại, thấm hút tốt, không hăm.",
     "shop_now", "baby", 3800, 450, 210),
    ("tiktok", "video", "Xe Máy Sài Gòn", "Honda Vision 2026 - Trả góp chỉ 3 triệu/tháng",
     "Honda Vision 2026 mới nhất, đủ màu. Trả góp từ 3 triệu/tháng, thủ tục nhanh gọn.",
     "learn_more", "automotive", 4100, 520, 180),
]


async def seed_users(db) -> int:
    """Seed test users. Returns count of newly created users."""
    created = 0
    for u in TEST_USERS:
        result = await db.execute(select(User).where(User.email == u["email"]))
        if result.scalar_one_or_none():
            print(f"  User {u['email']} already exists, skipping")
            continue
        user = User(
            email=u["email"],
            hashed_password=hash_password(u["password"]),
            full_name=u["full_name"],
            tier=u["tier"],
            is_active=True,
        )
        db.add(user)
        created += 1
        print(f"  Created user: {u['email']} (tier={u['tier']})")
    return created


async def seed_ads(db) -> tuple[int, list[dict]]:
    """Seed sample ads. Returns (count_created, es_docs)."""
    # Check if seed data already exists
    result = await db.execute(
        select(Ad).where(Ad.platform_ad_id.like("%_seed_%")).limit(1)
    )
    if result.scalar_one_or_none():
        print("  Seed ads already exist, skipping")
        return 0, []

    now = datetime.now(timezone.utc)
    random.seed(42)  # Deterministic for reproducibility
    es_docs = []

    for i, (platform, ad_type, advertiser, headline, body, cta, category,
            likes, comments, shares) in enumerate(SAMPLE_ADS):
        ad_id = uuid.uuid4()
        first_seen = now - timedelta(days=random.randint(3, 45))
        platform_ad_id = f"{platform}_seed_{i:03d}"

        ad = Ad(
            id=ad_id,
            platform=platform,
            platform_ad_id=platform_ad_id,
            advertiser_name=advertiser,
            ad_type=ad_type,
            headline=headline,
            body_text=body,
            cta_type=cta,
            target_countries=["VN"],
            likes=likes,
            comments=comments,
            shares=shares,
            category=category,
            language="vi",
            is_active=True,
            first_seen=first_seen,
            last_seen=now,
        )
        db.add(ad)

        es_docs.append({
            "id": str(ad_id),
            "platform": platform,
            "platform_ad_id": platform_ad_id,
            "advertiser_name": advertiser,
            "ad_type": ad_type,
            "headline": headline,
            "body_text": body,
            "cta_type": cta,
            "target_countries": ["VN"],
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "category": category,
            "language": "vi",
            "is_active": True,
            "first_seen": first_seen.isoformat(),
            "last_seen": now.isoformat(),
        })

    return len(SAMPLE_ADS), es_docs


async def main():
    print("=== AdSight Seed Data ===\n")

    # --- Users ---
    print("[1/3] Seeding users...")
    async with async_session() as db:
        user_count = await seed_users(db)
        await db.commit()
    print(f"  Users done: {user_count} created\n")

    # --- Ads (PostgreSQL) ---
    print("[2/3] Seeding ads into PostgreSQL...")
    async with async_session() as db:
        ad_count, es_docs = await seed_ads(db)
        if ad_count:
            await db.commit()
    print(f"  Ads done: {ad_count} created\n")

    # --- Ads (Elasticsearch) ---
    print("[3/3] Indexing ads into Elasticsearch...")
    if es_docs:
        try:
            await es_client.initialize()
            es = es_client.client
            await create_ads_index(es)
            await bulk_index_ads(es, es_docs)
            await es_client.close()
            print(f"  Indexed {len(es_docs)} ads into Elasticsearch\n")
        except Exception as e:
            print(f"  WARNING: Elasticsearch not available ({e})")
            print("  Ads were saved to PostgreSQL but not indexed.\n")
    else:
        print("  No new ads to index\n")

    print("=== Seed complete ===")


if __name__ == "__main__":
    asyncio.run(main())
