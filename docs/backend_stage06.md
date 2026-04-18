## Stage 6 — Risk Gatekeeper

### Run tests
cd backend
pytest tests/test_risk_gatekeeper.py -v

All 15 tests must pass. If any fail, the
gatekeeper logic has a bug — fix before
proceeding to Stage 7.

### Test via API

Approved signal:
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
Expected: approved: true

Rejected — low confidence:
curl -X POST http://localhost:8000/api/risk/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "signal": {
      "symbol": "NHPC",
      "action": "BUY",
      "entry_price": 84.10,
      "target": 85.00,
      "stoploss": 81.00,
      "qty": 9,
      "confidence": 55
    }
  }'
Expected: approved: false, reason mentions Confidence

Rejected — bad R:R:
curl -X POST http://localhost:8000/api/risk/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "signal": {
      "symbol": "SAIL",
      "action": "BUY",
      "entry_price": 130.0,
      "target": 131.0,
      "stoploss": 127.0,
      "qty": 10,
      "confidence": 80
    }
  }'
Expected: approved: false, reason mentions R:R

Evaluate a signal already in DB:
curl -X POST http://localhost:8000/api/risk/evaluate/sig-001

Check risk config:
curl http://localhost:8000/api/risk/config

### Verify DB update
After POST /api/risk/evaluate/{signal_id},
check that signal row in DB has updated
risk_status and reject_reason:
sqlite3 trading.db "SELECT id, risk_status,
  reject_reason FROM signals;"
