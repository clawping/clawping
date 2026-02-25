"""Notification dispatcher — routes to the correct channel."""

import logging

from app.channels.email_channel import send_email
from app.channels.telegram_channel import send_telegram

logger = logging.getLogger(__name__)


async def dispatch(
    channel: str,
    message: str,
    title: str | None = None,
    chat_id: str | None = None,
    email: str | None = None,
    source_url: str | None = None,
) -> bool:
    """
    Dispatch a notification to the specified channel.

    Args:
        channel:    'telegram' or 'email'
        message:    Notification body text.
        title:      Optional heading / subject.
        chat_id:    Telegram chat ID (required for telegram channel).
        email:      Email address (required for email channel).
        source_url: Optional source URL appended to email body.

    Returns:
        True if delivery succeeded.
    """
    if channel == "telegram":
        if not chat_id:
            logger.error("dispatch: chat_id required for telegram channel")
            return False
        return await send_telegram(chat_id=chat_id, message=message, title=title)

    if channel == "email":
        if not email:
            logger.error("dispatch: email required for email channel")
            return False
        return await send_email(
            to=email,
            subject=title or "ClawPing Notification",
            body=message,
            title=title,
            source_url=source_url,
        )

    logger.error("dispatch: unknown channel '%s'", channel)
    return False
