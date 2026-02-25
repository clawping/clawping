"""Telegram notification channel via python-telegram-bot."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def send_telegram(chat_id: str, message: str, title: str | None = None) -> bool:
    """
    Send a message to a Telegram chat via the Bot API.

    Args:
        chat_id: Target Telegram chat ID.
        message: Notification body text.
        title:   Optional bold title prepended to the message.

    Returns:
        True if delivery succeeded, False otherwise.
    """
    if not settings.telegram_bot_token:
        logger.warning("Telegram bot token not configured — skipping delivery")
        return False

    text = f"*{title}*\n\n{message}" if title else message

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info("Telegram message sent to chat_id=%s", chat_id)
            return True
    except httpx.HTTPStatusError as e:
        logger.error("Telegram API error: %s — %s", e.response.status_code, e.response.text)
        return False
    except Exception as e:
        logger.error("Telegram delivery failed: %s", str(e))
        return False


async def test_connection(chat_id: str | None = None) -> bool:
    """Send a test message to verify the bot is configured correctly."""
    target = chat_id or settings.telegram_chat_id
    if not target:
        return False
    return await send_telegram(
        chat_id=target,
        title="ClawPing ✓",
        message="Telegram connection is working correctly.",
    )
