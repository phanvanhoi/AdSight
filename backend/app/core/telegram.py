"""Telegram Bot API utilities."""
import httpx

from app.config import settings

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


async def send_telegram_message(chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    """Send message via Telegram Bot API."""
    if not settings.telegram_bot_token:
        print("Telegram bot not configured")
        return False

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                },
                timeout=10,
            )
            return resp.status_code == 200
    except Exception as e:
        print(f"Telegram send failed: {e}")
        return False


def build_alert_message(alert_name: str, match_value: str, ad_count: int, ads_preview: list[dict]) -> str:
    """Build Telegram message for competitor alert."""
    lines = [
        f"\U0001f514 <b>{alert_name}</b>",
        f'Ph\u00e1t hi\u1ec7n <b>{ad_count}</b> qu\u1ea3ng c\u00e1o m\u1edbi t\u1eeb "{match_value}"',
        "",
    ]

    for ad in ads_preview[:5]:
        headline = ad.get("headline", "N/A")[:60]
        platform = ad.get("platform", "").upper()
        lines.append(f"\u2022 <i>{platform}</i> \u2014 {headline}")

    if ad_count > 5:
        lines.append(f"\n...v\u00e0 {ad_count - 5} ads kh\u00e1c")

    lines.append('\n\U0001f449 <a href="https://app.adsight.vn/alerts">Xem chi ti\u1ebft</a>')

    return "\n".join(lines)
