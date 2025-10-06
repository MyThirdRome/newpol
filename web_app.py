#!/usr/bin/env python3
"""
Web interface for Polymarket Orderbook Monitor
Real-time dashboard with WebSocket support
"""

from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
from flask_sock import Sock
import json
import threading
import time
from orderbook_monitor import monitor
import config

app = Flask(__name__)
CORS(app)
sock = Sock(app)

# Monitor thread
monitor_thread = None

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """Get monitor status"""
    status = monitor.get_status()
    
    # Add performance metrics
    if monitor.update_latencies:
        avg_latency = sum(monitor.update_latencies) / len(monitor.update_latencies)
        min_latency = min(monitor.update_latencies)
        max_latency = max(monitor.update_latencies)
        status['avg_latency_ms'] = round(avg_latency, 2)
        status['min_latency_ms'] = round(min_latency, 2)
        status['max_latency_ms'] = round(max_latency, 2)
    
    # Add WebSocket connection status
    status['websocket_connected'] = monitor.ws_connection is not None
    
    return jsonify(status)

@app.route('/api/matches')
def api_matches():
    """Get upcoming sports matches"""
    hours = request.args.get('hours', config.DEFAULT_HOURS_AHEAD, type=int)
    matches = monitor.get_upcoming_sports_matches(hours_ahead=hours)
    return jsonify([{
        'event_id': m.event_id,
        'title': m.title,
        'slug': m.slug,
        'start_time': m.start_time,
        'end_time': m.end_time,
        'active': m.active
    } for m in matches])

@app.route('/api/subscribed')
def api_subscribed():
    """Get subscribed markets"""
    return jsonify([{
        'event_id': m.event_id,
        'title': m.title,
        'slug': m.slug,
        'start_time': m.start_time,
        'end_time': m.end_time,
        'active': m.active
    } for m in monitor.subscribed_markets.values()])

@app.route('/api/subscribe', methods=['POST'])
def api_subscribe():
    """Subscribe to a match"""
    data = request.json
    event_id = data.get('event_id')
    event_slug = data.get('event_slug')
    
    # Support subscription by slug (preferred for manual entry)
    if event_slug:
        success = monitor.subscribe_by_slug(event_slug)
        if not success:
            return jsonify({'success': False, 'message': f'Failed to subscribe to {event_slug}'}), 404
        
        # Restart monitor if running
        if monitor.running:
            restart_monitor()
        
        return jsonify({'success': True, 'message': f'Subscribed to {event_slug}'})
    
    # Support subscription by event_id (for auto-discovered matches)
    if not event_id:
        return jsonify({'success': False, 'message': 'Missing event_id or event_slug'}), 400
    
    # Find match
    matches = monitor.get_upcoming_sports_matches(hours_ahead=48)
    match = next((m for m in matches if m.event_id == event_id), None)
    
    if not match:
        return jsonify({'success': False, 'message': 'Match not found'}), 404
    
    monitor.subscribe_to_match(match)
    
    # Restart monitor if running
    if monitor.running:
        restart_monitor()
    
    return jsonify({'success': True, 'message': f'Subscribed to {match.title}'})

@app.route('/api/unsubscribe', methods=['POST'])
def api_unsubscribe():
    """Unsubscribe from a match"""
    data = request.json
    event_id = data.get('event_id')
    
    if not event_id:
        return jsonify({'success': False, 'message': 'Missing event_id'}), 400
    
    monitor.unsubscribe_from_match(event_id)
    
    return jsonify({'success': True, 'message': 'Unsubscribed'})

