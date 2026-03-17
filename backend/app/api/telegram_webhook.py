"""Telegram Bot webhook — receives messages from Telegram."""
import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.telegram import send_telegram_message
from app.models.user import User

router = APIRouter()


@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Process incoming Telegram messages."""
    data = await request.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = str(message.get("chat", {}).get("id", ""))

    if not chat_id:
        return {"ok": True}

    # Handle /start {token} command
    if text.startswith("/start "):
        token = text.split(" ", 1)[1].strip()
        await _handle_start(token, chat_id, db)

    elif text == "/start":
        await send_telegram_message(
            chat_id,
            "\U0001f44b Ch\u00e0o b\u1ea1n! \u0110\u1ec3 k\u1ebft n\u1ed1i v\u1edbi AdSight, h\u00e3y v\u00e0o Settings tr\u00ean web v\u00e0 b\u1ea5m \"K\u1ebft n\u1ed1i Telegram\".",
        )

    elif text == "/status":
        user = (
            await db.execute(select(User).where(User.telegram_chat_id == chat_id))
        ).scalar_one_or_none()
        if user:
            await send_telegram_message(
                chat_id,
                f"\u2705 \u0110\u00e3 k\u1ebft n\u1ed1i v\u1edbi <b>{user.email}</b> (g\u00f3i {user.tier.capitalize()})",
            )
        else:
            await send_telegram_message(
                chat_id,
                "\u274c Ch\u01b0a k\u1ebft n\u1ed1i. V\u00e0o Settings tr\u00ean web \u0111\u1ec3 k\u1ebft n\u1ed1i.",
            )

    elif text == "/stop":
        user = (
            await db.execute(select(User).where(User.telegram_chat_id == chat_id))
        ).scalar_one_or_none()
        if user:
            user.telegram_chat_id = None
            user.telegram_enabled = False
            await db.commit()
            await send_telegram_message(
                chat_id,
                "\U0001f515 \u0110\u00e3 ng\u1eaft k\u1ebft n\u1ed1i. B\u1ea1n s\u1ebd kh\u00f4ng nh\u1eadn th\u00f4ng b\u00e1o n\u1eefa.",
            )
        else:
            await send_telegram_message(
                chat_id,
                "B\u1ea1n ch\u01b0a k\u1ebft n\u1ed1i v\u1edbi t\u00e0i kho\u1ea3n n\u00e0o.",
            )

    return {"ok": True}


async def _handle_start(token: str, chat_id: str, db: AsyncSession):
    """Handle /start {token} — link Telegram chat to user."""
    from app.api.auth import _telegram_tokens

    token_data = _telegram_tokens.get(token)
    if not token_data:
        await send_telegram_message(
            chat_id,
            "\u274c Token kh\u00f4ng h\u1ee3p l\u1ec7 ho\u1eb7c \u0111\u00e3 h\u1ebft h\u1ea1n. Th\u1eed l\u1ea1i t\u1eeb Settings.",
        )
        return

    user_id, expire_ts = token_data
    if time.time() > expire_ts:
        del _telegram_tokens[token]
        await send_telegram_message(
            chat_id,
            "\u274c Token \u0111\u00e3 h\u1ebft h\u1ea1n. Th\u1eed l\u1ea1i t\u1eeb Settings.",
        )
        return

    # Link chat_id to user
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        await send_telegram_message(chat_id, "\u274c User kh\u00f4ng t\u1ed3n t\u1ea1i.")
        return

    user.telegram_chat_id = chat_id
    user.telegram_enabled = True
    await db.commit()

    # Cleanup token
    del _telegram_tokens[token]

    await send_telegram_message(
        chat_id,
        f"\u2705 K\u1ebft n\u1ed1i th\u00e0nh c\u00f4ng! B\u1ea1n s\u1ebd nh\u1eadn th\u00f4ng b\u00e1o competitor alerts cho <b>{user.email}</b>.\n\n"
        f"G\u00f5 /stop \u0111\u1ec3 ng\u1eaft k\u1ebft n\u1ed1i.\nG\u00f5 /status \u0111\u1ec3 ki\u1ec3m tra.",
    )
