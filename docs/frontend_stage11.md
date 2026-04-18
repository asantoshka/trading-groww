## Stage 11 — Agent Control Page

### What to verify

1. All 3 agent cards show real status from backend
2. Start/Stop buttons call API and update card
3. Mode toggle shows PAPER in amber
4. Clicking "Switch to LIVE" opens modal
5. Typing anything other than CONFIRM keeps button disabled
6. Typing CONFIRM enables and clicking switches mode — both sidebar pill and toggle update
7. Config panel shows current DB values
8. Editing any field shows sticky save bar
9. Discarding resets to last saved values
10. Saving calls POST /api/config and persists
11. Trigger Scan button fires scan and shows green flash for 3 seconds
12. Log stream shows live events from WebSocket
13. Download button saves .txt file

### Test mode switch:
1. Click "Switch to LIVE"
2. Type "CONFIRM"
3. Click confirm button
4. Sidebar should show "● LIVE MODE" in green
5. All agent mode badges should show "live"
6. Switch back to paper immediately

### Test config save:
1. Change RSI oversold to 38
2. Save bar appears at bottom
3. Click Save
4. Refresh page — value should still be 38

### Test scan trigger:
curl -X GET http://localhost:8000/api/agents
Should show market_scanner status updating while scan runs.
