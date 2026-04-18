## Stage 3 — WebSocket Server

### Run
uvicorn main:app --reload --port 8000

### Test WebSocket connection
Open browser console on any tab and run:

const ws = new WebSocket('ws://localhost:8000/ws/feed');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.onopen = () => console.log('Connected');

You should see the "connected" welcome message immediately.

### Test with simulator script
Open second terminal:
python simulator.py

### Fire test events via HTTP
| Method | URL | What it does |
|--------|-----|--------------|
| GET  | /api/debug/ws/status   | How many clients connected |
| POST | /api/debug/ws/fire     | Fire a single event |
| POST | /api/debug/ws/simulate | Fire full 9-event sequence |

### Example: fire an LTP update
curl -X POST http://localhost:8000/api/debug/ws/fire \
  -H "Content-Type: application/json" \
  -d '{"event_type": "ltp_update",
       "payload": {"symbol": "NHPC", "ltp": 87.50,
                   "change": 1.30, "change_pct": 1.52}}'

### Example: fire full simulation
curl -X POST http://localhost:8000/api/debug/ws/simulate

### Verify logs are persisted
After firing agent_log events, check:
GET /api/agents/logs
The new logs should appear in the DB response.

### Expected event types and shapes
ltp_update:   { type, symbol, ltp, change, change_pct, timestamp }
agent_log:    { type, agent, level, msg, time, timestamp }
new_signal:   { type, signal, timestamp }
order_filled: { type, order_id, symbol, qty, price, action, mode, timestamp }
pnl_update:   { type, total_pnl, total_pnl_pct, available_capital, timestamp }
agent_status: { type, agent, status, last_run, timestamp }
connected:    { type, message, connections, timestamp }
pong:         { type, timestamp }
