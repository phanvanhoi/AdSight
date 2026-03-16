"""
Vietnamese Auto-Categorizer — rule-based NLP for ad classification.

Detects:
- L1/L2 product categories (11 top-level, subcategories)
- Offer patterns (discount, freeship, bundle, urgency, social_proof)
- Emotional triggers (fear, desire, trust, fomo)
- Target audience guess (heuristic from category)
"""

import re
import unicodedata

# ---------------------------------------------------------------------------
# Category taxonomy (L1 → L2)
# ---------------------------------------------------------------------------
CATEGORY_RULES: dict[str, dict] = {
    "Mỹ phẩm": {
        "keywords": [
            "kem", "serum", "son", "mỹ phẩm", "skincare", "makeup", "trang điểm",
            "dưỡng da", "chống nắng", "kcn", "toner", "sữa rửa mặt", "mặt nạ",
            "collagen", "retinol", "niacinamide", "vitamin c", "kem nền", "phấn",
        ],
        "subcategories": {
            "Kem chống nắng": ["chống nắng", "kcn", "spf", "sunscreen", "uv"],
            "Serum/Tinh chất": ["serum", "tinh chất", "essence", "ampoule"],
            "Son môi": ["son", "lipstick", "lip"],
            "Kem nền/Trang điểm": ["kem nền", "foundation", "phấn", "makeup", "trang điểm"],
            "Chăm sóc da": ["dưỡng da", "skincare", "toner", "sữa rửa mặt", "mặt nạ", "kem dưỡng"],
        },
    },
    "Thời trang": {
        "keywords": [
            "áo", "quần", "váy", "đầm", "giày", "dép", "túi", "balo",
            "thời trang", "fashion", "hoodie", "jacket", "sneaker", "sandal",
            "đồng hồ", "kính", "phụ kiện",
        ],
        "subcategories": {
            "Áo": ["áo thun", "áo phông", "áo sơ mi", "áo khoác", "hoodie", "jacket"],
            "Quần": ["quần jean", "quần short", "quần dài", "jogger"],
            "Giày dép": ["giày", "dép", "sneaker", "sandal", "boot"],
            "Túi xách/Balo": ["túi", "balo", "bag", "clutch"],
            "Phụ kiện": ["đồng hồ", "kính", "vòng", "nhẫn", "dây chuyền"],
        },
    },
    "Công nghệ": {
        "keywords": [
            "iphone", "samsung", "laptop", "điện thoại", "smartphone", "tablet",
            "tai nghe", "sạc", "ốp lưng", "camera", "máy tính", "pc", "gaming",
        ],
        "subcategories": {
            "Điện thoại": ["iphone", "samsung", "oppo", "xiaomi", "điện thoại", "smartphone"],
            "Laptop/PC": ["laptop", "máy tính", "pc", "gaming", "notebook"],
            "Phụ kiện": ["tai nghe", "sạc", "ốp lưng", "cáp", "adapter", "pin"],
        },
    },
    "F&B": {
        "keywords": [
            "đồ ăn", "thức ăn", "nhà hàng", "quán", "trà sữa", "cafe",
            "gà rán", "pizza", "bánh", "snack", "khô", "food", "drink",
        ],
        "subcategories": {
            "Đồ ăn vặt": ["snack", "khô", "bánh", "kẹo"],
            "Đồ uống": ["trà sữa", "cafe", "nước", "sữa", "sinh tố"],
            "Nhà hàng": ["nhà hàng", "quán", "buffet", "gà rán", "pizza"],
        },
    },
    "Giáo dục": {
        "keywords": [
            "khóa học", "học", "ielts", "toeic", "lập trình", "tiếng anh", "đào tạo",
        ],
        "subcategories": {
            "Ngoại ngữ": ["ielts", "toeic", "tiếng anh", "tiếng hàn", "tiếng nhật"],
            "IT/Lập trình": ["lập trình", "python", "java", "web", "data", "code"],
            "Kỹ năng": ["marketing", "kinh doanh", "bán hàng", "quản lý"],
        },
    },
    "Bất động sản": {
        "keywords": ["nhà", "đất", "chung cư", "biệt thự", "căn hộ", "bds"],
        "subcategories": {},
    },
    "Sức khỏe": {
        "keywords": [
            "gym", "fitness", "yoga", "thực phẩm chức năng", "vitamin", "giảm cân", "sức khỏe",
        ],
        "subcategories": {
            "Fitness": ["gym", "fitness", "yoga", "tập"],
            "TPCN": ["thực phẩm chức năng", "vitamin", "bổ sung"],
            "Giảm cân": ["giảm cân", "diet", "giảm mỡ"],
        },
    },
    "Du lịch": {
        "keywords": ["tour", "du lịch", "travel", "khách sạn", "resort", "vé máy bay"],
        "subcategories": {},
    },
    "Xe cộ": {
        "keywords": ["xe máy", "ô tô", "honda", "yamaha", "toyota", "vinfast"],
        "subcategories": {},
    },
    "Mẹ & Bé": {
        "keywords": ["bỉm", "sữa bột", "đồ chơi", "em bé", "mẹ bầu", "baby", "tã"],
        "subcategories": {},
    },
    "Nội thất": {
        "keywords": ["nội thất", "decor", "bàn", "ghế", "giường", "tủ", "đèn", "rèm"],
        "subcategories": {},
    },
    "TMĐT": {
        "keywords": ["shopee", "lazada", "tiki", "flash sale", "siêu sale", "11.11", "12.12"],
        "subcategories": {},
    },
}

