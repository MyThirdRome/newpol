# 🎯 Quick Start Guide

## Manual Subscription (Recommended for Now)

Since Polymarket's API structure for live sports events is evolving, the easiest way to monitor a specific game is:

### Step 1: Find the Event on Polymarket
Visit [https://polymarket.com/sports/live](https://polymarket.com/sports/live) and find the game you want to monitor.

Example: `https://polymarket.com/event/mlb-lad-phi-2025-10-06`

### Step 2: Extract the Event Slug
From the URL, copy the event slug (the last part):
```
mlb-lad-phi-2025-10-06
```

### Step 3: Subscribe via API
Use the dashboard or API to subscribe:

**Via Dashboard:**
1. Open [http://localhost:5001](http://localhost:5001)
2. Manually enter the event slug in the subscription field (feature to be added)

**Via API (curl):**
```bash
curl -X POST http://localhost:5001/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"event_slug": "mlb-lad-phi-2025-10-06"}'
```

**Via Python:**
```python
import requests

response = requests.post('http://localhost:5001/api/subscribe', json={
    'event_slug': 'mlb-lad-phi-2025-10-06'
})
print(response.json())
```

### Step 4: Start Monitoring
Click "Start Monitor" in the dashboard or:
```bash
curl -X POST http://localhost:5001/api/start
```

### Step 5: Watch Real-time Data
- **Orderbooks** update every second
- **ATH records** are automatically detected
- **Logs** show all activity

---

## Example: Monitor Today's MLB Game

```bash
# Subscribe to Dodgers vs Phillies
curl -X POST http://localhost:5001/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"event_slug": "mlb-lad-phi-2025-10-06"}'

# Start monitoring
curl -X POST http://localhost:5001/api/start

# Check status
curl http://localhost:5001/api/status

# View orderbooks
curl http://localhost:5001/api/orderbooks

# View ATH records
curl http://localhost:5001/api/ath
```

---

## Troubleshooting

### "Event not found"
- Verify the event slug is correct
- Check that the event is still active on Polymarket
- Try accessing the event directly: `https://polymarket.com/event/YOUR-SLUG`

### "No orderbook updates"
- Ensure the game hasn't started yet (markets close at game time)
- Check that WebSocket is connected (see logs)
- Verify the event has `enableOrderBook: true`

### "WebSocket disconnects"
- Check internet connection
- Polymarket may have rate limits
- Try restarting the monitor

---

## API Endpoints

### Subscribe to Event
```
POST /api/subscribe
Body: {"event_slug": "mlb-lad-phi-2025-10-06"}
```

### Unsubscribe
```
POST /api/unsubscribe
Body: {"event_id": "54395"}
```

### Start/Stop
```
POST /api/start
POST /api/stop
```

### Get Data
```
GET /api/status
GET /api/subscribed
GET /api/orderbooks
GET /api/ath
GET /api/logs
```

---

## Next Steps

We're working on:
- [ ] Auto-discovery of live sports events
- [ ] Manual event slug input in dashboard
- [ ] Better API endpoint detection
- [ ] Historical data export
- [ ] Price charts

For now, manual subscription by slug works perfectly!
