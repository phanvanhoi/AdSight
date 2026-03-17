import json
import re

import anthropic

from app.config import settings
from app.models.ad import Ad


async def analyze_ad_creative(ad: Ad) -> dict:
    """
    Gọi Claude API để phân tích creative của 1 ad.
    Returns structured analysis dict.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.claude_api_key)

    prompt = _build_analysis_prompt(ad)

    message = await client.messages.create(
        model=settings.claude_model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
        system="Bạn là chuyên gia phân tích quảng cáo digital tại thị trường Việt Nam và Đông Nam Á. "
               "Phân tích ad creative và trả về JSON. Luôn trả lời bằng tiếng Việt.",
    )

    response_text = message.content[0].text

    # Parse JSON response
    try:
        analysis = json.loads(response_text)
    except json.JSONDecodeError:
        # Tìm JSON trong markdown code block
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group(1))
        else:
            analysis = {"raw_response": response_text, "parse_error": True}

    return analysis


def _build_analysis_prompt(ad: Ad) -> str:
    """Build prompt for Claude API from ad data."""
    parts = [
        "Phân tích quảng cáo sau đây và trả về JSON với cấu trúc bên dưới.\n",
        "## Thông tin quảng cáo",
        f"- Platform: {ad.platform}",
        f"- Loại: {ad.ad_type}",
    ]

    if ad.headline:
        parts.append(f"- Headline: {ad.headline}")
    if ad.body_text:
        parts.append(f"- Nội dung: {ad.body_text}")
    if ad.cta_type:
        parts.append(f"- CTA: {ad.cta_type}")
    if ad.advertiser_name:
        parts.append(f"- Nhà quảng cáo: {ad.advertiser_name}")
    if ad.landing_page_url:
        parts.append(f"- Landing page: {ad.landing_page_url}")
    if ad.category_l1:
        parts.append(f"- Ngành: {ad.category_l1} > {ad.category_l2 or 'N/A'}")
    if ad.target_countries:
        countries = ', '.join(ad.target_countries) if isinstance(ad.target_countries, list) else str(ad.target_countries)
        parts.append(f"- Quốc gia: {countries}")

    # Metrics
    metrics = []
    if ad.likes:
        metrics.append(f"{ad.likes:,} likes")
    if ad.comments:
        metrics.append(f"{ad.comments:,} comments")
    if ad.shares:
        metrics.append(f"{ad.shares:,} shares")
    if ad.engagement_rate:
        metrics.append(f"engagement rate: {ad.engagement_rate:.2%}")
    if ad.viral_score:
        metrics.append(f"viral score: {ad.viral_score:.1f}")
    if metrics:
        parts.append(f"- Metrics: {', '.join(metrics)}")

    if ad.estimated_daily_spend:
        parts.append(f"- Chi tiêu ước tính: ${ad.estimated_daily_spend:.0f}/ngày")

    if ad.first_seen and ad.last_seen:
        days = (ad.last_seen - ad.first_seen).days
        parts.append(f"- Thời gian chạy: {days} ngày")

    parts.append("""
## Yêu cầu output JSON

Trả về JSON (không có markdown, chỉ JSON thuần) với cấu trúc:

{
    "summary": "Tóm tắt ngắn gọn về ad (2-3 câu)",
    "hook_analysis": {
        "hook_type": "loại hook (curiosity/fear/benefit/social_proof/urgency/other)",
        "hook_text": "phần hook chính trong ad",
        "effectiveness": 1-10,
        "explanation": "tại sao hook này hiệu quả/không hiệu quả"
    },
    "emotional_triggers": ["danh sách emotional triggers được sử dụng"],
    "target_audience": {
        "primary": "đối tượng chính",
        "demographics": "tuổi, giới tính, thu nhập",
        "psychographics": "sở thích, pain points, motivations"
    },
    "cta_analysis": {
        "cta_text": "text CTA",
        "cta_strength": 1-10,
        "suggestion": "gợi ý CTA tốt hơn nếu có"
    },
    "copy_analysis": {
        "tone": "giọng văn (casual/professional/urgent/friendly)",
        "readability": 1-10,
        "key_benefits": ["benefit 1", "benefit 2"],
        "power_words": ["từ mạnh được sử dụng"]
    },
    "strengths": ["điểm mạnh 1", "điểm mạnh 2"],
    "weaknesses": ["điểm yếu 1", "điểm yếu 2"],
    "suggestions": ["gợi ý cải thiện 1", "gợi ý cải thiện 2"],
    "performance_prediction": {
        "score": 1-10,
        "reasoning": "lý do dự đoán"
    },
    "similar_angle_ideas": ["ý tưởng angle tương tự 1", "ý tưởng 2"]
}""")

    return "\n".join(parts)