# ---------------------------------------------------------------------------
# Offer detection patterns
# ---------------------------------------------------------------------------
OFFER_PATTERNS: dict[str, list[str]] = {
    "discount": [
        r"giảm\s*(\d+)\s*%",
        r"sale\s*(\d+)\s*%",
        r"chỉ\s*(?:còn\s*)?(\d+\.?\d*)\s*[kK]",
    ],
    "freeship": [
        r"free\s*ship",
        r"miễn\s*phí\s*(?:vận\s*chuyển|ship|giao\s*hàng)",
    ],
    "bundle": [
        r"mua\s*(\d+)\s*tặng\s*(\d+)",
        r"combo",
        r"set\s*\d+",
    ],
    "urgency": [
        r"chỉ\s*(?:hôm\s*nay|ngày\s*nay)",
        r"(?:\d+)\s*ngày\s*cuối",
        r"số\s*lượng\s*(?:có\s*hạn|giới\s*hạn)",
        r"flash\s*sale",
    ],
    "social_proof": [
        r"(\d+\.?\d*)\s*(?:đã\s*mua|đã\s*bán)",
        r"best\s*seller",
        r"bán\s*chạy",
    ],
}

# ---------------------------------------------------------------------------
# Emotional triggers
# ---------------------------------------------------------------------------
EMOTIONAL_TRIGGERS: dict[str, list[str]] = {
    "fear": [r"lão\s*hóa", r"da\s*xấu", r"mụn", r"nám", r"tụt\s*hậu"],
    "desire": [r"trắng\s*sáng", r"đẹp", r"xinh", r"sang\s*trọng", r"thành\s*công", r"chính\s*hãng"],
    "trust": [r"chính\s*hãng", r"cam\s*kết", r"bảo\s*hành", r"100%", r"nhập\s*khẩu"],
    "fomo": [r"sắp\s*hết", r"chỉ\s*còn\s*\d+", r"số\s*lượng\s*có\s*hạn"],
}

# ---------------------------------------------------------------------------
# Audience heuristics by L1 category
# ---------------------------------------------------------------------------
AUDIENCE_MAP: dict[str, str] = {
    "Mỹ phẩm": "Phụ nữ 18-35",
    "Thời trang": "Nam/Nữ 18-35",
    "Công nghệ": "Nam 18-40",
    "F&B": "Tất cả 18-45",
    "Giáo dục": "Sinh viên/Người đi làm 18-35",
    "Bất động sản": "Người đi làm 25-50",
    "Sức khỏe": "Nam/Nữ 25-45",
    "Du lịch": "Tất cả 22-45",
    "Xe cộ": "Nam 22-45",
    "Mẹ & Bé": "Phụ nữ 25-40",
    "Nội thất": "Gia đình 25-45",
    "TMĐT": "Tất cả 18-40",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_RE_FLAGS = re.IGNORECASE | re.UNICODE


def _normalize_text(text: str) -> str:
    """Lowercase, NFC normalize, collapse whitespace."""
    text = unicodedata.normalize("NFC", text)
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _remove_diacritics(text: str) -> str:
    """Remove Vietnamese diacritics for fallback matching."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _count_keyword_matches(text: str, keywords: list[str]) -> int:
    """Count how many keywords appear in text (with diacritic fallback)."""
    count = 0
    text_no_diacritics = _remove_diacritics(text)
    for kw in keywords:
        if kw in text:
            count += 1
        elif _remove_diacritics(kw) in text_no_diacritics:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------
def categorize_ad(headline: str | None, body_text: str | None) -> dict:
    """
    Categorize a Vietnamese ad based on headline + body text.

    Returns:
        {
            "category_l1": str | None,
            "category_l2": str | None,
            "detected_offers": dict,       # {"discount": [...], "freeship": [...], ...}
            "emotional_triggers": dict,     # {"fear": [...], "desire": [...], ...}
            "target_audience_guess": str | None,
        }
    """
    result = {
        "category_l1": None,
        "category_l2": None,
        "detected_offers": {},
        "emotional_triggers": {},
        "target_audience_guess": None,
    }

    if not headline and not body_text:
        return result

    combined = _normalize_text(f"{headline or ''} {body_text or ''}")

    # --- Category detection ---
    best_l1 = None
    best_score = 0

    for l1_name, rule in CATEGORY_RULES.items():
        score = _count_keyword_matches(combined, rule["keywords"])
        if score > best_score:
            best_score = score
            best_l1 = l1_name

    if best_l1:
        result["category_l1"] = best_l1
        result["target_audience_guess"] = AUDIENCE_MAP.get(best_l1)

        # Find best L2
        subcats = CATEGORY_RULES[best_l1].get("subcategories", {})
        best_l2 = None
        best_l2_score = 0
        for l2_name, l2_keywords in subcats.items():
            l2_score = _count_keyword_matches(combined, l2_keywords)
            if l2_score > best_l2_score:
                best_l2_score = l2_score
                best_l2 = l2_name
        if best_l2:
            result["category_l2"] = best_l2

    # --- Offer detection ---
    offers: dict[str, list[str]] = {}
    for offer_type, patterns in OFFER_PATTERNS.items():
        matches = []
        for pattern in patterns:
            for m in re.finditer(pattern, combined, _RE_FLAGS):
                matches.append(m.group(0))
        if matches:
            offers[offer_type] = matches
    result["detected_offers"] = offers

    # --- Emotional triggers ---
    triggers: dict[str, list[str]] = {}
    for trigger_type, patterns in EMOTIONAL_TRIGGERS.items():
        matches = []
        for pattern in patterns:
            for m in re.finditer(pattern, combined, _RE_FLAGS):
                matches.append(m.group(0))
        if matches:
            triggers[trigger_type] = matches
    result["emotional_triggers"] = triggers

    return result
