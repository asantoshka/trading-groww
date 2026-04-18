## Stage 14 — Paper Trading Page

### What to verify

1. Page loads with paper account summary
2. Stats show 60% win rate from seeded data
3. Performance breakdown metrics correct
4. "No paper trades yet" empty state with tip
   (seeded trades may show depending on mode)
5. Force Scan button triggers scan + green flash
6. Export CSV downloads file with trade data
7. Reset modal appears with confirmation
8. Getting started tips show when no trades

### With seeded paper trades:
Total return = (162/5000 × 100) = +3.24%
Win rate = 60%
Avg win = +₹65.70
Avg loss = -₹31.25
Profit factor = 65.70/31.25 = 2.10x

### Test export:
Click Export CSV → file downloads as:
paper-trades-2026-04-17.csv
Open in Excel/Numbers — should have
5 rows of trade data with all columns.

### Test force scan:
Click Force Scan → button shows "Scanning..."
→ green "✓ Scan Triggered" for 3 seconds
Open Dashboard to watch the log stream.
