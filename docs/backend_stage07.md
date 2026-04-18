## Stage 7 — Groww Client + Token Manager

### Run paper mode tests (no credentials needed)
cd backend
pip install pytest-asyncio
pytest tests/test_groww_client.py -v

All 14 tests should pass (test 15 skipped).

### Run live smoke test (real API call)
Ensure .env has GROWW_API_KEY and GROWW_API_SECRET set.
TEST_LIVE=1 pytest tests/test_groww_client.py::test_live_ltp_smoke -v -s

You should see real NHPC LTP printed.

### Test token generation manually
cd backend
python -c "
import asyncio, os
from dotenv import load_dotenv
load_dotenv()
from services.token_manager import token_manager
async def main():
  token = await token_manager.get_token()
  print('Token:', token[:20], '...')
  print('Expires: next 6AM IST')
asyncio.run(main())
"

### Test LTP via API
Start uvicorn, then add a quick debug route
by calling from Python directly or check
that /api/debug/ws/fire still works normally
(confirms backend starts without import errors).

### Add pytest-asyncio to requirements.txt
pip install pytest-asyncio
Add to requirements.txt: pytest-asyncio

### Environment check
Ensure backend/.env contains:
  GROWW_API_KEY=...      (your trading-bot key)
  GROWW_API_SECRET=...   (your trading-bot secret)
  GROWW_ACCESS_TOKEN=    (leave empty, auto-filled)
  GROWW_BASE_URL=https://api.groww.in
  MODE=paper             (keep paper for now)
