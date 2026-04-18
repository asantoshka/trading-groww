## Stage 12 — Trade History Page

### What to verify

1. Page loads with mock trade data (5 seeded trades)
2. Stats cards show correct win rate (~60%)
3. Monthly P&L bar chart renders with green/red bars
4. Win/Loss donut shows ratio with center % label
5. Filter by symbol: type "NHPC" → filters table
6. Filter by result: "Winners" → only green P&L rows
7. Click any trade row → expands with detail panel
8. Symbol performance table shows ranked symbols
9. Reset button clears all filters

### Expected with seeded data:
- 5 trades total
- 3 winners (SAIL, NHPC, RELIANCE)
- 2 losers (TCS, IDEA)
- Win rate: 60%
- Best trade: NHPC +₹63.60

### Test filter:
Set result=Winners → should show 3 rows
Set mode=live → should show 0 rows
  (all seeded trades are paper mode)