@app.route('/api/start', methods=['POST'])
def api_start():
    """Start monitoring"""
    global monitor_thread
    
    if monitor.running:
        return jsonify({'success': False, 'message': 'Monitor already running'})
    
    if not monitor.subscribed_markets:
        return jsonify({'success': False, 'message': 'No markets subscribed'})
    
    monitor_thread = threading.Thread(target=monitor.start, daemon=config.DAEMON_THREADS)
    monitor_thread.start()
    
    return jsonify({'success': True, 'message': 'Monitor started'})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop monitoring"""
    monitor.stop()
    return jsonify({'success': True, 'message': 'Monitor stopped'})

@app.route('/api/orderbooks')
def api_orderbooks():
    """Get current orderbook snapshots"""
    return jsonify(monitor.get_current_orderbooks())

@app.route('/api/asks')
def api_asks():
    """Get only asks (sell orders) for both teams with ATL"""
    orderbooks = monitor.get_current_orderbooks()
    atl_records = monitor.get_atl_records()
    
    # Create ATL lookup by market name
    atl_lookup = {}
    for atl in atl_records:
        if atl['side'] == 'ask':
            atl_lookup[atl['market_name']] = {
                'price': atl['price'],
                'size': atl['size'],
                'timestamp': atl['timestamp']
            }
    
    # Filter for moneyline markets only (the main team vs team bets)
    asks = []
    for ob in orderbooks:
        # Only show moneyline (not spread or totals)
        if 'O/U' not in ob['market_name'] and 'Spread' not in ob['market_name']:
            # Extract team name from "Question - Team" format
            parts = ob['market_name'].split(' - ')
            team_name = parts[-1] if len(parts) > 1 else ob['market_name']
            
            # Get ATL for this market
            atl = atl_lookup.get(ob['market_name'], None)
            
            asks.append({
                'team': team_name,
                'current_ask': ob['best_ask'],
                'ask_size': ob['ask_size'],
                'atl_ask': atl['price'] if atl else None,
                'atl_size': atl['size'] if atl else None,
                'atl_timestamp': atl['timestamp'] if atl else None,
                'market_name': ob['market_name']
            })
    
    return jsonify(asks)

@app.route('/api/ath')
def api_ath():
    """Get ATH records"""
    return jsonify(monitor.get_ath_records())

@app.route('/api/atl')
def api_atl():
    """Get ATL records"""
    return jsonify(monitor.get_atl_records())

@app.route('/api/logs')
def api_logs():
    """Get logs"""
    count = request.args.get('count', 100, type=int)
    return jsonify(monitor.get_logs(count))

@app.route('/api/logs/stream')
def api_logs_stream():
    """Stream logs via SSE"""
    def generate():
        last_count = 0
        while True:
            logs = monitor.get_logs()
            current_count = len(logs)
            
            if current_count > last_count:
                new_logs = logs[last_count:]
                for log in new_logs:
                    yield f"data: {json.dumps(log)}\n\n"
                last_count = current_count
            
            time.sleep(config.LOG_STREAM_INTERVAL)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/best-matches')
def api_best_matches():
    """Get best matches (pairs under $1)"""
    return jsonify(monitor.get_best_matches())

@app.route('/api/total-records')
def api_total_records():
    """Get historical total records"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify(monitor.get_total_records(limit))

@sock.route('/ws/orderbooks')
def ws_orderbooks(ws):
    """WebSocket for real-time orderbook updates"""
    while True:
        try:
            orderbooks = monitor.get_current_orderbooks()
            ws.send(json.dumps({
                'type': 'orderbooks',
                'data': orderbooks
            }))
            time.sleep(1)
        except Exception as e:
            break

@sock.route('/ws/ath')
def ws_ath(ws):
    """WebSocket for ATH updates"""
    last_count = 0
    while True:
        try:
            ath_records = monitor.get_ath_records()
            if len(ath_records) > last_count:
                ws.send(json.dumps({
                    'type': 'ath',
                    'data': ath_records
                }))
                last_count = len(ath_records)
            time.sleep(0.5)
        except Exception as e:
            break

def restart_monitor():
    """Restart monitor with new subscriptions"""
    global monitor_thread
    
    if monitor.running:
        monitor.stop()
        time.sleep(1)
    
    monitor_thread = threading.Thread(target=monitor.start, daemon=config.DAEMON_THREADS)
    monitor_thread.start()

if __name__ == '__main__':
    print("🚀 Starting Polymarket Orderbook Monitor Web Interface...")
    print(f"📊 Dashboard: http://localhost:{config.WEB_PORT}")
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=config.WEB_DEBUG, threaded=config.ENABLE_THREADING)
