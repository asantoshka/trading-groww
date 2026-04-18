# Groww Agentic Trading Bot

> Central documentation for the Groww Agentic Trading project.

This folder contains the current production documentation plus the archived stage-by-stage build notes. The backend uses FastAPI, APScheduler, Groww Trading API integration, Claude or Bedrock for reasoning, and optional Telegram notifications.

## Documentation Map

- [Project Overview](#project-overview)
- [Setup](#setup)
- [Operations](#operations)
- [Configuration](#configuration)
- [Telegram Notifications](#telegram-notifications)
- [Testing](#testing)
- [Docker](#docker)
- [API Surface](#api-surface)
- [Stage Archive](#stage-archive)

## Project Overview

The system runs three coordinated agents:

1. `Market Scanner`
   Fetches market data, computes RSI and MACD locally, and asks Claude to reason over the indicator set and produce a structured signal.
2. `Risk Gatekeeper`
   Applies capital, trade value, loss, confidence, and risk-reward checks in Python before any execution is allowed.
3. `Execution Agent`
   Places entry orders, places or manages stoploss protection, monitors open positions, exits at target, and force closes MIS positions near market close.

Supporting services:

- `APScheduler` for timed scans, token reset handling, and square-off reminders
- `GrowwClient` for broker API access
- `TokenManager` for session token lifecycle
- `WebSocketManager` for live dashboard events
- `TelegramNotifier` for optional bot alerts

## Repository Layout

```text
trading-app/
├── backend/
│   ├── main.py
│   ├── scheduler.py
│   ├── env_validator.py
│   ├── models.py
│   ├── database.py
│   ├── seed.py
│   ├── simulator.py
│   ├── services/
│   │   ├── market_scanner.py
│   │   ├── risk_gatekeeper.py
│   │   ├── execution_agent.py
│   │   ├── groww_client.py
│   │   ├── token_manager.py
│   │   ├── llm_client.py
│   │   ├── websocket_manager.py
│   │   └── telegram_notifier.py
│   ├── routers/
│   └── tests/
├── frontend/
│   └── src/
└── docs/
```

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python seed.py
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Local URLs

- Frontend: `http://localhost:5173`
- Backend docs: `http://localhost:8000/docs`
- WebSocket feed: `ws://localhost:8000/ws/feed`

## Environment

Core backend variables:

```bash
GROWW_API_KEY=your_groww_trading_api_key
GROWW_API_SECRET=your_groww_trading_api_secret
GROWW_ACCESS_TOKEN=
GROWW_BASE_URL=https://api.groww.in

LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key

AWS_REGION=ap-south-1

MODE=paper
DATABASE_URL=sqlite:///./trading.db

TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## Operations

### Daily Schedule

| Time (IST) | Action |
|---|---|
| 06:05 | Groww token invalidated |
| 09:14 | Market open reminder |
| 09:15 | Scheduled scan |
| 11:00 | Scheduled scan |
| 13:30 | Scheduled scan |
| 15:05 | Square-off warning |
| 15:10 | MIS force close |

### Daily Startup Checklist

1. Approve the Groww API session in the Groww dashboard.
2. Start backend and frontend.
3. Verify:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/scheduler/status
```

## Configuration

Runtime config is editable from the UI or API.

```bash
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"rsi_oversold": 35, "confidence_threshold": 70, "max_trade_value": 2000}'
```

Changing scan times reloads APScheduler immediately.

## Telegram Notifications

Telegram alerts are optional and backend-only.

### Enable

1. Create a bot with `@BotFather`
2. Send a message to the bot
3. Resolve your chat id with:

```bash
https://api.telegram.org/bot<TOKEN>/getUpdates
```

4. Add to `backend/.env`:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Test

```bash
curl -X POST http://localhost:8000/api/debug/telegram/test
```

Expected result:

- API returns `{ "sent": true, "enabled": true }`
- Telegram receives a confirmation message

### Notification Events

- Scan started
- No signal found
- Signal approved or rejected
- Scanner error
- Order placed
- GTT stoploss placed
- Target hit
- Stoploss hit
- Square-off warning
- Square-off complete
- Token refresh reminder
- Market open reminder

If Telegram variables are absent, the notifier disables itself and the rest of the system continues normally.

## Testing

Backend test suite:

```bash
cd backend
pytest tests/ -v
```

Current verified result:

- `52 passed, 6 skipped`

Useful targeted runs:

```bash
pytest tests/test_risk_gatekeeper.py -v
pytest tests/test_groww_client.py -v
pytest tests/test_market_scanner.py -v
pytest tests/test_execution_agent.py -v
```

## Docker

Build and run:

```bash
cp backend/.env.example backend/.env
docker-compose up --build
```

Services:

- Backend on `http://localhost:8000`
- Frontend on `http://localhost`

## API Surface

Key endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health and mode |
| GET | `/api/status` | Dashboard summary |
| POST | `/api/agents/scanner/trigger` | Manual scan |
| GET | `/api/scheduler/status` | Scheduler state |
| POST | `/api/scheduler/pause` | Pause scan jobs |
| POST | `/api/scheduler/resume` | Resume scan jobs |
| GET | `/api/positions` | Open positions |
| POST | `/api/positions/{id}/close` | Manual square-off |
| GET | `/api/trades` | Trade history |
| GET | `/api/trades/stats` | Trade analytics |
| GET | `/api/signals/today` | Today’s signals |
| POST | `/api/signals/manual` | Inject signal |
| GET | `/api/config` | Current config |
| POST | `/api/config` | Update config |
| POST | `/api/debug/telegram/test` | Telegram health check |
| WS | `/ws/feed` | Real-time events |

## Stage Archive

All stage notes are now in this folder.

### Backend stages

- [Stage 01](/Users/santosh/code/trading-ai/trading-app/docs/backend_stage01.md)
- [Stage 02](/Users/santosh/code/trading-ai/trading-app/docs/backend_stage02.md)
- [Stage 03](/Users/santosh/code/trading-ai/trading-app/docs/backend_stage03.md)
- [Stage 06](/Users/santosh/code/trading-ai/trading-app/docs/backend_stage06.md)
- [Stage 07](/Users/santosh/code/trading-ai/trading-app/docs/backend_stage07.md)
- [Stage 08](/Users/santosh/code/trading-ai/trading-app/docs/backend_stage08.md)
- [Stage 09](/Users/santosh/code/trading-ai/trading-app/docs/backend_stage09.md)
- [Stage 15](/Users/santosh/code/trading-ai/trading-app/docs/backend_stage15.md)

### Frontend stages

- [Stage 04](/Users/santosh/code/trading-ai/trading-app/docs/frontend_stage04.md)
- [Stage 05](/Users/santosh/code/trading-ai/trading-app/docs/frontend_stage05.md)
- [Stage 10](/Users/santosh/code/trading-ai/trading-app/docs/frontend_stage10.md)
- [Stage 11](/Users/santosh/code/trading-ai/trading-app/docs/frontend_stage11.md)
- [Stage 12](/Users/santosh/code/trading-ai/trading-app/docs/frontend_stage12.md)
- [Stage 13](/Users/santosh/code/trading-ai/trading-app/docs/frontend_stage13.md)
- [Stage 14](/Users/santosh/code/trading-ai/trading-app/docs/frontend_stage14.md)
