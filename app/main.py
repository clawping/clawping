"""FastAPI application — routes, startup, and shutdown."""

import logging
import secrets
import uuid
from datetime import datetime, timezone
from time import time

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.database import (
    create_ping,
    get_agent_by_key,
    get_ping,
    init_db,
    list_pings,
    register_agent_key,
    update_ping_status,
)
from app.models import (
    ConditionRequest,
    ConditionResponse,
    HealthResponse,
    PingListResponse,
    PingRequest,
    PingResponse,
    RecurringRequest,
    RecurringResponse,
    ReminderRequest,
    ReminderResponse,
    TokenRequest,
    TokenResponse,
    WebhookRequest,
    WebhookResponse,
)
from app.services.notifier import dispatch
from app.services.scheduler import (
    cancel_job,
    parse_delay,
    schedule_recurring,
    schedule_reminder,
    start_scheduler,
    stop_scheduler,
)

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_start_time = time()

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ClawPing",
    description="AI Agent Notification & Reminder Service — part of the Claw Ecosystem.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Lifecycle ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup() -> None:
    await init_db()
    start_scheduler()
    logger.info("ClawPing v%s started", __version__)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    stop_scheduler()
    logger.info("ClawPing shutdown complete")


# ─── Auth ─────────────────────────────────────────────────────────────────────

def _require_api_key(authorization: str = Header(...)) -> None:
    """Dependency: validate Bearer token."""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or token != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")


async def _require_agent_key(x_agent_key: str = Header(...)) -> dict:
    """Dependency: validate X-Agent-Key for webhook endpoints."""
    agent = await get_agent_by_key(x_agent_key)
    if not agent:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid agent key")
    return agent


def _ping_id() -> str:
    return f"ping_{uuid.uuid4().hex[:8]}"


