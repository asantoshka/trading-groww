## Stage 2 — Database + Migrations + Seed

### Setup
pip install -r requirements.txt
alembic upgrade head
python seed.py
uvicorn main:app --reload --port 8000

### Verify seed worked
sqlite3 trading.db "SELECT COUNT(*) FROM trades;"      -- expect 5
sqlite3 trading.db "SELECT COUNT(*) FROM signals;"     -- expect 3
sqlite3 trading.db "SELECT COUNT(*) FROM agent_logs;"  -- expect 10
sqlite3 trading.db "SELECT mode FROM config;"          -- expect paper

### Test endpoints (all should return DB data now)
| Method | URL | Expected |
|--------|-----|----------|
| GET  | /api/trades              | 5 trades from DB |
| GET  | /api/trades/stats        | win_rate ~60%, total_pnl positive |
| GET  | /api/trades?result=winners | 3 trades |
| GET  | /api/trades?symbol=nhpc  | 1 trade |
| GET  | /api/signals             | 3 signals from DB |
| GET  | /api/signals/today       | signals with today's date |
| POST | /api/signals/manual      | new row appears in DB |
| GET  | /api/config              | config from DB |
| POST | /api/config              | update persists after restart |
| GET  | /api/agents/logs         | 10 logs from DB |
| GET  | /api/agents/logs?level=error | filtered from DB |

### Confirm persistence
POST /api/config with { "rsi_oversold": 30 }
Restart uvicorn
GET /api/config → rsi_oversold should still be 30
