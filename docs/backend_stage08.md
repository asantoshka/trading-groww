## Stage 8 — Market Scanner

### Install new dependencies
pip install pandas pandas-ta numpy

### Run tests (no API calls)
pytest tests/test_market_scanner.py -v

### Run real scan
uvicorn main:app --reload --port 8000

# Terminal 2 — watch events
python simulator.py

# Terminal 3 — trigger scan
curl -X POST http://localhost:8000/api/agents/scanner/trigger

### Expected log sequence in simulator:
[SCANNER] Market scan started
[SCANNER] Scanning 7 symbols: ...
[SCANNER] Live prices — NHPC: ₹XX...
[SCANNER] Computing technical indicators...
[SCANNER] NHPC — RSI: XX.X | MACD: bullish/bearish
[SCANNER] Sending indicators to Claude...
[RISK]    Evaluating: BUY NHPC @ ₹XX qty=X
[RISK]    APPROVED/REJECTED — ...
[SCANNER] Signal approved/rejected: ...

### Check DB after scan
sqlite3 trading.db \
  "SELECT symbol, action, entry_price,
          risk_status, confidence, rsi
   FROM signals
   ORDER BY created_at DESC LIMIT 3;"

### Switch to Bedrock when quota approved
Change in .env:
  LLM_PROVIDER=bedrock
Restart uvicorn. Everything else identical.
