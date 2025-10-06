# 📊 Polymarket Orderbook Monitor

Real-time sports orderbook tracking with ATH (All-Time High) detection for Polymarket.

## 🌟 Features

### Core Features
- ✅ **Real-time Orderbook Monitoring** via WebSocket
- ✅ **Sports Match Discovery** - Auto-find upcoming sports events
- ✅ **ATH Tracking** - Automatically detect and highlight all-time highs
- ✅ **Live Logs** - Real-time activity logs with toggle on/off
- ✅ **Beautiful Dashboard** - Modern, responsive web interface
- ✅ **Start/Stop Controls** - Easy monitor management
- ✅ **Multi-Market Support** - Subscribe to multiple matches simultaneously

### Dashboard Features
- 📊 Live orderbook updates (bid/ask/spread/mid-price)
- 🚀 ATH records with timestamps
- 📝 Real-time logs (can be toggled)
- 🏆 Upcoming sports matches list
- ⚡ WebSocket-powered real-time updates
- 📈 Statistics dashboard

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd /workspaces/polymarket-orderbook-monitor
pip install -r requirements.txt
```

### 2. Start the Web Interface
```bash
python web_app.py
```

### 3. Open Dashboard
```
http://localhost:5001
```

---

## 🎮 How to Use

### Step 1: Browse Upcoming Matches
- Dashboard shows upcoming sports matches (next 48 hours)
- Click on any match to subscribe

### Step 2: Subscribe to Matches
- Click matches you want to monitor
- Subscribed matches turn green
- Can subscribe to multiple matches

### Step 3: Start Monitoring
- Click **"▶ Start Monitor"** button
- WebSocket connects to Polymarket
- Real-time orderbook updates begin

### Step 4: Watch the Data
- **Live Orderbooks** - See bid/ask prices updating in real-time
- **ATH Records** - New all-time highs are automatically detected
- **Real-time Logs** - Watch activity (toggle on/off)

### Step 5: Stop When Done
- Click **"⏹ Stop Monitor"** button
- WebSocket disconnects
- Data is preserved

---

## 📊 Dashboard Sections

### 1. Statistics Bar
- **Status** - Running/Stopped
- **Subscribed Markets** - Number of active subscriptions
- **ATH Records** - Total all-time highs found
- **Total Updates** - Orderbook updates received

### 2. Upcoming Sports Matches
- Shows matches starting within 48 hours
- Click to subscribe/unsubscribe
- Green = subscribed, White = available

### 3. Live Orderbooks
- Real-time bid/ask prices
- Order sizes
- Spread calculation
- Mid-price
- Updates every second

### 4. ATH Records
- All-time high prices detected
- Side (BID/ASK)
- Price and size
- Timestamp
- **NEW!** badge flashes on new ATH

### 5. Real-time Logs
- Activity feed
- Color-coded by level (INFO/WARNING/ERROR)
- Toggle on/off with checkbox
- Auto-scrolls to latest

---

## 🔧 API Endpoints

### Status & Control
```
GET  /api/status          # Monitor status
GET  /api/matches         # Get upcoming matches
GET  /api/subscribed      # Get subscribed markets
POST /api/subscribe       # Subscribe to match
POST /api/unsubscribe     # Unsubscribe from match
POST /api/start           # Start monitoring
POST /api/stop            # Stop monitoring
```

### Data
```
GET  /api/orderbooks      # Current orderbook snapshots
GET  /api/ath             # ATH records
GET  /api/logs            # Recent logs
GET  /api/logs/stream     # Stream logs (SSE)
```

### WebSocket
```
WS   /ws/orderbooks       # Real-time orderbook updates
WS   /ws/ath              # Real-time ATH updates
```

---

## 🎯 Use Cases

### 1. Market Research
- Monitor orderbook depth
- Track price movements
- Identify liquidity patterns

### 2. ATH Tracking
- Find peak prices
- Detect unusual activity
- Historical price records

### 3. Sports Betting Analysis
- Pre-game orderbook analysis
- Live game price tracking
- Market sentiment monitoring

### 4. Data Collection
- Collect orderbook snapshots
- Build historical database
- Analyze market behavior

---

## 🏗️ Architecture

### Backend (`orderbook_monitor.py`)
- WebSocket client for Polymarket
- Orderbook data processing
- ATH detection algorithm
- Match discovery system
- Thread-safe data storage

### Web API (`web_app.py`)
- Flask REST API
- Server-Sent Events for logs
- WebSocket endpoints
- Monitor control

### Frontend (`templates/dashboard.html`)
- Real-time dashboard
- WebSocket client
- Auto-updating UI
- Responsive design

---

## 📈 Data Flow

```
Polymarket WebSocket
        ↓
OrderbookMonitor
        ↓
   Data Processing
        ↓
   ATH Detection
        ↓
    Web API
        ↓
   Dashboard
```

---

## 🎨 Technologies Used

### Backend
- **Python 3.11+**
- **Flask** - Web framework
- **WebSockets** - Real-time communication
- **Threading** - Concurrent processing
- **Requests** - HTTP client

### Frontend
- **HTML5/CSS3** - Modern UI
- **JavaScript** - Real-time updates
- **EventSource** - Server-Sent Events
- **WebSocket** - Bi-directional communication

### Data
- **Polymarket CLOB API** - Market data
- **Polymarket Data API** - Match information
- **WebSocket API** - Real-time orderbooks

---

## 🔒 Features Comparison

| Feature | This Bot | Trading Bot |
|---------|----------|-------------|
| **Purpose** | Monitor & Track | Trade Execution |
| **WebSocket** | ✅ Yes | ❌ No |
| **Real-time Logs** | ✅ Toggle On/Off | ✅ Always On |
| **ATH Tracking** | ✅ Yes | ❌ No |
| **Auto-Subscribe** | ✅ Sports Matches | ❌ Manual |
| **Orderbook View** | ✅ Full Depth | ❌ No |
| **Trading** | ❌ No | ✅ Yes |

---

## 💡 Tips

### Performance
- Subscribe to 3-5 matches max for best performance
- Toggle logs off if not needed
- Refresh matches periodically

### Best Practices
- Start monitoring before game time
- Watch for ATH spikes during key moments
- Use logs to debug issues

### Troubleshooting
- **No matches found?** - Try increasing hours (48-72)
- **WebSocket disconnects?** - Check internet connection
- **No orderbook updates?** - Verify markets are active

---

## 🚀 Future Enhancements

Possible additions:
- [ ] Historical data export
- [ ] Price charts/graphs
- [ ] Email/SMS alerts on ATH
- [ ] Multiple sport filters
- [ ] Custom ATH thresholds
- [ ] Database storage
- [ ] API rate limiting
- [ ] Authentication system

---

## 📞 Support

For issues or questions:
1. Check logs in dashboard
2. Verify WebSocket connection
3. Ensure markets are active
4. Check Polymarket API status

---

## 🎉 Enjoy!

You now have a powerful orderbook monitoring system for Polymarket sports markets!

**Dashboard:** http://localhost:5001

**Happy Monitoring!** 📊🚀
