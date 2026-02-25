"""Database connection and query helpers (aiosqlite / SQLAlchemy async)."""

import os
from datetime import datetime

import aiosqlite

from app.config import settings

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

DB_PATH = settings.database_url.replace("sqlite+aiosqlite:///", "")


async def get_db() -> aiosqlite.Connection:
    """Open and return a database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    """Create tables on startup if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS pings (
                id          TEXT PRIMARY KEY,
                type        TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'scheduled',
                message     TEXT NOT NULL,
                channel     TEXT NOT NULL,
                chat_id     TEXT,
                email       TEXT,
                delay       TEXT,
                cron        TEXT,
                timezone    TEXT,
                asset       TEXT,
                operator    TEXT,
                threshold   REAL,
                repeat      INTEGER DEFAULT 0,
                agent_id    TEXT,
                scheduled_at TEXT,
                fired_at    TEXT,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_keys (
                id          TEXT PRIMARY KEY,
                agent_id    TEXT NOT NULL UNIQUE,
                name        TEXT,
                agent_key   TEXT NOT NULL UNIQUE,
                created_at  TEXT NOT NULL
            );
        """)
        await db.commit()


async def create_ping(ping: dict) -> dict:
    """Insert a new ping record."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cols = ", ".join(ping.keys())
        placeholders = ", ".join("?" * len(ping))
        await db.execute(
            f"INSERT INTO pings ({cols}) VALUES ({placeholders})",
            list(ping.values()),
        )
        await db.commit()
        row = await db.execute("SELECT * FROM pings WHERE id = ?", (ping["id"],))
        return dict(await row.fetchone())


async def get_ping(ping_id: str) -> dict | None:
    """Fetch a single ping by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await db.execute("SELECT * FROM pings WHERE id = ?", (ping_id,))
        result = await row.fetchone()
        return dict(result) if result else None


async def list_pings(status: str | None = None, limit: int = 20, offset: int = 0) -> tuple[int, list[dict]]:
    """List pings with optional status filter and pagination."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        where = "WHERE status = ?" if status else ""
        params = [status] if status else []

        count_row = await db.execute(f"SELECT COUNT(*) FROM pings {where}", params)
        total = (await count_row.fetchone())[0]

        rows = await db.execute(
            f"SELECT * FROM pings {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        pings = [dict(r) for r in await rows.fetchall()]
        return total, pings


async def update_ping_status(ping_id: str, status: str) -> None:
    """Update a ping's status."""
    async with aiosqlite.connect(DB_PATH) as db:
        fired_at = datetime.utcnow().isoformat() if status == "fired" else None
        await db.execute(
            "UPDATE pings SET status = ?, fired_at = ? WHERE id = ?",
            (status, fired_at, ping_id),
        )
        await db.commit()


async def get_scheduled_conditions() -> list[dict]:
    """Fetch all active condition-based alerts."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute(
            "SELECT * FROM pings WHERE type = 'condition' AND status = 'scheduled'"
        )
        return [dict(r) for r in await rows.fetchall()]


async def register_agent_key(agent_id: str, name: str, agent_key: str) -> dict:
    """Register an agent key for webhook auth."""
    import uuid
    record = {
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "name": name,
        "agent_key": agent_key,
        "created_at": datetime.utcnow().isoformat(),
    }
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO agent_keys (id, agent_id, name, agent_key, created_at) VALUES (?, ?, ?, ?, ?)",
            list(record.values()),
        )
        await db.commit()
    return record


async def get_agent_by_key(agent_key: str) -> dict | None:
    """Look up an agent by their webhook key."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await db.execute("SELECT * FROM agent_keys WHERE agent_key = ?", (agent_key,))
        result = await row.fetchone()
        return dict(result) if result else None