def _uptime() -> str:
    secs = int(time() - _start_time)
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Service health and connectivity status."""
    from app.services.scheduler import scheduler

    return HealthResponse(
        status="ok",
        version=__version__,
        uptime=_uptime(),
        scheduler="running" if scheduler.running else "stopped",
        db="connected",
        telegram="configured" if settings.telegram_bot_token else "not configured",
        email="configured" if settings.smtp_user else "not configured",
    )


# ─── Auth Endpoint ────────────────────────────────────────────────────────────

@app.post("/api/auth/token", response_model=TokenResponse, tags=["Auth"])
async def get_token(req: TokenRequest) -> TokenResponse:
    """Generate an API token. Authenticate with your API_SECRET_KEY."""
    if req.secret != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid secret")
    return TokenResponse(token=settings.api_key, expires_at=None, type="Bearer")


# ─── Instant Ping ─────────────────────────────────────────────────────────────

@app.post("/ping", response_model=PingResponse, status_code=201, tags=["Pings"])
async def instant_ping(req: PingRequest, _: None = Depends(_require_api_key)) -> PingResponse:
    """Send an instant notification immediately."""
    ping_id = _ping_id()
    now = datetime.now(tz=timezone.utc)

    delivered = await dispatch(
        channel=req.channel.value,
        message=req.message,
        title="🔔 Ping",
        chat_id=req.chat_id,
        email=req.email,
    )

    await create_ping({
        "id": ping_id,
        "type": "instant",
        "status": "fired",
        "message": req.message,
        "channel": req.channel.value,
        "chat_id": req.chat_id,
        "email": req.email,
        "created_at": now.isoformat(),
        "scheduled_at": now.isoformat(),
        "fired_at": now.isoformat(),
    })

    return PingResponse(
        id=ping_id,
        status="fired",
        message=req.message,
        channel=req.channel,
        delivered=delivered,
        created_at=now,
    )


# ─── Reminders ────────────────────────────────────────────────────────────────

@app.post("/reminders", response_model=ReminderResponse, status_code=201, tags=["Reminders"])
async def create_reminder(req: ReminderRequest, _: None = Depends(_require_api_key)) -> ReminderResponse:
    """Schedule a time-based reminder."""
    ping_id = _ping_id()
    now = datetime.now(tz=timezone.utc)

    try:
        fire_at = schedule_reminder(
            ping_id=ping_id,
            delay=req.delay,
            channel=req.channel.value,
            message=req.message,
            chat_id=req.chat_id,
            email=req.email,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await create_ping({
        "id": ping_id,
        "type": "reminder",
        "status": "scheduled",
        "message": req.message,
        "channel": req.channel.value,
        "chat_id": req.chat_id,
        "email": req.email,
        "delay": req.delay,
        "scheduled_at": fire_at.isoformat(),
        "created_at": now.isoformat(),
    })

    return ReminderResponse(
        id=ping_id,
        status="scheduled",
        message=req.message,
        channel=req.channel,
        delay=req.delay,
        scheduled_at=fire_at,
        created_at=now,
    )


# ─── Condition Alerts ─────────────────────────────────────────────────────────

@app.post("/conditions", response_model=ConditionResponse, status_code=201, tags=["Conditions"])
async def create_condition(req: ConditionRequest, _: None = Depends(_require_api_key)) -> ConditionResponse:
    """Create a condition-based alert (e.g. crypto price threshold)."""
    ping_id = _ping_id()
    now = datetime.now(tz=timezone.utc)

    await create_ping({
        "id": ping_id,
        "type": "condition",
        "status": "scheduled",
        "message": req.message,
        "channel": req.channel.value,
        "chat_id": req.chat_id,
        "email": req.email,
        "asset": req.asset,
        "operator": req.operator.value,
        "threshold": req.threshold,
        "repeat": int(req.repeat),
        "created_at": now.isoformat(),
    })

    return ConditionResponse(
        id=ping_id,
        status="scheduled",
        asset=req.asset,
        operator=req.operator,
        threshold=req.threshold,
        message=req.message,
        channel=req.channel,
        repeat=req.repeat,
        created_at=now,
    )


# ─── Recurring ────────────────────────────────────────────────────────────────

@app.post("/api/recurring", response_model=RecurringResponse, status_code=201, tags=["Recurring"])
async def create_recurring_schedule(req: RecurringRequest, _: None = Depends(_require_api_key)) -> RecurringResponse:
    """Create a cron-based recurring notification schedule."""
    ping_id = _ping_id()
    now = datetime.now(tz=timezone.utc)
    tz = req.timezone or settings.scheduler_timezone

    try:
        schedule_recurring(
            ping_id=ping_id,
            cron=req.cron,
            channel=req.channel.value,
            message=req.message,
            chat_id=req.chat_id,
            email=req.email,
            timezone=tz,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {e}")

    await create_ping({
        "id": ping_id,
        "type": "recurring",
        "status": "scheduled",
        "message": req.message,
        "channel": req.channel.value,
        "chat_id": req.chat_id,
        "email": req.email,
        "cron": req.cron,
        "timezone": tz,
        "created_at": now.isoformat(),
    })

    return RecurringResponse(
        id=ping_id,
        cron=req.cron,
        message=req.message,
        channel=req.channel,
        timezone=tz,
        created_at=now,
    )


# ─── Webhook (Agent-to-Agent) ─────────────────────────────────────────────────

@app.post("/webhook/notify", response_model=WebhookResponse, tags=["Webhooks"])
async def webhook_notify(req: WebhookRequest, agent: dict = Depends(_require_agent_key)) -> WebhookResponse:
    """Agent-to-agent notification endpoint. Authenticate with X-Agent-Key header."""
    ping_id = _ping_id()
    now = datetime.now(tz=timezone.utc)

    title = req.notification.title
    body = req.notification.body
    source_url = req.notification.source_url

    delivered = await dispatch(
        channel=req.recipient.channel.value,
        message=body,
        title=title,
        chat_id=req.recipient.chat_id,
        email=req.recipient.email,
        source_url=source_url,
    )

    await create_ping({
        "id": ping_id,
        "type": "webhook",
        "status": "fired",
        "message": f"{title}: {body}",
        "channel": req.recipient.channel.value,
        "chat_id": req.recipient.chat_id,
        "email": req.recipient.email,
        "agent_id": req.agent_id,
        "created_at": now.isoformat(),
        "scheduled_at": now.isoformat(),
        "fired_at": now.isoformat(),
    })

    return WebhookResponse(
        success=delivered,
        ping_id=ping_id,
        delivered=delivered,
        channel=req.recipient.channel,
    )


@app.post("/webhook/agents/register", tags=["Webhooks"], status_code=201)
async def register_agent(
    body: dict,
    _: None = Depends(_require_api_key),
) -> dict:
    """Register a new agent and receive an agent key for webhook auth."""
    agent_id = body.get("agent_id", "")
    name = body.get("name", "")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")

    agent_key = f"sk_agent_{secrets.token_hex(16)}"
    record = await register_agent_key(agent_id=agent_id, name=name, agent_key=agent_key)
    return {
        "agent_key": record["agent_key"],
        "agent_id": record["agent_id"],
        "created_at": record["created_at"],
    }


# ─── List / Get / Cancel Pings ───────────────────────────────────────────────

@app.get("/pings", response_model=PingListResponse, tags=["Pings"])
async def get_pings(
    status: str | None = Query(None, description="Filter by status: scheduled, fired, cancelled"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(_require_api_key),
) -> PingListResponse:
    """List pings with optional status filtering and pagination."""
    total, pings = await list_pings(status=status, limit=limit, offset=offset)
    return PingListResponse(total=total, limit=limit, offset=offset, pings=pings)


@app.get("/pings/{ping_id}", tags=["Pings"])
async def get_ping_detail(ping_id: str, _: None = Depends(_require_api_key)) -> dict:
    """Get details for a specific ping by ID."""
    ping = await get_ping(ping_id)
    if not ping:
        raise HTTPException(status_code=404, detail="Ping not found")
    return ping


@app.delete("/pings/{ping_id}", tags=["Pings"])
async def cancel_ping(ping_id: str, _: None = Depends(_require_api_key)) -> dict:
    """Cancel a scheduled ping."""
    ping = await get_ping(ping_id)
    if not ping:
        raise HTTPException(status_code=404, detail="Ping not found")
    if ping["status"] == "fired":
        raise HTTPException(status_code=400, detail="Cannot cancel a ping that has already fired")
    if ping["status"] == "cancelled":
        raise HTTPException(status_code=400, detail="Ping is already cancelled")

    cancel_job(ping_id)
    await update_ping_status(ping_id, "cancelled")
    return {"success": True, "id": ping_id, "status": "cancelled"}


# ─── Test Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/test/telegram", tags=["Testing"])
async def test_telegram(_: None = Depends(_require_api_key)) -> dict:
    """Send a test Telegram message to verify bot configuration."""
    from app.channels.telegram_channel import test_connection
    ok = await test_connection()
    if not ok:
        raise HTTPException(status_code=400, detail="Telegram test failed — check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    return {"success": True, "message": "Telegram connected ✓", "chat_id": settings.telegram_chat_id}


@app.post("/api/test/email", tags=["Testing"])
async def test_email(body: dict = {}, _: None = Depends(_require_api_key)) -> dict:
    """Send a test email to verify SMTP configuration."""
    from app.channels.email_channel import test_connection
    to = body.get("to") or settings.email_to
    if not to:
        raise HTTPException(status_code=400, detail="Provide 'to' in request body or set EMAIL_TO in .env")
    ok = await test_connection(to=to)
    if not ok:
        raise HTTPException(status_code=400, detail="Email test failed — check SMTP configuration")
    return {"success": True, "message": "Test email sent ✓", "to": to}


# ─── Telegram Webhook ─────────────────────────────────────────────────────────

@app.post("/telegram/webhook", tags=["Telegram"], include_in_schema=False)
async def telegram_webhook(update: dict) -> dict:
    """Receive Telegram bot updates via webhook."""
    try:
        from app.services.telegram_bot import build_bot
        from telegram import Update as TGUpdate

        bot_app = build_bot()
        if not bot_app:
            return {"ok": False}

        tg_update = TGUpdate.de_json(update, bot_app.bot)
        async with bot_app:
            await bot_app.process_update(tg_update)
        return {"ok": True}
    except Exception as e:
        logger.error("Telegram webhook error: %s", str(e))
        return {"ok": False, "error": str(e)}
