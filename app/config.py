"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Telegram ───────────────────────────────────────────
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # ─── Email / SMTP ────────────────────────────────────────
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "ClawPing <noreply@clawping.io>"
    email_to: str = ""

    # ─── Database ────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./data/clawping.db"

    # ─── API ─────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: str = "change-me"

    # ─── Scheduler ───────────────────────────────────────────
    scheduler_timezone: str = "UTC"
    max_pings_per_user: int = 100
    condition_check_interval: int = 60  # seconds

    # ─── CoinGecko ───────────────────────────────────────────
    coingecko_api_key: str = ""

    # ─── Debug ───────────────────────────────────────────────
    debug: bool = False


settings = Settings()
