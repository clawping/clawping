# 🔔 ClawPing

> **The notification layer for the AI agent ecosystem.**

ClawPing is a lightweight, self-hosted notification service that bridges AI agents and humans. Set time-based reminders, monitor conditions like crypto prices, and let agents ping humans (or each other) directly — all via Telegram or Email.

Part of the **[Claw Ecosystem](https://github.com/claw-ecosystem)** — a suite of interoperable AI agents.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)
![Status](https://img.shields.io/badge/Status-MVP-orange?style=flat)

---

## Features

- ⏰ **Time-based reminders** — `30s`, `5m`, `2h`, `1d` natural delay formats
- 📊 **Condition alerts** — Monitor crypto prices via CoinGecko; fire when threshold is crossed
- 🔗 **Agent webhooks** — Agents call `POST /webhook/notify` to ping humans directly
- 🔄 **Recurring pings** — Cron-based schedules (daily standups, weekly reviews)
- 🤖 **Telegram Bot** — Slash commands for managing pings from chat
- 📧 **Email notifications** — Async HTML-formatted emails via SMTP
- 🚀 **FastAPI backend** — Auto-documented REST API at `/docs`
- 🗄️ **SQLite storage** — Zero-dependency persistent storage

---

## Quick Start

### Prerequisites

- Python 3.11+
- A Telegram Bot token (from [@BotFather](https://t.me/BotFather))
- SMTP credentials (Gmail App Password or any SMTP provider)

### 1. Clone & Install

```bash
git clone https://github.com/claw-ecosystem/clawping.git
cd clawping

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your credentials
```

Minimum required configuration:

```env
TELEGRAM_BOT_TOKEN=123456:ABCdef...
SMTP_HOST=smtp.gmail.com
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your_app_password
API_KEY=your-secret-api-key
```

### 3. Run

```bash
# Development (hot reload)
make dev

# Production
make run

# Docker
make docker
```

Server starts at `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`.

---

## Telegram Bot Commands

Start a chat with your bot and use these commands:

| Command | Description | Example |
|---------|-------------|---------|
| `/ping <message>` | Send an instant notification | `/ping Hello!` |
| `/remind <delay> <message>` | Set a time-based reminder | `/remind 30m Check the oven` |
| `/alert <asset> <above\|below> <value> <message>` | Set a price alert | `/alert btc below 60000 BTC dipped` |
| `/repeat <cron> <message>` | Create a recurring reminder | `/repeat "0 9 * * 1-5" Standup time` |
| `/list` | List all active pings | `/list` |
| `/cancel <id>` | Cancel a ping by ID | `/cancel ping_7f3a9b2c` |
| `/help` | Show all commands | `/help` |

---

## API Reference

All requests require `Authorization: Bearer <API_KEY>` header.

Base URL: `http://localhost:8000`

### Health Check

```bash
GET /health
```

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0","uptime":"2m 34s","scheduler":"running"}
```

---

### Instant Notification

```bash
POST /ping
```

```bash
curl -X POST http://localhost:8000/ping \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello from ClawPing!",
    "channel": "telegram",
    "chat_id": "437734870"
  }'
```

---

### Create Reminder

```bash
POST /reminders
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | ✅ | Notification text |
| `delay` | string | ✅ | `30s`, `5m`, `2h`, `1d` |
| `channel` | string | ✅ | `telegram` or `email` |
| `chat_id` | string | if telegram | Telegram chat ID |
| `email` | string | if email | Recipient email address |

```bash
curl -X POST http://localhost:8000/reminders \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Deploy to production",
    "delay": "2h",
    "channel": "telegram",
    "chat_id": "437734870"
  }'
```

```json
{
  "id": "ping_7f3a9b2c",
  "status": "scheduled",
  "scheduled_at": "2025-02-25T11:31:00Z"
}
```

---

### Create Condition Alert

```bash
POST /conditions
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `asset` | string | ✅ | CoinGecko asset ID (`bitcoin`, `ethereum`) |
| `operator` | string | ✅ | `above` or `below` |
| `threshold` | number | ✅ | Price in USD |
| `message` | string | ✅ | Notification text |
| `channel` | string | ✅ | `telegram` or `email` |
| `repeat` | boolean | | Re-arm after firing (default: `false`) |

```bash
curl -X POST http://localhost:8000/conditions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "asset": "bitcoin",
    "operator": "below",
    "threshold": 60000,
    "message": "BTC dipped — check positions",
    "channel": "telegram",
    "chat_id": "437734870"
  }'
```

---

### Agent-to-Agent Webhook

```bash
POST /webhook/notify
```

Allows other Claw agents to trigger notifications without a user API key. Authenticate with an agent key (`X-Agent-Key` header).

```bash
curl -X POST http://localhost:8000/webhook/notify \
  -H "X-Agent-Key: sk_agent_clawscout_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "clawscout-v1.2",
    "priority": "urgent",
    "recipient": {
      "channel": "telegram",
      "chat_id": "437734870"
    },
    "notification": {
      "title": "🚨 Breaking news detected",
      "body": "SEC approved a Bitcoin ETF",
      "source_url": "https://reuters.com/..."
    }
  }'
```

---

### List Active Pings

```bash
GET /pings
```

```bash
curl http://localhost:8000/pings?status=scheduled&limit=20 \
  -H "Authorization: Bearer $API_KEY"
```

---

### Get Ping Detail

```bash
GET /pings/{id}
```

```bash
curl http://localhost:8000/pings/ping_7f3a9b2c \
  -H "Authorization: Bearer $API_KEY"
```

---

### Cancel a Ping

```bash
DELETE /pings/{id}
```

```bash
curl -X DELETE http://localhost:8000/pings/ping_7f3a9b2c \
  -H "Authorization: Bearer $API_KEY"
```

---

## Project Structure

```
clawping/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, routes
│   ├── config.py            # Settings from .env
│   ├── database.py          # SQLite connection & queries
│   ├── models.py            # Pydantic models
│   ├── channels/
│   │   ├── __init__.py
│   │   ├── telegram_channel.py   # Telegram send logic
│   │   └── email_channel.py      # SMTP send logic
│   └── services/
│       ├── __init__.py
│       ├── notifier.py      # Dispatch to channels
│       ├── scheduler.py     # APScheduler setup & jobs
│       └── telegram_bot.py  # Bot command handlers
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── Makefile
├── README.md
└── requirements.txt
```

---

## Roadmap

- [ ] Discord & Slack notification channels
- [ ] Natural language time parsing ("remind me tomorrow at 9am")
- [ ] Web dashboard for managing pings
- [ ] SMS notifications via Twilio
- [ ] More condition types: API health, GitHub PRs, weather
- [ ] Standardized Claw agent communication protocol
- [ ] PostgreSQL support for production deployments
- [ ] Multi-user support with auth tokens per user

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

[MIT](LICENSE) © 2025 Claw Ecosystem
