## Stage 10 — Live Positions Page

### What to verify

1. Page loads at http://localhost:5173/positions
2. Empty state shows when no open positions
3. Margin bar shows correct figures
4. After a paper trade executes, position appears in the table
5. LTP column updates in real time when WebSocket fires ltp_update events
6. P&L recalculates on every LTP update
7. Square-off button shows confirmation dialog
8. Progress bar moves toward target as price rises

### Test LTP update live:
curl -X POST http://localhost:8000/api/debug/ws/fire \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "ltp_update",
    "payload": {
      "symbol": "RVNL",
      "ltp": 310.00,
      "change": 7.68,
      "change_pct": 2.54
    }
  }'

If RVNL is an open position, LTP cell should
update instantly and P&L should recalculate.

### Test with real position:
Trigger a scan and wait for an approved signal.
The position will appear automatically.
Or manually check DB:
sqlite3 trading.db \
  "SELECT id, symbol, entry_price, status
   FROM positions WHERE status='open';"
