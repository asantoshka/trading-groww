## Stage 1 — FastAPI Scaffold

### Run
pip install -r requirements.txt  
cp .env.example .env  
uvicorn main:app --reload --port 8000

### Test endpoints
| Method | URL | Expected |
|--------|-----|----------|
| GET  | /                        | API info |
| GET  | /health                  | Health + agent states |
| GET  | /api/agents              | 3 agent statuses |
| GET  | /api/agents/logs         | 10 log entries |
| GET  | /api/agents/logs?agent=market_scanner | filtered logs |
| POST | /api/agents/market_scanner/start | agent started |
| GET  | /api/positions           | 2 open positions |
| POST | /api/positions/p1/close  | position closed |
| GET  | /api/trades              | 5 trades |
| GET  | /api/trades/stats        | win rate, avg pnl |
| GET  | /api/signals/today       | 3 signals |
| POST | /api/signals/manual      | inject signal |
| GET  | /api/config              | current config |
| POST | /api/config              | update config |
| GET  | /api/status              | full system status |

### Interactive docs
http://localhost:8000/docs
