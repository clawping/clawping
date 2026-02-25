"""Telegram Bot command handlers."""

import logging
import uuid
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings
from app.database import create_ping, list_pings, update_ping_status
from app.services.notifier import dispatch
from app.services.scheduler import cancel_job, parse_delay, schedule_recurring, schedule_reminder

logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ping_id() -> str:
    return f"ping_{uuid.uuid4().hex[:8]}"


async def _reply(update: Update, text: str) -> None:
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── Command Handlers ─────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, (
        "🔔 *ClawPing* — AI Agent Notification Service\n\n"
        "I bridge AI agents and humans with smart notifications.\n\n"
        "Type `/help` to see available commands."
    ))


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, (
        "*ClawPing Commands*\n\n"
        "`/ping <message>` — Instant notification\n"
        "`/remind <delay> <message>` — Time-based reminder (30s, 5m, 2h, 1d)\n"
        "`/alert <asset> <above|below> <value> <msg>` — Price alert\n"
        "`/repeat \"<cron>\" <message>` — Recurring ping\n"
        "`/list` — List active pings\n"
        "`/cancel <id>` — Cancel a ping\n"
    ))


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await _reply(update, "Usage: `/ping <message>`")
        return

    message = " ".join(context.args)
    chat_id = str(update.effective_chat.id)

    delivered = await dispatch(channel="telegram", message=message, chat_id=chat_id)
    if delivered:
        await _reply(update, "✅ Ping sent!")
    else:
        await _reply(update, "❌ Failed to send ping.")


async def cmd_remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await _reply(update, "Usage: `/remind <delay> <message>`\nExample: `/remind 30m Check the oven`")
        return

    delay = context.args[0]
    message = " ".join(context.args[1:])
    chat_id = str(update.effective_chat.id)
    ping_id = _ping_id()

    try:
        fire_at = schedule_reminder(
            ping_id=ping_id,
            delay=delay,
            channel="telegram",
            message=message,
            chat_id=chat_id,
        )
        await create_ping({
            "id": ping_id,
            "type": "reminder",
            "status": "scheduled",
            "message": message,
            "channel": "telegram",
            "chat_id": chat_id,
            "delay": delay,
            "scheduled_at": fire_at.isoformat(),
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
        })
        await _reply(update, f"⏰ Reminder set! I'll ping you in *{delay}*.\nID: `{ping_id}`")
    except ValueError as e:
        await _reply(update, f"❌ {e}")


async def cmd_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # /alert btc below 60000 BTC dipped — act now
    if len(context.args) < 4:
        await _reply(update, "Usage: `/alert <asset> <above|below> <value> <message>`")
        return

    asset = context.args[0].lower()
    operator = context.args[1].lower()
    threshold_str = context.args[2]
    message = " ".join(context.args[3:])
    chat_id = str(update.effective_chat.id)

    if operator not in ("above", "below"):
        await _reply(update, "❌ Operator must be `above` or `below`.")
        return
    try:
        threshold = float(threshold_str)
    except ValueError:
        await _reply(update, "❌ Threshold must be a number.")
        return

    ping_id = _ping_id()
    await create_ping({
        "id": ping_id,
        "type": "condition",
        "status": "scheduled",
        "message": message,
        "channel": "telegram",
        "chat_id": chat_id,
        "asset": asset,
        "operator": operator,
        "threshold": threshold,
        "repeat": 0,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    })
    await _reply(update, f"📊 Alert set: notify me when *{asset.upper()}* goes *{operator}* ${threshold:,.0f}.\nID: `{ping_id}`")


async def cmd_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # /repeat "0 9 * * 1-5" Daily standup
    if len(context.args) < 2:
        await _reply(update, 'Usage: `/repeat "<cron>" <message>`\nExample: `/repeat "0 9 * * 1-5" Standup time`')
        return

    cron = context.args[0].strip('"')
    message = " ".join(context.args[1:])
    chat_id = str(update.effective_chat.id)
    ping_id = _ping_id()

    try:
        schedule_recurring(
            ping_id=ping_id,
            cron=cron,
            channel="telegram",
            message=message,
            chat_id=chat_id,
        )
        await create_ping({
            "id": ping_id,
            "type": "recurring",
            "status": "scheduled",
            "message": message,
            "channel": "telegram",
            "chat_id": chat_id,
            "cron": cron,
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
        })
        await _reply(update, f"🔄 Recurring ping set!\nCron: `{cron}`\nID: `{ping_id}`")
    except Exception as e:
        await _reply(update, f"❌ Invalid cron expression: {e}")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    total, pings = await list_pings(status="scheduled", limit=10)
    if not pings:
        await _reply(update, "No active pings.")
        return

    lines = [f"*Active Pings ({total})*\n"]
    for p in pings:
        lines.append(f"• `{p['id']}` — {p['type']}: {p['message'][:40]}...")
    await _reply(update, "\n".join(lines))


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await _reply(update, "Usage: `/cancel <ping_id>`")
        return

    ping_id = context.args[0]
    cancel_job(ping_id)
    await update_ping_status(ping_id, "cancelled")
    await _reply(update, f"✅ Ping `{ping_id}` cancelled.")


# ─── Bot Application ──────────────────────────────────────────────────────────

def build_bot() -> Application | None:
    """Build and return the Telegram bot application, or None if not configured."""
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram bot disabled")
        return None

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("remind", cmd_remind))
    app.add_handler(CommandHandler("alert", cmd_alert))
    app.add_handler(CommandHandler("repeat", cmd_repeat))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    return app
