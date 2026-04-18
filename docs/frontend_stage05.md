## Stage 5 — Dashboard Page

### Run
Backend: uvicorn main:app --reload --port 8000
Frontend: npm run dev

### What to verify

1. 4 stat cards render with correct data from /api/status
2. P&L card is green for positive, red for negative
3. Agent cards show correct status badges and dots
4. Start/Stop buttons call the API and update status
5. Signals strip shows today's signals from DB
6. Empty signals state shows when no signals today
7. Log stream shows last 50 logs from DB on load
8. Log filter dropdowns filter correctly

### Test live updates

Fire a P&L update — TopBar and card update:
curl -X POST http://localhost:8000/api/debug/ws/fire \
  -H "Content-Type: application/json" \
  -d '{"event_type":"pnl_update",
       "payload":{"total_pnl":-120.50,
                  "total_pnl_pct":-2.41,
                  "available_capital":2880}}'
→ P&L card should turn red

Fire a new signal — appears in strip instantly:
curl -X POST http://localhost:8000/api/debug/ws/fire \
  -H "Content-Type: application/json" \
  -d '{"event_type":"new_signal","payload":{}}'

Fire full simulation — watch log stream fill up:
curl -X POST http://localhost:8000/api/debug/ws/simulate

Fire agent status change:
curl -X POST http://localhost:8000/api/debug/ws/fire \
  -H "Content-Type: application/json" \
  -d '{"event_type":"agent_status",
       "payload":{"agent":"market_scanner",
                  "status":"running"}}'
→ Scanner card dot should turn green + pulse

### Test log filter
Fire several events of different agents/levels.
Use the filter dropdowns in the log stream to
confirm filtering works correctly.
