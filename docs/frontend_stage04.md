## Stage 4 — React Frontend Scaffold

### Setup
cd frontend
npm install

### Run (backend must be running on port 8000)
npm run dev

### Access
http://localhost:5173

### What to verify
1. App loads with dark grid background
2. Sidebar shows all 6 nav items
3. Clicking each nav item changes the page
4. Active nav item highlights in green
5. TopBar shows capital figures from /api/status
6. IST clock in sidebar updates every second
7. Browser console shows "[WS] Connected"
8. Browser console shows "[WS] Server: Connected to..."
9. Mode pill in sidebar shows "PAPER MODE" in amber
10. WS status at bottom of sidebar shows "● Connected" in green

### Test live events
With frontend running, fire a simulation from backend:
curl -X POST http://localhost:8000/api/debug/ws/simulate

Watch the browser console — you should see
the store updating from incoming WS events.

### Test P&L update in TopBar
curl -X POST http://localhost:8000/api/debug/ws/fire \
  -H "Content-Type: application/json" \
  -d '{"event_type":"pnl_update",
       "payload":{"total_pnl":500,
                  "total_pnl_pct":10.0,
                  "available_capital":3500}}'

TopBar P&L should update to +₹500.00 (+10.00%) in green
without a page refresh.
