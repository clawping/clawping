"""APScheduler setup and job management for reminders and condition checks."""

import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from app.config import settings
from app.database import get_scheduled_conditions, update_ping_status
from app.services.notifier import dispatch

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)


# ─── Delay Parser ─────────────────────────────────────────────────────────────

_DELAY_RE = re.compile(r"^(\d+)(s|m|h|d)$")
_UNITS = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}


def parse_delay(delay: str) -> timedelta:
    """
    Parse a human-readable delay string into a timedelta.

    Supported formats: 30s, 5m, 2h, 1d

    Raises:
        ValueError: If the format is not recognized.
    """
    m = _DELAY_RE.match(delay.strip().lower())
    if not m:
        raise ValueError(
            f"Invalid delay format '{delay}'. Use: 30s, 5m, 2h, 1d"
        )
    value, unit = int(m.group(1)), m.group(2)
    return timedelta(**{_UNITS[unit]: value})


# ─── Reminder Scheduling ──────────────────────────────────────────────────────

async def _fire_reminder(ping_id: str, channel: str, message: str, chat_id: str | None, email: str | None) -> None:
    """Callback executed by APScheduler when a reminder fires."""
    logger.info("Firing reminder ping_id=%s", ping_id)
    delivered = await dispatch(
        channel=channel,
        message=message,
        title="⏰ Reminder",
        chat_id=chat_id,
        email=email,
    )
    status = "fired" if delivered else "scheduled"
    await update_ping_status(ping_id, status)


def schedule_reminder(
    ping_id: str,
    delay: str,
    channel: str,
    message: str,
    chat_id: str | None = None,
    email: str | None = None,
) -> datetime:
    """
    Add a one-shot reminder job to the scheduler.

    Returns:
        The UTC datetime when the reminder will fire.
    """
    delta = parse_delay(delay)
    fire_at = datetime.now(tz=timezone.utc) + delta

    scheduler.add_job(
        _fire_reminder,
        trigger=DateTrigger(run_date=fire_at),
        id=ping_id,
        kwargs=dict(ping_id=ping_id, channel=channel, message=message, chat_id=chat_id, email=email),
        replace_existing=True,
        misfire_grace_time=120,
    )
    logger.info("Scheduled reminder %s to fire at %s", ping_id, fire_at.isoformat())
    return fire_at


# ─── Recurring Scheduling ─────────────────────────────────────────────────────

def schedule_recurring(
    ping_id: str,
    cron: str,
    channel: str,
    message: str,
    chat_id: str | None = None,
    email: str | None = None,
    timezone: str | None = None,
) -> None:
    """Add a recurring cron job to the scheduler."""
    tz = timezone or settings.scheduler_timezone

    async def _fire() -> None:
        await dispatch(channel=channel, message=message, title="🔄 Recurring Ping", chat_id=chat_id, email=email)

    scheduler.add_job(
        _fire,
        trigger=CronTrigger.from_crontab(cron, timezone=tz),
        id=f"recurring_{ping_id}",
        replace_existing=True,
        misfire_grace_time=300,
    )
    logger.info("Scheduled recurring job %s with cron '%s'", ping_id, cron)


# ─── Condition Checking ───────────────────────────────────────────────────────

async def _check_conditions() -> None:
    """Periodically check all active condition alerts against live data."""
    conditions = await get_scheduled_conditions()
    if not conditions:
        return

    # Batch unique assets
    assets = list({c["asset"] for c in conditions})
    prices: dict[str, float] = {}

    try:
        ids = ",".join(assets)
        headers = {}
        if settings.coingecko_api_key:
            headers["x-cg-pro-api-key"] = settings.coingecko_api_key

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": ids, "vs_currencies": "usd"},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            for asset in assets:
                if asset in data:
                    prices[asset] = data[asset]["usd"]
    except Exception as e:
        logger.warning("CoinGecko fetch failed: %s", str(e))
        return

    for condition in conditions:
        asset = condition["asset"]
        price = prices.get(asset)
        if price is None:
            continue

        threshold = float(condition["threshold"])
        operator = condition["operator"]
        triggered = (operator == "above" and price > threshold) or \
                    (operator == "below" and price < threshold)

        if triggered:
            logger.info(
                "Condition triggered: %s %s %s (current: %s)",
                asset, operator, threshold, price,
            )
            await dispatch(
                channel=condition["channel"],
                message=condition["message"],
                title=f"📊 Price Alert: {asset.upper()}",
                chat_id=condition.get("chat_id"),
                email=condition.get("email"),
            )
            new_status = "scheduled" if condition.get("repeat") else "fired"
            await update_ping_status(condition["id"], new_status)


def start_scheduler() -> None:
    """Start APScheduler and register the condition polling job."""
    scheduler.add_job(
        _check_conditions,
        trigger="interval",
        seconds=settings.condition_check_interval,
        id="condition_checker",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started (tz=%s)", settings.scheduler_timezone)


def stop_scheduler() -> None:
    """Gracefully stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def cancel_job(ping_id: str) -> None:
    """Remove a scheduled job by ping ID."""
    for job_id in [ping_id, f"recurring_{ping_id}"]:
        try:
            scheduler.remove_job(job_id)
            logger.info("Cancelled job %s", job_id)
        except Exception:
            pass
