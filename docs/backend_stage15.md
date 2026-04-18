## Stage 15 — APScheduler

### Verify scheduler started
Start backend:
  uvicorn main:app --reload --port 8000

Check scheduler status:
  curl http://localhost:8000/api/scheduler/status

Expected response:
{
  "running": true,
  "job_count": 5,
  "jobs": [
    { "id": "scan_0_0915",
      "name": "Market Scan 09:15 IST",
      "next_run_ist": "2026-04-18 09:15:00 IST" },
    { "id": "scan_1_1100",
      "name": "Market Scan 11:00 IST",
      "next_run_ist": "2026-04-18 11:00:00 IST" },
    { "id": "scan_2_1330",
      "name": "Market Scan 13:30 IST",
      "next_run_ist": "2026-04-18 13:30:00 IST" },
    { "id": "token_refresh",
      "name": "Groww Token Refresh 6:05 AM",
      "next_run_ist": "2026-04-18 06:05:00 IST" },
    { "id": "squareoff_warning",
      "name": "Square-off Warning 15:05",
      "next_run_ist": "2026-04-18 15:05:00 IST" }
  ]
}

### Test pause/resume
curl -X POST http://localhost:8000/api/scheduler/pause
curl http://localhost:8000/api/scheduler/status
  → jobs still listed but next_run_ist = "paused"

curl -X POST http://localhost:8000/api/scheduler/resume
  → jobs resume with next scheduled times

### Test config update reloads schedule
Update scan times via config:
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"scan_times": ["09:15","10:00","13:30"]}'

curl http://localhost:8000/api/scheduler/status
  → Should show new 10:00 job, no 11:00 job

### Test manual trigger
curl -X POST http://localhost:8000/api/scheduler/trigger
  → Immediate scan fires (watch simulator.py)

### Token refresh behavior
At 6:05 AM IST:
  Token is invalidated in memory
  Next Groww API call regenerates it
  If session approval needed: log message
    instructs to visit Groww dashboard

### Scan time configuration
Default: 09:15, 11:00, 13:30 IST
Change via Agent Control → Config → Scan Times
Or directly via POST /api/config
Changes take effect immediately (no restart)
