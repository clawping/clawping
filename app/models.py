"""Pydantic v2 request/response models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─── Enums ───────────────────────────────────────────────────────────────────

class Channel(str, Enum):
    telegram = "telegram"
    email = "email"


class PingStatus(str, Enum):
    scheduled = "scheduled"
    fired = "fired"
    cancelled = "cancelled"


class ConditionOperator(str, Enum):
    above = "above"
    below = "below"


class Priority(str, Enum):
    low = "low"
    normal = "normal"
    urgent = "urgent"


# ─── Instant Ping ─────────────────────────────────────────────────────────────

class PingRequest(BaseModel):
    message: str = Field(..., max_length=2000, description="Notification text")
    channel: Channel = Field(..., description="Delivery channel")
    chat_id: Optional[str] = Field(None, description="Telegram chat ID")
    email: Optional[str] = Field(None, description="Recipient email address")


class PingResponse(BaseModel):
    id: str
    status: PingStatus
    message: str
    channel: Channel
    delivered: bool
    created_at: datetime


# ─── Reminder ─────────────────────────────────────────────────────────────────

class ReminderRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    delay: str = Field(..., description="Delay until firing: 30s, 5m, 2h, 1d")
    channel: Channel
    chat_id: Optional[str] = None
    email: Optional[str] = None


class ReminderResponse(BaseModel):
    id: str
    status: PingStatus
    message: str
    channel: Channel
    delay: str
    scheduled_at: datetime
    created_at: datetime


# ─── Condition Alert ──────────────────────────────────────────────────────────

class ConditionRequest(BaseModel):
    asset: str = Field(..., description="CoinGecko asset ID: bitcoin, ethereum")
    operator: ConditionOperator
    threshold: float = Field(..., description="Price threshold in USD")
    message: str = Field(..., max_length=2000)
    channel: Channel
    chat_id: Optional[str] = None
    email: Optional[str] = None
    repeat: bool = Field(False, description="Re-arm alert after it fires")


class ConditionResponse(BaseModel):
    id: str
    status: PingStatus
    asset: str
    operator: ConditionOperator
    threshold: float
    message: str
    channel: Channel
    repeat: bool
    created_at: datetime


# ─── Recurring Schedule ───────────────────────────────────────────────────────

class RecurringRequest(BaseModel):
    cron: str = Field(..., description="5-field cron expression: '0 9 * * 1-5'")
    message: str = Field(..., max_length=2000)
    channel: Channel
    chat_id: Optional[str] = None
    email: Optional[str] = None
    timezone: Optional[str] = None


class RecurringResponse(BaseModel):
    id: str
    cron: str
    message: str
    channel: Channel
    timezone: str
    created_at: datetime


# ─── Webhook (Agent-to-Agent) ─────────────────────────────────────────────────

class WebhookRecipient(BaseModel):
    channel: Channel
    chat_id: Optional[str] = None
    email: Optional[str] = None


class WebhookNotification(BaseModel):
    title: str
    body: str
    source_url: Optional[str] = None
    timestamp: Optional[datetime] = None


class WebhookRequest(BaseModel):
    agent_id: str
    priority: Priority = Priority.normal
    recipient: WebhookRecipient
    notification: WebhookNotification
    metadata: Optional[dict[str, Any]] = None


class WebhookResponse(BaseModel):
    success: bool
    ping_id: str
    delivered: bool
    channel: Channel


# ─── List / Detail ────────────────────────────────────────────────────────────

class PingListItem(BaseModel):
    id: str
    status: PingStatus
    type: str  # reminder | condition | recurring | instant
    message: str
    channel: Channel
    scheduled_at: Optional[datetime] = None
    created_at: datetime


class PingListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    pings: list[PingListItem]


# ─── Auth ─────────────────────────────────────────────────────────────────────

class TokenRequest(BaseModel):
    secret: str
    expires_in: str = Field("never", description="7d, 30d, or never")


class TokenResponse(BaseModel):
    token: str
    expires_at: Optional[datetime]
    type: str = "Bearer"


# ─── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: str
    scheduler: str
    db: str
    telegram: str
    email: str
