"""Seed sample data for development/demo.

Usage:
    python -m scripts.seed_data

Creates:
    - 2 test users
    - 50 ads (20 meta, 20 tiktok, 10 google) with enrichment data
    - 5 TikTok shops with ~50 products
    - 10 advertiser groups (cross-platform)
    - 20 landing page info records
    - Indexes ads into Elasticsearch

Idempotent: skips if seed data already exists.
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func

from app.core.database import async_session, engine
from app.core.security import hash_password
from app.models.base import Base
from app.models.ad import Ad
from app.models.user import User
from app.models.tiktok_shop import TikTokShop, TikTokShopProduct
from app.models.advertiser_group import AdvertiserGroup
from app.models.landing_page import LandingPageInfo
from app.search.es_client import es_client
from app.search.indexing import bulk_index_ads

NOW = datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# Test users
# ---------------------------------------------------------------------------
TEST_USERS = [
    {"email": "demo@adsight.vn", "password": "demo1234", "full_name": "Demo User", "tier": "free"},
    {"email": "pro@adsight.vn", "password": "pro12345", "full_name": "Pro User", "tier": "pro"},
]

# ---------------------------------------------------------------------------
# 50 Ads — 20 meta, 20 tiktok, 10 google
# (platform, ad_type, advertiser_name, advertiser_id, headline, body_text,
#  cta_type, category_l1, category_l2, target_gender,
#  likes_range, comments_range, shares_range)
# ---------------------------------------------------------------------------
AD_TEMPLATES = [
    # ── META (20) ──────────────────────────────────────────────────────
    # Làm đẹp - Skincare (3)
    ("meta", "image", "Laneige VN", "adv_laneige_m",
     "Serum Vitamin C giá sốc - Giảm 40% chỉ hôm nay!",
     "🔥 FLASH SALE chỉ 24H! Serum Vitamin C 20% - Sáng da sau 2 tuần sử dụng.\n✅ Chiết xuất thiên nhiên 100%\n✅ Phù hợp mọi loại da\n✅ Free ship đơn từ 300K\n👉 Đặt ngay kẻo hết!",
     "SHOP_NOW", "Làm đẹp", "Skincare", "female",
     (3000, 15000), (200, 2000), (100, 800)),
    ("meta", "carousel", "Innisfree VN", "adv_innisfree_m",
     "Kem chống nắng SPF50+ PA++++ không nhờn dính",
     "☀️ Bảo vệ da suốt 12 giờ dưới nắng gắt\n🌿 100% chiết xuất tự nhiên từ đảo Jeju\n💰 Chỉ 289K (giá gốc 420K)\nMua ngay tại Shopee Mall!",
     "SHOP_NOW", "Làm đẹp", "Skincare", "female",
     (2000, 8000), (150, 1000), (50, 500)),
    ("meta", "video", "The Ordinary VN", "adv_ordinary_m",
     "Niacinamide 10% + Zinc 1% - Kiểm soát dầu hoàn hảo",
     "Serum kiểm soát dầu #1 thế giới 🌍\nGiảm mụn, thu nhỏ lỗ chân lông\nĐã bán 50,000+ chai tại VN\nGiá chỉ 199K - Ship COD toàn quốc",
     "SHOP_NOW", "Làm đẹp", "Skincare", "all",
     (5000, 20000), (300, 3000), (200, 1500)),

    # Làm đẹp - Makeup (2)
    ("meta", "video", "3CE VN", "adv_3ce_m",
     "Son kem lì mới - 12 màu trendy nhất 2026 💄",
     "💄 SON KEM LÌ MỚI - 12 MÀU TRENDY 2026\nBền màu 12h, không transfer, dưỡng ẩm\nGiá chỉ 189K (giá gốc 350K)\n🎁 Tặng son mini khi mua 2 cây\nShip COD toàn quốc 🚚",
     "SHOP_NOW", "Làm đẹp", "Makeup", "female",
     (8000, 30000), (500, 4000), (300, 2000)),
    ("meta", "image", "Maybelline VN", "adv_maybelline_m",
     "Mascara Lash Sensational - Mi cong vút 24h",
     "Mascara #1 toàn cầu đã có mặt tại VN 🇻🇳\nCông thức chống nước, không vón cục\nGiảm 30% khi mua qua TikTok Shop\n⏰ Chỉ còn 24h!",
     "SHOP_NOW", "Làm đẹp", "Makeup", "female",
     (4000, 12000), (200, 1500), (100, 800)),

    # Thời trang (3)
    ("meta", "video", "YODY", "adv_yody_m",
     "Đầm công sở thanh lịch - Chỉ từ 299K 👗",
     "👗 BST Đầm Công Sở Mới 2026\nChất liệu cao cấp, form chuẩn dáng\nSize S-XXL - Free đổi trả 30 ngày\n🚚 Freeship đơn từ 500K",
     "SHOP_NOW", "Thời trang", "Thời trang nữ", "female",
     (3000, 10000), (200, 1500), (100, 600)),
    ("meta", "image", "Canifa", "adv_canifa_m",
     "Áo khoác gió nam - Nhẹ, chống nước, giá tốt",
     "Áo khoác gió siêu nhẹ, chống nước cấp 3\nCuộn gọn bỏ túi, đi du lịch cực tiện\nChỉ 399K - Giảm thêm 10% cho đơn đầu tiên",
     "SHOP_NOW", "Thời trang", "Thời trang nam", "male",
     (2000, 7000), (100, 800), (50, 400)),
    ("meta", "carousel", "Elise", "adv_elise_m",
     "BST Xuân Hè 2026 - Thanh lịch & Hiện đại",
     "🌸 BST mới nhất từ Elise\nThiết kế Pháp, sản xuất tại VN\nƯu đãi 20% cho khách hàng mới\nGhé store hoặc đặt online ngay!",
     "SHOP_NOW", "Thời trang", "Thời trang nữ", "female",
     (1500, 6000), (80, 500), (40, 300)),

    # Công nghệ (3)
    ("meta", "image", "Samsung VN", "adv_samsung_m",
     "Galaxy S26 Ultra - Đặt trước giảm 3 triệu 📱",
     "📱 SAMSUNG GALAXY S26 ULTRA\n- Camera 200MP AI Photography\n- Pin 5000mAh sạc 45W\n🎉 Đặt trước: Giảm 3.000.000đ\n🎁 Tặng ốp lưng + cường lực\nTrả góp 0% qua mọi ngân hàng",
     "LEARN_MORE", "Công nghệ", "Điện thoại", "all",
     (10000, 40000), (800, 5000), (500, 3000)),
    ("meta", "video", "OPPO VN", "adv_oppo_m",
     "OPPO Find X8 Pro - Camera Hasselblad đỉnh cao",
     "Camera Hasselblad chuyên nghiệp trên điện thoại 📸\nChụp đêm AI siêu sáng\nSạc nhanh SUPERVOOC 100W\nGiá chỉ 22.990.000đ",
     "LEARN_MORE", "Công nghệ", "Điện thoại", "all",
     (6000, 20000), (400, 3000), (200, 1500)),
    ("meta", "image", "Baseus VN", "adv_baseus_m",
     "Sạc nhanh 120W - Pin đầy trong 15 phút ⚡",
     "⚡ Sạc nhanh Baseus 120W GaN5\n- Sạc iPhone 15: 0→50% trong 18 phút\n- Nhỏ gọn bằng nắm tay\n- Bảo vệ pin thông minh\nGiá: 499K (gốc 799K) 🎉",
     "SHOP_NOW", "Công nghệ", "Phụ kiện", "all",
     (3000, 10000), (200, 1500), (100, 800)),

    # F&B (2)
    ("meta", "video", "Highlands Coffee", "adv_highlands_m",
     "Trà sữa topping mới - Chỉ 29K size L 🧋",
     "🧋 MỚI! Trà Sữa Kem Cheese Matcha\nTopping trân châu đen + thạch kem cheese\nSize L chỉ 29K (áp dụng app)\n📍 Giao hàng tận nơi qua GrabFood",
     "ORDER_NOW", "F&B", "Đồ uống", "all",
     (5000, 18000), (400, 2500), (200, 1200)),
    ("meta", "image", "Vinamilk", "adv_vinamilk_m",
     "Sữa tươi organic - Mua 6 tặng 1 🥛",
     "🥛 Sữa tươi Organic chuẩn Châu Âu\n✅ Không đường, không chất bảo quản\n✅ Nguồn sữa từ trang trại hữu cơ\n🎁 Mua 6 hộp tặng 1 - Chỉ trong tháng này!",
     "SHOP_NOW", "F&B", "Thực phẩm", "all",
     (2000, 8000), (100, 800), (50, 400)),

    # Giáo dục (1)
    ("meta", "video", "IELTS Fighter", "adv_ielts_m",
     "IELTS 7.0 trong 3 tháng - Cam kết đầu ra 🎓",
     "🎓 IELTS 7.0 TRONG 3 THÁNG\n✅ Giáo viên 8.0+ IELTS\n✅ Lớp tối đa 15 học viên\n✅ Cam kết đầu ra hoặc học lại FREE\n📞 Đăng ký tư vấn miễn phí ngay!",
     "SIGN_UP", "Giáo dục", "Khóa học online", "all",
     (3000, 12000), (300, 2000), (150, 1000)),

    # Sức khỏe (1)
    ("meta", "image", "DHC VN", "adv_dhc_m",
     "Vitamin tổng hợp cho phụ nữ - Giảm 30% 💊",
     "💊 DHC Vitamin Tổng Hợp\nBổ sung 13 loại vitamin + khoáng chất\nHỗ trợ da đẹp, tóc khỏe, móng chắc\nGiảm 30% chỉ trong tuần này - Hàng nội địa Nhật 🇯🇵",
     "SHOP_NOW", "Sức khỏe", "Thực phẩm chức năng", "female",
     (2000, 8000), (150, 1000), (80, 500)),

    # Bất động sản (1)
    ("meta", "video", "Vinhomes", "adv_vinhomes_m",
     "Căn hộ view sông Sài Gòn - Chỉ từ 2.5 tỷ 🏠",
     "🏠 VINHOMES GOLDEN RIVER\n- Căn hộ cao cấp view sông Sài Gòn\n- Tiện ích 5 sao: Hồ bơi, gym, spa\n- Giá chỉ từ 2.5 tỷ/căn\n- Trả góp ưu đãi 0% trong 36 tháng\n📞 Hotline: 1900.xxxx",
     "LEARN_MORE", "Bất động sản", "Căn hộ", "all",
     (4000, 15000), (300, 2000), (200, 1000)),

    # ── TIKTOK (20) ──────────────────────────────────────────────────
    # Làm đẹp (4)
    ("tiktok", "video", "Laneige VN", "adv_laneige_t",
     "Water Sleeping Mask - Mặt nạ ngủ bán chạy #1",
     "✨ Water Sleeping Mask - Best seller toàn cầu\nCấp ẩm suốt đêm, da căng mọng khi thức dậy\n🛒 Mua ngay tại TikTok Shop: Giảm 35%\n#laneige #skincare #matnanongu",
     "SHOP_NOW", "Làm đẹp", "Skincare", "female",
     (15000, 50000), (2000, 8000), (800, 4000)),
    ("tiktok", "video", "Innisfree VN", "adv_innisfree_t",
     "Green Tea Seed Serum - Da ẩm mịn cả ngày",
     "🍵 Green Tea Seed Serum #1 bán chạy\nChiết xuất trà xanh Jeju 100%\nGiữ ẩm 72h, phù hợp mọi loại da\n💰 199K tại TikTok Shop (gốc 350K)",
     "SHOP_NOW", "Làm đẹp", "Skincare", "female",
     (8000, 25000), (1000, 4000), (500, 2500)),
    ("tiktok", "video", "3CE VN", "adv_3ce_t",
     "Bảng phấn mắt 9 màu - Tone nâu đất cực hot",
     "🎨 Bảng phấn mắt 3CE Multi Eye Color Palette\n9 màu nâu đất phù hợp da Việt\nBột mịn, bám màu 12h\n✅ Chính hãng 100% - Có tem chống giả",
     "SHOP_NOW", "Làm đẹp", "Makeup", "female",
     (12000, 35000), (1500, 5000), (700, 3000)),
    ("tiktok", "video", "Cocoon VN", "adv_cocoon_t",
     "Toner gạo lứt Việt Nam - Thuần chay, an toàn",
     "🌾 Toner Gạo Lứt Cocoon\nThương hiệu Việt - Thuần chay 100%\nSe khít lỗ chân lông, da sáng mịn\nChỉ 135K - Đã bán 100,000+ chai 🎉",
     "SHOP_NOW", "Làm đẹp", "Skincare", "all",
     (20000, 60000), (3000, 10000), (1500, 6000)),

    # Thời trang (4)
    ("tiktok", "video", "YODY", "adv_yody_t",
     "Áo polo nam cotton cao cấp - Free ship toàn quốc",
     "👔 Áo Polo Nam YODY\nCotton 100% cao cấp, thấm hút mồ hôi\nForm slim fit chuẩn dáng\nGiá: 259K - Free ship đơn từ 299K\n#yody #poloshirt #thoitrangnam",
     "SHOP_NOW", "Thời trang", "Thời trang nam", "male",
     (7000, 22000), (800, 3000), (400, 1800)),
    ("tiktok", "video", "Routine", "adv_routine_t",
     "Quần jeans nam slim fit - Thoải mái suốt ngày",
     "👖 Quần Jeans Slim Fit Routine\nVải denim co giãn 4 chiều\nĐứng form, thoải mái vận động\nSize 28-36 - Đổi trả 15 ngày\nChỉ 399K tại TikTok Shop 🛒",
     "SHOP_NOW", "Thời trang", "Thời trang nam", "male",
     (5000, 15000), (500, 2000), (200, 1200)),
    ("tiktok", "video", "Local Brand VN", "adv_localbrand_t",
     "Áo hoodie oversize - Bán chạy nhất mùa đông",
     "🧥 Hoodie Oversize Unisex\nNỉ bông dày dặn 350gsm\nIn tràn chất lượng cao, không phai\nChỉ 199K - Ship COD toàn quốc 🚚\n#hoodie #streetwear #localbrand",
     "SHOP_NOW", "Thời trang", "Thời trang nữ", "all",
     (10000, 30000), (1200, 4500), (600, 2500)),
    ("tiktok", "video", "Aristino", "adv_aristino_t",
     "Sơ mi nam công sở - Chất vải lụa Hàn",
     "👔 Sơ Mi Lụa Aristino - Bộ sưu tập 2026\nVải lụa Hàn mát lạnh, ít nhăn\n15 màu phối dễ dàng\nGiá: 459K (gốc 650K)\n✅ Miễn phí ủi thẳng khi mua tại shop",
     "SHOP_NOW", "Thời trang", "Thời trang nam", "male",
     (3000, 10000), (300, 1500), (150, 800)),

    # Công nghệ (3)
    ("tiktok", "video", "Samsung VN", "adv_samsung_t",
     "Galaxy Tab S10 - Máy tính bảng cho sinh viên",
     "📱 Galaxy Tab S10 FE\nMàn hình 10.9\" Super AMOLED\nBút S Pen đi kèm - Ghi chú siêu tiện\nGiá sinh viên: 7.990.000đ\n🎁 Tặng bao da + ốp lưng",
     "SHOP_NOW", "Công nghệ", "Điện thoại", "all",
     (8000, 25000), (1000, 4000), (500, 2000)),
    ("tiktok", "video", "Anker VN", "adv_anker_t",
     "Pin sạc dự phòng 20000mAh - Sạc 3 lần iPhone",
     "🔋 Anker PowerCore 20000\nSạc nhanh 22.5W, sạc 3 lần iPhone 16\nNhỏ gọn, nhẹ chỉ 340g\nĐã bán 200,000+ tại VN\nGiá: 399K 🎉",
     "SHOP_NOW", "Công nghệ", "Phụ kiện", "all",
     (6000, 18000), (700, 2500), (300, 1500)),
    ("tiktok", "video", "Tech Review VN", "adv_techreview_t",
     "So sánh iPhone 16 vs Samsung S26 - Ai thắng?",
     "📱 BATTLE 2026: iPhone 16 Pro Max vs Galaxy S26 Ultra\nCamera, hiệu năng, pin - Test thực tế\n💬 Comment chọn team nào!\n#iphone16 #galaxys26 #sosanh",
     "LEARN_MORE", "Công nghệ", "Điện thoại", "all",
     (25000, 80000), (5000, 15000), (2000, 8000)),

    # F&B (3)
    ("tiktok", "video", "The Coffee House", "adv_coffeehouse_t",
     "CloudTea mới - Trà sữa mây bông siêu mềm",
     "☁️ MỚI! CloudTea - Trà Sữa Mây Bông\nFoam kem cheese mềm như mây\nVị trà oolong đậm đà\nChỉ 35K size M tại app 📱\n#thecoffeehouse #cloudtea #trasua",
     "ORDER_NOW", "F&B", "Đồ uống", "all",
     (15000, 45000), (2000, 7000), (1000, 4000)),
    ("tiktok", "video", "Bếp Nhà Mình", "adv_bepnha_t",
     "Cách làm phở bò tại nhà - Chuẩn vị Hà Nội",
     "🍜 PHỞ BÒ HÀ NỘI tại nhà\nBí quyết nước dùng trong veo, ngọt xương\nNguyên liệu dễ mua, ai cũng nấu được\n👨‍🍳 Follow để xem thêm công thức mỗi ngày!",
     "LEARN_MORE", "F&B", "Thực phẩm", "all",
     (30000, 100000), (5000, 20000), (3000, 10000)),
    ("tiktok", "video", "Snack Import VN", "adv_snack_t",
     "Snack Hàn Quốc combo 10 gói - Giá sỉ",
     "🍿 COMBO 10 GÓI SNACK HÀN QUỐC\nHoney Butter Chip, Pepero, Choco Pie...\nHạn sử dụng dài, hàng nội địa Hàn\nChỉ 189K/combo - Ship COD 🚚",
     "SHOP_NOW", "F&B", "Thực phẩm", "all",
     (8000, 25000), (1000, 3500), (500, 2000)),

    # Giáo dục (2)
    ("tiktok", "video", "Topica", "adv_topica_t",
     "Học tiếng Anh 1-1 với giáo viên bản ngữ",
     "🎓 HỌC TIẾNG ANH ONLINE 1-1\n👨‍🏫 Giáo viên Mỹ/Anh/Úc\n📅 Lịch học linh hoạt 24/7\n💰 Chỉ từ 89K/buổi\n🎁 Đăng ký ngay: Tặng 2 buổi học thử FREE!",
     "SIGN_UP", "Giáo dục", "Khóa học online", "all",
     (6000, 20000), (800, 3000), (400, 1800)),
    ("tiktok", "video", "Học Lập Trình", "adv_hoclaptrinh_t",
     "Python từ zero - Lương 15 triệu sau 6 tháng",
     "💻 KHÓA HỌC PYTHON THỰC CHIẾN\nTừ zero đến được việc trong 6 tháng\n✅ 200+ bài tập thực hành\n✅ Project thực tế cuối khóa\n✅ Hỗ trợ tìm việc sau khóa học\nĐăng ký: Link bio 👆",
     "SIGN_UP", "Giáo dục", "Khóa học online", "all",
     (12000, 35000), (2000, 6000), (800, 3500)),

    # Sức khỏe (2)
    ("tiktok", "video", "Blackmores VN", "adv_blackmores_t",
     "Dầu cá Omega-3 - Tốt cho tim mạch & trí não",
     "🐟 Blackmores Fish Oil 1000mg\nOmega-3 hàm lượng cao từ Úc\nTốt cho tim mạch, trí não, mắt\nHộp 200 viên - Giá: 450K\n✅ Chính hãng - Tem chống giả",
     "SHOP_NOW", "Sức khỏe", "Thực phẩm chức năng", "all",
     (5000, 15000), (600, 2000), (300, 1200)),
    ("tiktok", "video", "Nhà Thuốc An Khang", "adv_ankhang_t",
     "Vitamin C 1000mg - Tăng đề kháng mùa dịch",
     "💊 Vitamin C 1000mg - DHC Nhật Bản\nTăng cường miễn dịch, sáng da\nUống mỗi ngày 1 viên\nGiá chỉ 99K/gói 30 ngày\n🚚 Giao nhanh 2h nội thành",
     "SHOP_NOW", "Sức khỏe", "Thực phẩm chức năng", "all",
     (4000, 12000), (400, 1500), (200, 800)),

    # ── GOOGLE (10) ──────────────────────────────────────────────────
    ("google", "image", "Shopee VN", "adv_shopee_g",
     "Shopee 3.3 Sale - Giảm đến 50% toàn sàn",
     "🛒 SHOPEE 3.3 MEGA SALE\nGiảm đến 50% hàng triệu sản phẩm\nVoucher freeship đơn từ 0đ\nFlash sale 99K mỗi ngày\nTải app ngay! 📱",
     "SHOP_NOW", "Thương mại điện tử", "Marketplace", "all",
     (8000, 30000), (500, 3000), (300, 1500)),
    ("google", "image", "Lazada VN", "adv_lazada_g",
     "Lazada - Mua sắm thả ga, freeship mọi đơn",
     "Lazada LazMall - Chính hãng 100%\n🎁 Mã giảm 100K cho đơn đầu tiên\n🚚 Freeship không giới hạn\nTải app ngay để nhận ưu đãi!",
     "DOWNLOAD", "Thương mại điện tử", "Marketplace", "all",
     (5000, 18000), (300, 1500), (150, 800)),
    ("google", "image", "Tiki", "adv_tiki_g",
     "Tiki - Giao nhanh 2h, đổi trả 30 ngày",
     "📦 TikiNOW - Giao nhanh 2 giờ\nSản phẩm chính hãng, đổi trả 30 ngày\nThanh toán sau với Mua Trước Trả Sau\n🎉 Giảm 50K cho đơn đầu tiên",
     "SHOP_NOW", "Thương mại điện tử", "Marketplace", "all",
     (3000, 10000), (200, 1000), (100, 500)),
    ("google", "image", "FPT Shop", "adv_fptshop_g",
     "iPhone 16 giá tốt nhất - Trả góp 0%",
     "📱 iPhone 16 chính hãng Apple\nGiá tốt nhất thị trường\nTrả góp 0% qua mọi ngân hàng\nThu cũ đổi mới - Giảm thêm 2 triệu",
     "LEARN_MORE", "Công nghệ", "Điện thoại", "all",
     (4000, 15000), (300, 2000), (150, 800)),
    ("google", "image", "Thế Giới Di Động", "adv_tgdd_g",
     "Laptop học tập & văn phòng từ 8.990K",
     "💻 Laptop giá rẻ cho sinh viên\nASUS, Acer, Lenovo từ 8.990.000đ\nTặng chuột + balo + Office 365\nBảo hành 24 tháng chính hãng",
     "SHOP_NOW", "Công nghệ", "Phụ kiện", "all",
     (2000, 8000), (150, 800), (80, 400)),
    ("google", "image", "Vinpearl", "adv_vinpearl_g",
     "Nghỉ dưỡng Phú Quốc 5 sao - Giảm 40%",
     "🏖️ Vinpearl Resort Phú Quốc\nPhòng view biển 5 sao\nGiảm 40% đặt sớm mùa hè 2026\nBao gồm buffet sáng + spa\nĐặt ngay trên Vinpearl.com",
     "LEARN_MORE", "Du lịch", "Resort", "all",
     (3000, 12000), (200, 1500), (100, 700)),
    ("google", "image", "MoMo", "adv_momo_g",
     "Ví MoMo - Thanh toán mọi nơi, hoàn tiền 50%",
     "💳 Ví MoMo - Thanh toán không tiền mặt\nHoàn đến 50% khi thanh toán hóa đơn\nNạp tiền, chuyển khoản miễn phí\n🎁 Tải app: Nhận ngay 50K",
     "DOWNLOAD", "Tài chính", "Ví điện tử", "all",
     (5000, 20000), (400, 2000), (200, 1000)),
    ("google", "image", "VNExpress", "adv_vnexpress_g",
     "Tin tức nóng nhất - Cập nhật 24/7",
     "📰 VnExpress - Báo tiếng Việt nhiều người đọc nhất\nTin tức, kinh doanh, thể thao, giải trí\nCập nhật 24/7, nhanh & chính xác\nTải app đọc báo miễn phí!",
     "DOWNLOAD", "Truyền thông", "Tin tức", "all",
     (2000, 7000), (100, 600), (50, 300)),
    ("google", "image", "Be (ride-hailing)", "adv_be_g",
     "Be - Gọi xe siêu nhanh, giá siêu rẻ",
     "🚗 Ứng dụng gọi xe Be\nGiá rẻ hơn, phục vụ tốt hơn\n🎁 Mã BECHAO giảm 50% chuyến đầu\nXe máy, ô tô, giao hàng - Có hết!",
     "DOWNLOAD", "Vận tải", "Ride-hailing", "all",
     (4000, 15000), (300, 1500), (150, 800)),
    ("google", "image", "Grab VN", "adv_grab_g",
     "GrabFood - Đặt đồ ăn giảm 30%, freeship",
     "🍔 GrabFood - Đặt đồ ăn online\nGiảm 30% đơn đầu tiên\nFreeship trong bán kính 3km\n⏰ Giao nhanh 30 phút\nMã: GRABMOI giảm thêm 20K",
     "ORDER_NOW", "F&B", "Delivery", "all",
     (6000, 22000), (400, 2500), (200, 1200)),
]

# ---------------------------------------------------------------------------
# TikTok Shops
# ---------------------------------------------------------------------------
SHOPS_DATA = [
    {
        "shop_id": "tt_shop_laneige",
        "shop_name": "Laneige Official VN",
        "category": "Làm đẹp",
        "followers": 125000,
        "rating": 4.8,
        "is_verified": True,
        "products": [
            ("Water Sleeping Mask 70ml", 520000, 750000, 45000, 4.9),
            ("Lip Sleeping Mask Berry 20g", 380000, 520000, 38000, 4.8),
            ("Neo Cushion Glow SPF46", 890000, 1200000, 12000, 4.7),
            ("Cream Skin Toner & Moisturizer", 650000, 850000, 22000, 4.8),
            ("Water Bank Blue Hyaluronic Serum", 780000, 1050000, 15000, 4.7),
            ("Radian-C Cream 30ml", 920000, None, 8000, 4.6),
            ("Bouncy & Firm Sleeping Mask", 580000, 780000, 11000, 4.7),
            ("Lip Glowy Balm Berry", 280000, 350000, 30000, 4.9),
            ("Perfect Renew 3X Cream", 1150000, None, 5000, 4.5),
            ("Fresh Calming Toner 250ml", 450000, 620000, 18000, 4.8),
        ],
    },
    {
        "shop_id": "tt_shop_yody",
        "shop_name": "YODY Fashion",
        "category": "Thời trang",
        "followers": 89000,
        "rating": 4.6,
        "is_verified": True,
        "products": [
            ("Áo Polo Nam Cotton Cao Cấp", 259000, 399000, 35000, 4.7),
            ("Đầm Công Sở Nữ Thanh Lịch", 359000, 520000, 22000, 4.6),
            ("Áo Thun Unisex Oversize", 179000, 250000, 50000, 4.8),
            ("Quần Short Nam Kaki", 229000, 320000, 28000, 4.5),
            ("Áo Sơ Mi Nữ Tay Dài", 299000, 420000, 18000, 4.6),
            ("Quần Jeans Nữ Ống Rộng", 349000, 480000, 15000, 4.5),
            ("Áo Khoác Gió Unisex", 399000, 550000, 20000, 4.7),
            ("Váy Liền Hoa Nhí", 319000, 450000, 12000, 4.6),
        ],
    },
    {
        "shop_id": "tt_shop_samsung",
        "shop_name": "Samsung Flagship",
        "category": "Công nghệ",
        "followers": 200000,
        "rating": 4.9,
        "is_verified": True,
        "products": [
            ("Galaxy S26 Ultra 256GB", 29990000, 33990000, 5000, 4.9),
            ("Galaxy Tab S10 FE", 7990000, 9990000, 8000, 4.8),
            ("Galaxy Buds3 Pro", 4990000, 5990000, 15000, 4.7),
            ("Galaxy Watch7 44mm", 6990000, 8490000, 10000, 4.8),
            ("Galaxy A55 5G 128GB", 8990000, 10990000, 20000, 4.6),
            ("Sạc nhanh 45W chính hãng", 590000, 790000, 30000, 4.7),
            ("Ốp lưng Galaxy S26 Ultra", 390000, 550000, 25000, 4.5),
            ("Galaxy Fit3 vòng tay", 1290000, 1590000, 12000, 4.6),
            ("Dây sạc USB-C chính hãng", 190000, 290000, 40000, 4.8),
            ("Galaxy S26+ 256GB", 25990000, 28990000, 3000, 4.9),
        ],
    },
    {
        "shop_id": "tt_shop_vinamilk",
        "shop_name": "Vinamilk Online",
        "category": "Thực phẩm",
        "followers": 156000,
        "rating": 4.7,
        "is_verified": True,
        "products": [
            ("Sữa tươi Organic 1L (lốc 4)", 135000, 160000, 42000, 4.8),
            ("Sữa chua Vinamilk không đường (lốc 4)", 32000, 38000, 65000, 4.7),
            ("Sữa đặc Ông Thọ 380g", 25000, None, 80000, 4.9),
            ("Sữa tươi Flex 1L (lốc 4)", 85000, 105000, 35000, 4.6),
            ("Phô mai Con Bò Cười 8 miếng", 35000, 42000, 55000, 4.7),
            ("Sữa bột Dielac Grow 1.5kg", 350000, 420000, 15000, 4.6),
            ("Nước ép trái cây VFresh 1L", 28000, 35000, 38000, 4.5),
            ("Sữa hạt óc chó Vinamilk 180ml (lốc 4)", 45000, 55000, 25000, 4.6),
            ("Kem Vinamilk hộp 450ml", 55000, 68000, 30000, 4.8),
            ("Sữa tươi Vinamilk 100% 180ml (thùng 48)", 285000, 340000, 20000, 4.7),
        ],
    },
    {
        "shop_id": "tt_shop_ankhang",
        "shop_name": "Nhà Thuốc An Khang",
        "category": "Sức khỏe",
        "followers": 45000,
        "rating": 4.5,
        "is_verified": False,
        "products": [
            ("Vitamin C DHC 1000mg 30 ngày", 99000, 150000, 25000, 4.7),
            ("Dầu cá Omega-3 Blackmores 200v", 450000, 580000, 12000, 4.6),
            ("Collagen dạng nước 10 ống", 320000, 450000, 18000, 4.5),
            ("Vitamin tổng hợp Centrum 100v", 550000, 680000, 8000, 4.7),
            ("Nước súc miệng Listerine 750ml", 85000, 110000, 30000, 4.6),
            ("Kem chống nắng Skin Aqua SPF50", 165000, 220000, 20000, 4.5),
            ("Dung dịch rửa tay Lifebuoy 500ml", 55000, 72000, 35000, 4.8),
            ("Băng vệ sinh Diana Sensi 20m", 38000, 45000, 45000, 4.6),
        ],
    },
]

# ---------------------------------------------------------------------------
# Advertiser Groups
# ---------------------------------------------------------------------------
ADVERTISER_GROUPS_DATA = [
    ("Laneige Vietnam", "laneige-vietnam", {"meta": "adv_laneige_m", "tiktok": "adv_laneige_t"}, ["Làm đẹp", "Skincare"], True),
    ("Innisfree Vietnam", "innisfree-vietnam", {"meta": "adv_innisfree_m", "tiktok": "adv_innisfree_t"}, ["Làm đẹp", "Skincare"], True),
    ("3CE Vietnam", "3ce-vietnam", {"meta": "adv_3ce_m", "tiktok": "adv_3ce_t"}, ["Làm đẹp", "Makeup"], True),
    ("YODY Fashion", "yody-fashion", {"meta": "adv_yody_m", "tiktok": "adv_yody_t"}, ["Thời trang"], True),
    ("Samsung Vietnam", "samsung-vietnam", {"meta": "adv_samsung_m", "tiktok": "adv_samsung_t", "google": "adv_samsung_g"}, ["Công nghệ", "Điện thoại"], True),
    ("Vinamilk", "vinamilk", {"meta": "adv_vinamilk_m"}, ["F&B", "Thực phẩm"], True),
    ("Highlands Coffee", "highlands-coffee", {"meta": "adv_highlands_m"}, ["F&B", "Đồ uống"], True),
    ("The Coffee House", "the-coffee-house", {"tiktok": "adv_coffeehouse_t"}, ["F&B", "Đồ uống"], False),
    ("DHC Vietnam", "dhc-vietnam", {"meta": "adv_dhc_m"}, ["Sức khỏe", "Thực phẩm chức năng"], True),
    ("Vinhomes", "vinhomes", {"meta": "adv_vinhomes_m", "google": "adv_vinhomes_g"}, ["Bất động sản"], True),
]

# ---------------------------------------------------------------------------
# Offers & Triggers pools
# ---------------------------------------------------------------------------
OFFERS_POOL = [
    "Giảm 30%", "Giảm 40%", "Giảm 50%", "Mua 1 tặng 1", "Free ship",
    "Flash Sale", "Combo tiết kiệm", "Trả góp 0%", "Tặng quà", "Voucher 100K",
]
TRIGGERS_POOL = [
    "FOMO", "Social proof", "Scarcity", "Authority", "Urgency",
    "Loss aversion", "Bandwagon", "Reciprocity",
]
AUDIENCES = [
    "Nữ 18-25 quan tâm skincare Hàn Quốc",
    "Nữ 25-35 quan tâm thời trang công sở",
    "Nam 20-30 quan tâm công nghệ & gaming",
    "Nữ 18-30 quan tâm makeup & beauty",
    "Nam 25-40 quan tâm thời trang nam",
    "All 18-35 quan tâm F&B & ẩm thực",
    "All 22-35 quan tâm giáo dục & phát triển bản thân",
    "All 25-45 quan tâm sức khỏe & wellness",
    "All 25-50 quan tâm bất động sản & đầu tư",
    "All 18-30 quan tâm mua sắm online",
]
DOMINANT_COLORS_POOL = [
    ["#FF5733", "#FFFFFF", "#333333"],
    ["#E91E63", "#FCE4EC", "#FFFFFF"],
    ["#3498DB", "#2ECC71", "#FFFFFF"],
    ["#FF9800", "#FFF3E0", "#333333"],
    ["#9C27B0", "#F3E5F5", "#FFFFFF"],
    ["#000000", "#FFFFFF", "#FF0000"],
    ["#1976D2", "#BBDEFB", "#FFFFFF"],
    ["#4CAF50", "#E8F5E9", "#333333"],
]
PLATFORMS_LANDING = ["shopee", "lazada", "haravan", "custom", "tiktok_shop", None]


def create_sample_ads() -> tuple[list, list[dict]]:
    """Create 50 Ad objects + ES docs."""
    random.seed(42)
    ads = []
    es_docs = []

    for i, tmpl in enumerate(AD_TEMPLATES):
        (platform, ad_type, advertiser_name, advertiser_id, headline, body_text,
         cta_type, cat_l1, cat_l2, target_gender,
         likes_range, comments_range, shares_range) = tmpl

        ad_id = uuid.uuid4()
        first_seen = NOW - timedelta(days=random.randint(3, 30))
        last_seen = first_seen + timedelta(days=random.randint(1, (NOW - first_seen).days or 1))
        if last_seen > NOW:
            last_seen = NOW
        is_active = random.random() < 0.7
        likes = random.randint(*likes_range)
        comments = random.randint(*comments_range)
        shares = random.randint(*shares_range)
        days_running = max(1, (last_seen - first_seen).days)

        daily_spend = round(random.uniform(50, 2000), 2)
        total_spend = round(daily_spend * days_running, 2)
        cpm = round(random.uniform(3.0, 15.0), 2)
        engagement = round(random.uniform(0.01, 0.15), 4)
        viral = round(random.uniform(10, 95), 1)
        is_hot = viral > 70

        detected_offers = random.sample(OFFERS_POOL, k=random.randint(0, 3))
        emotional_triggers = random.sample(TRIGGERS_POOL, k=random.randint(0, 3))
        target_audience = random.choice(AUDIENCES)
        dominant_colors = random.choice(DOMINANT_COLORS_POOL)

        seed_str = f"{platform}_{i:03d}"
        thumbnail_url = f"https://picsum.photos/seed/{seed_str}/640/360"

        is_video = ad_type == "video"
        creative_h = 1920 if is_video else 1080

        ad = Ad(
            id=ad_id,
            platform=platform,
            platform_ad_id=f"{platform}_seed_{i:03d}",
            advertiser_name=advertiser_name,
            advertiser_id=advertiser_id,
            ad_type=ad_type,
            headline=headline,
            body_text=body_text,
            cta_type=cta_type,
            thumbnail_url=thumbnail_url,
            landing_page_url=f"https://{advertiser_name.lower().replace(' ', '-')}.vn/product",
            target_countries=["VN"],
            target_age_min=random.choice([18, 20, 22, 25]),
            target_age_max=random.choice([35, 40, 45, 55]),
            target_gender=target_gender,
            likes=likes,
            comments=comments,
            shares=shares,
            category=cat_l1,
            category_l1=cat_l1,
            category_l2=cat_l2,
            detected_offers=detected_offers,
            emotional_triggers=emotional_triggers,
            target_audience_guess=target_audience,
            estimated_daily_spend=daily_spend,
            estimated_total_spend=total_spend,
            cpm_estimate=cpm,
            engagement_rate=engagement,
            viral_score=viral,
            is_hot=is_hot,
            creative_width=1080,
            creative_height=creative_h,
            creative_format="mp4" if is_video else "jpg",
            has_text_overlay=random.random() < 0.6,
            dominant_colors=dominant_colors,
            language="vi",
            is_active=is_active,
            first_seen=first_seen,
            last_seen=last_seen,
        )
        ads.append(ad)

        es_docs.append({
            "id": str(ad_id),
            "platform": platform,
            "platform_ad_id": ad.platform_ad_id,
            "advertiser_name": advertiser_name,
            "advertiser_id": advertiser_id,
            "ad_type": ad_type,
            "headline": headline,
            "body_text": body_text,
            "cta_type": cta_type,
            "thumbnail_url": thumbnail_url,
            "landing_page_url": ad.landing_page_url,
            "target_countries": ["VN"],
            "target_age_min": ad.target_age_min,
            "target_age_max": ad.target_age_max,
            "target_gender": target_gender,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "category": cat_l1,
            "category_l1": cat_l1,
            "category_l2": cat_l2,
            "detected_offers": detected_offers,
            "emotional_triggers": emotional_triggers,
            "target_audience_guess": target_audience,
            "estimated_daily_spend": daily_spend,
            "estimated_total_spend": total_spend,
            "cpm_estimate": cpm,
            "engagement_rate": engagement,
            "viral_score": viral,
            "is_hot": is_hot,
            "language": "vi",
            "is_active": is_active,
            "first_seen": first_seen.isoformat(),
            "last_seen": last_seen.isoformat(),
            "created_at": NOW.isoformat(),
        })

    return ads, es_docs


def create_sample_shops() -> list:
    """Create 5 TikTokShop with ~50 products."""
    random.seed(123)
    shops = []

    for shop_data in SHOPS_DATA:
        shop = TikTokShop(
            shop_id=shop_data["shop_id"],
            shop_name=shop_data["shop_name"],
            shop_url=f"https://www.tiktok.com/@{shop_data['shop_id']}",
            followers=shop_data["followers"],
            rating=shop_data["rating"],
            total_products=len(shop_data["products"]),
            total_sales=sum(p[3] for p in shop_data["products"]),
            category=shop_data["category"],
            is_verified=shop_data["is_verified"],
        )

        for j, (name, price, orig_price, sales, rating) in enumerate(shop_data["products"]):
            daily_avg = sales // 30
            daily_sales = {}
            for d in range(7):
                day = (NOW - timedelta(days=d)).strftime("%Y-%m-%d")
                daily_sales[day] = max(1, daily_avg + random.randint(-daily_avg // 3, daily_avg // 3))

            product = TikTokShopProduct(
                product_id=f"tt_prod_{shop_data['shop_id']}_{j:02d}",
                product_name=name,
                product_url=f"https://www.tiktok.com/product/{shop_data['shop_id']}_{j:02d}",
                price=price,
                original_price=orig_price,
                currency="VND",
                sales_count=sales,
                review_count=random.randint(sales // 20, sales // 5),
                rating=rating,
                category=shop_data["category"],
                images=[f"https://picsum.photos/seed/prod_{shop_data['shop_id']}_{j}/400/400"],
                is_active=True,
                daily_sales=daily_sales,
                estimated_daily_revenue=round(price * daily_avg, 2),
                estimated_monthly_revenue=round(price * daily_avg * 30, 2),
            )
            shop.products.append(product)

        shops.append(shop)

    return shops


def create_advertiser_groups(ads: list) -> list:
    """Create 10 cross-platform advertiser groups."""
    # Build lookup: advertiser_id -> list of ads
    adv_ads: dict[str, list] = {}
    for ad in ads:
        if ad.advertiser_id:
            adv_ads.setdefault(ad.advertiser_id, []).append(ad)

    groups = []
    for name, slug, platform_ids, categories, is_verified in ADVERTISER_GROUPS_DATA:
        total_ads = 0
        total_spend = 0.0
        for adv_id in platform_ids.values():
            for ad in adv_ads.get(adv_id, []):
                total_ads += 1
                total_spend += ad.estimated_total_spend or 0

        group = AdvertiserGroup(
            name=name,
            slug=slug,
            platform_ids=platform_ids,
            total_ads=max(total_ads, random.randint(5, 25)),
            total_estimated_spend=round(total_spend if total_spend > 0 else random.uniform(5000, 50000), 2),
            categories=categories,
            is_verified=is_verified,
        )
        groups.append(group)

    return groups


def create_landing_pages(ads: list) -> list:
    """Create landing page info for first 20 ads."""
    random.seed(456)
    pages = []

    for ad in ads[:20]:
        brand_domain = ad.advertiser_name.lower().replace(" ", "-") + ".vn"
        final_url = f"https://{brand_domain}/san-pham"
        platform_detected = random.choice(PLATFORMS_LANDING)

        page = LandingPageInfo(
            ad_id=ad.id,
            final_url=final_url,
            redirect_chain=[
                f"https://l.facebook.com/l.php?u={final_url}" if ad.platform == "meta" else f"https://www.tiktok.com/redirect?url={final_url}",
                final_url,
            ],
            platform_detected=platform_detected,
            product_name=ad.headline,
            product_price=random.uniform(100000, 5000000),
            product_currency="VND",
            has_fb_pixel=ad.platform == "meta" or random.random() < 0.3,
            has_tiktok_pixel=ad.platform == "tiktok" or random.random() < 0.2,
            has_google_analytics=random.random() < 0.7,
            has_chat_widget="zalo" if random.random() < 0.5 else None,
            has_ssl=True,
            page_load_ms=random.randint(800, 3000),
            crawl_status="success",
            crawled_at=NOW,
        )
        pages.append(page)

    return pages


async def seed_users(db) -> int:
    """Seed test users. Returns count created."""
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


async def main():
    print("=== AdSight Seed Data ===\n")

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 1. Users
    print("[1/5] Seeding users...")
    async with async_session() as db:
        user_count = await seed_users(db)
        await db.commit()
    print(f"  Users done: {user_count} created\n")

    # 2. Check if already seeded
    async with async_session() as db:
        count = (await db.execute(select(func.count()).select_from(Ad))).scalar()
        if count and count > 0:
            print(f"Database already has {count} ads. Skipping seed.")
            print("To re-seed, truncate tables first.\n")
            print("=== Seed complete (skipped) ===")
            return

    # 3. Ads
    print("[2/5] Seeding 50 ads into PostgreSQL...")
    ads, es_docs = create_sample_ads()
    async with async_session() as db:
        db.add_all(ads)
        await db.flush()

        # 4. Landing pages (needs ad.id)
        print("[3/5] Seeding 20 landing pages...")
        landing_pages = create_landing_pages(ads)
        db.add_all(landing_pages)

        # 5. Advertiser groups
        print("[4/5] Seeding 10 advertiser groups...")
        groups = create_advertiser_groups(ads)
        db.add_all(groups)

        await db.commit()

    print(f"  Created: {len(ads)} ads, {len(landing_pages)} landing pages, {len(groups)} groups\n")

    # 6. TikTok Shops (separate session)
    print("[5/5] Seeding TikTok shops + products...")
    shops = create_sample_shops()
    total_products = sum(len(s.products) for s in shops)
    async with async_session() as db:
        db.add_all(shops)
        await db.commit()
    print(f"  Created: {len(shops)} shops, {total_products} products\n")

    # 7. Elasticsearch indexing
    print("[ES] Indexing ads into Elasticsearch...")
    if es_docs:
        try:
            await es_client.initialize()
            es = es_client.client
            await bulk_index_ads(es, es_docs)
            await es_client.close()
            print(f"  Indexed {len(es_docs)} ads into Elasticsearch\n")
        except Exception as e:
            print(f"  WARNING: Elasticsearch not available ({e})")
            print("  Ads saved to PostgreSQL but not indexed.\n")

    print("=== Seed complete ===")
    print(f"  50 ads | 5 shops | {total_products} products | 10 groups | 20 landing pages")


if __name__ == "__main__":
    asyncio.run(main())
