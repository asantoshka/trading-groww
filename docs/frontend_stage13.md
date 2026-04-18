## Stage 13 — Signals Page

### What to verify

1. Page loads with today's 3 mock signals
2. SignalChips show confidence bars correctly
3. Click a chip → expands SignalDetail below it
4. SignalDetail shows R:R calculation
5. Analytics strip shows 3 total, 67% approved
6. Rejection reasons bar shows one rejection
7. All signals table shows all 3 with filters
8. Mode=paper shows Inject Signal button
9. Inject form appears with animation
10. Fill form with invalid data → error message
11. Valid inject → success + form closes

### Test manual inject:
Fill form:
  Symbol: RVNL
  Action: BUY
  Entry: 302.00
  Target: 308.00
  Stoploss: 298.00
  Qty: 6

Click Inject Signal.
Expected:
  Success message appears
  New signal appears at top of Today's Signals
  Signal chip shows "pending" risk status
  (Risk gate evaluates on backend)

### Test WebSocket new signal:
curl -X POST http://localhost:8000/api/debug/ws/fire \
  -H "Content-Type: application/json" \
  -d '{"event_type":"new_signal","payload":{}}'

New signal chip should appear at top of
Today's Signals in real time.

### Test filter:
All Signals table → Status=Rejected
Should show only the 1 rejected mock signal
with its rejection reason visible.
