# Changelog

All notable changes to ClawPing will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Discord & Slack notification channels
- Natural language time parsing ("remind me tomorrow at 9am")
- Web dashboard for managing pings
- SMS notifications via Twilio
- PostgreSQL support

---

## [0.1.0] — 2025-02-25

### Added

- **FastAPI backend** with auto-generated `/docs` (Swagger UI) and `/redoc`
- **`POST /ping`** — instant notification endpoint
- **`POST /reminders`** — time-based reminder scheduling with delay formats: `30s`, `5m`, `2h`, `1d`
- **`POST /conditions`** — condition-based alerts (crypto price via CoinGecko API)
- **`POST /webhook/notify`** — agent-to-agent webhook endpoint with `X-Agent-Key` auth
- **`GET /pings`** — list active pings with status filtering and pagination
- **`GET /pings/{id}`** — retrieve a single ping by ID
- **`DELETE /pings/{id}`** — cancel a scheduled ping
- **`GET /health`** — service health check with scheduler and DB status
- **Telegram Bot** with slash commands: `/ping`, `/remind`, `/alert`, `/repeat`, `/list`, `/cancel`, `/help`
- **Email notifications** via async SMTP (`aiosmtplib`) with HTML formatting
- **APScheduler** integration for time-based and recurring ping delivery
- **CoinGecko price polling** every 60 seconds for condition-based alerts
- **SQLite storage** via `aiosqlite` for ping persistence across restarts
- **Pydantic v2** models for all request/response validation
- **Bearer token** authentication for REST API
- **Agent key** authentication for webhook endpoint
- **`Dockerfile`** and **`docker-compose.yml`** for containerized deployment
- **`Makefile`** with `install`, `dev`, `run`, `docker`, `lint`, `format`, `test`, `clean`
- **`.env.example`** with all configurable environment variables
- GitHub issue templates (bug report, feature request)
- GitHub PR template

[Unreleased]: https://github.com/claw-ecosystem/clawping/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/claw-ecosystem/clawping/releases/tag/v0.1.0
