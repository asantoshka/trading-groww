## Stage 9 — Execution Agent

### Run tests
pytest tests/test_execution_agent.py -v

### How the full flow works now
Scanner finds signal → Risk Gatekeeper approves
→ Execution Agent places order + GTT stoploss
→ Monitor polls LTP every 30s
→ Target hit → MARKET SELL + cancel GTT
→ 15:10 IST → force close all MIS positions

### Test end-to-end in paper mode
The scanner will automatically trigger execution
when it finds an approved signal during market hours.

To force test execution directly:
curl -X POST http://localhost:8000/api/risk/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "signal": {
      "symbol": "NHPC",
      "action": "BUY",
      "entry_price": 84.10,
      "target": 89.50,
      "stoploss": 81.00,
      "qty": 9,
      "confidence": 78
    }
  }'

Then check positions:
curl http://localhost:8000/api/positions

Check DB:
sqlite3 trading.db \
  "SELECT symbol, status, entry_price,
          exit_price, pnl, exit_reason
   FROM positions
   ORDER BY created_at DESC LIMIT 5;"

### Monitor LTP polling in simulator
python simulator.py
(Every 30s you'll see LTP updates for
 open positions)

### Manual squareoff
curl -X POST http://localhost:8000/api/positions/{position_id}/close
