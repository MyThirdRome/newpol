#!/usr/bin/env python3
"""
Polymarket Sports Orderbook Monitor
Real-time orderbook tracking with ATH detection
"""

import json
import time
import requests
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
import threading
from dataclasses import dataclass, asdict
import logging
import config
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import websockets
from arbitrage_executor import ArbitrageExecutor, ArbitrageOpportunity

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT
)
logger = logging.getLogger('orderbook_monitor')

@dataclass
class OrderbookSnapshot:
    """Orderbook snapshot data"""
    timestamp: float
    market_id: str
    market_name: str
    best_bid: float
    best_ask: float
    bid_size: float
    ask_size: float
    spread: float
    mid_price: float

@dataclass
class ATHRecord:
    """All-Time High record"""
    market_id: str
    market_name: str
    price: float
    size: float
    timestamp: float
    side: str  # 'bid' or 'ask'

@dataclass
class ATLRecord:
    """All-Time Low record"""
    market_id: str
    market_name: str
    price: float
    size: float
    timestamp: float
    side: str  # 'bid' or 'ask'

@dataclass
class BestMatch:
    """Best match when both sides total under $1"""
    event_id: str
    event_title: str
    market_type: str  # 'Moneyline', 'Spread', 'O/U'
    side1_name: str
    side1_price: float
    side2_name: str
    side2_price: float
    total: float
    timestamp: float

@dataclass
class TotalRecord:
    """Historical record of market totals"""
    event_id: str
    event_title: str
    market_type: str
    side1_name: str
    side1_price: float
    side2_name: str
    side2_price: float
    total: float
    timestamp: float
    is_best: bool  # True if under $1

@dataclass
class SportMatch:
    """Sports match information"""
    event_id: str
    title: str
    slug: str
    start_time: str
    end_time: str
    markets: List[Dict[str, Any]]
    active: bool = False

class OrderbookMonitor:
    """Monitor Polymarket orderbooks via WebSocket"""
    
    def __init__(self, arbitrage_executor: Optional[ArbitrageExecutor] = None):
        self.api_base = config.CLOB_API_BASE
        self.data_api = config.DATA_API_BASE
        self.ws_url = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
        
        self.subscribed_markets: Dict[str, SportMatch] = {}
        self.orderbook_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=config.MAX_ORDERBOOK_HISTORY))
        self.ath_records: Dict[str, ATHRecord] = {}
        self.atl_records: Dict[str, ATLRecord] = {}
        self.current_snapshots: Dict[str, OrderbookSnapshot] = {}
        self.token_to_market: Dict[str, str] = {}  # Map token_id to market_name
        self.market_to_token: Dict[str, str] = {}  # Map market_name to token_id
        
        # Best match tracking (pairs under $1)
        self.best_matches: List[BestMatch] = []
        self.total_records: List[TotalRecord] = []
        self.last_totals: Dict[str, float] = {}  # Track last total for each market pair
        
        # Arbitrage executor (optional)
        self.arbitrage_executor = arbitrage_executor
        
        self.running = False
        self.ws_connection = None
        self.logs = deque(maxlen=config.MAX_LOG_ENTRIES)
        
        # Performance tracking
        self.last_update_time = 0
        self.update_latencies = deque(maxlen=100)  # Track last 100 update times
        
        # HTTP session for connection pooling
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=0
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def log(self, message: str, level: str = "INFO"):
        """Add log entry"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        
        if level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
    
    def get_upcoming_sports_matches(self, hours_ahead: int = None) -> List[SportMatch]:
        """Fetch upcoming sports matches"""
        if hours_ahead is None:
            hours_ahead = config.DEFAULT_HOURS_AHEAD
            
        try:
            self.log(f"🔍 Fetching sports matches starting within {hours_ahead} hours...")
            
            # Get all active events (not markets)
            url = f"{self.data_api}/events"
            response = requests.get(url, params={'active': 'true', 'closed': 'false', 'limit': 500}, timeout=config.API_TIMEOUT)
            
            if response.status_code != 200:
                self.log(f"❌ API Error: {response.status_code}", "ERROR")
                return []
            
            events = response.json()
            sports_matches = []
            from datetime import timezone
            now = datetime.now(timezone.utc)
            cutoff = now + timedelta(hours=hours_ahead)
            
            for event in events:
                # Filter for sports events (check slug for sports keywords)
                slug = event.get('slug', '').lower()
                if not any(sport in slug for sport in ['mlb', 'nfl', 'nba', 'nhl', 'soccer', 'football', 'tennis', 'ufc', 'mma']):
                    continue
                
                # Check if starting soon (use creationDate as game time)
                game_time = event.get('creationDate') or event.get('endDate')
                if not game_time:
                    continue
                
                try:
                    game_dt = datetime.fromisoformat(game_time.replace('Z', '+00:00'))
                    if now < game_dt < cutoff:
                        match = SportMatch(
                            event_id=event.get('id'),
                            title=event.get('title', 'Unknown'),
                            slug=event.get('slug', ''),
                            start_time=event.get('startDate', ''),
                            end_time=game_time,
                            markets=event.get('markets', [])
                        )
                        sports_matches.append(match)
                        self.log(f"📅 Found: {match.title} (game at {game_time})")
                except Exception as e:
                    continue
            
            self.log(f"✅ Found {len(sports_matches)} upcoming sports matches")
            return sports_matches
            
        except Exception as e:
            self.log(f"❌ Error fetching matches: {str(e)}", "ERROR")
            return []
    
    def subscribe_by_slug(self, event_slug: str) -> bool:
        """Subscribe to an event by its slug"""
        try:
            self.log(f"🔍 Fetching event: {event_slug}")
            url = f"{self.data_api}/events"
            response = requests.get(url, params={'slug': event_slug}, timeout=config.API_TIMEOUT)
            
            if response.status_code != 200:
                self.log(f"❌ API Error: {response.status_code}", "ERROR")
                return False
            
            events = response.json()
            if not events:
                self.log(f"❌ Event not found: {event_slug}", "ERROR")
                return False
            
            event = events[0]
            match = SportMatch(
                event_id=event.get('id'),
                title=event.get('title', 'Unknown'),
                slug=event.get('slug', ''),
                start_time=event.get('startDate', ''),
                end_time=event.get('endDate', ''),
                markets=event.get('markets', [])
            )
            
            self.subscribe_to_match(match)
            return True
            
        except Exception as e:
            self.log(f"❌ Error subscribing to {event_slug}: {str(e)}", "ERROR")
            return False
    
    def subscribe_to_match(self, match: SportMatch):
        """Subscribe to a match's orderbook"""
        self.subscribed_markets[match.event_id] = match
        match.active = True
        self.log(f"✅ Subscribed to: {match.title}")
    
    def unsubscribe_from_match(self, event_id: str):
        """Unsubscribe from a match"""
        if event_id in self.subscribed_markets:
            match = self.subscribed_markets[event_id]
            match.active = False
            del self.subscribed_markets[event_id]
            self.log(f"❌ Unsubscribed from: {match.title}")
    
    async def connect_websocket(self):
        """Connect to Polymarket WebSocket with automatic reconnection"""
        reconnect_delay = 5
        
        while self.running:
            try:
                self.log("🔌 Connecting to Polymarket WebSocket...")
                
                async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=10) as websocket:
                    self.ws_connection = websocket
                    self.log("✅ WebSocket connected!")
                    
                    # Collect all token IDs
                    all_token_ids = []
                    for event_id, match in self.subscribed_markets.items():
                        for market in match.markets:
                            token_ids_str = market.get('clobTokenIds', '[]')
                            outcomes_str = market.get('outcomes', '[]')
                            try:
                                token_ids = json.loads(token_ids_str) if isinstance(token_ids_str, str) else token_ids_str
                                outcomes = json.loads(outcomes_str) if isinstance(outcomes_str, str) else outcomes_str
                            except:
                                token_ids = []
                                outcomes = []
                            
                            # Map token IDs to market names (bidirectional)
                            for idx, token_id in enumerate(token_ids):
                                if token_id:
                                    outcome_name = outcomes[idx] if idx < len(outcomes) else f"Option {idx+1}"
                                    market_name = f"{market.get('question', 'Unknown')} - {outcome_name}"
                                    self.token_to_market[token_id] = market_name
                                    self.market_to_token[market_name] = token_id
                                    all_token_ids.append(token_id)
                    
                    # Subscribe with correct format: assets_ids and type
                    subscribe_msg = {
                        "assets_ids": all_token_ids,
                        "type": "market"
                    }
                    
                    await websocket.send(json.dumps(subscribe_msg))
                    self.log(f"📡 Subscribed to {len(all_token_ids)} markets via WebSocket")
                    
                    # Listen for messages
                    while self.running:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            await self.process_websocket_message(json.loads(message))
                        except asyncio.TimeoutError:
                            continue
                        except websockets.exceptions.ConnectionClosed as e:
                            self.log(f"⚠️ WebSocket connection closed: {str(e)}", "WARNING")
                            break
                        except Exception as e:
                            self.log(f"❌ Error processing message: {str(e)}", "ERROR")
                            
            except Exception as e:
                self.log(f"❌ WebSocket error: {str(e)}", "ERROR")
            
            # Reconnect if still running
            if self.running:
                self.log(f"🔄 Reconnecting in {reconnect_delay} seconds...")
                await asyncio.sleep(reconnect_delay)
    
    async def process_websocket_message(self, data):
        """Process WebSocket message"""
        try:
            # Handle if data is a list (initial orderbook snapshots)
            if isinstance(data, list):
                self.log(f"📦 Received initial orderbooks: {len(data)} markets")
                for book in data:
                    await self.process_book_message(book)
                return
            
            # Handle price_change messages
            if 'price_changes' in data:
                # This is a price change message - we need to fetch full orderbook
                # For now, just log it
                return
            
            # Handle book messages
            if 'bids' in data and 'asks' in data:
                await self.process_book_message(data)
                return
                
        except Exception as e:
            self.log(f"❌ Error processing WebSocket message: {str(e)}", "ERROR")
    
    async def process_book_message(self, data):
        """Process a book message (full orderbook)"""
        try:
            # Track timing
            process_start = time.time()
            
            # Full orderbook snapshot
            asset_id = data.get('asset_id')
            if not asset_id:
                return
            
            market_name = self.token_to_market.get(asset_id, 'Unknown')
            
            # Parse orderbook
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            
            if bids and asks:
                # Find lowest ask
                min_ask = min(asks, key=lambda x: float(x['price']))
                best_ask = float(min_ask['price'])
                ask_size = float(min_ask['size'])
                
                # Highest bid
                best_bid = float(bids[0]['price']) if bids else 0
                bid_size = float(bids[0]['size']) if bids else 0
                
                spread = best_ask - best_bid
                mid_price = (best_bid + best_ask) / 2
                
                # Create snapshot
                snapshot = OrderbookSnapshot(
                    timestamp=time.time(),
                    market_id=asset_id,
                    market_name=market_name,
                    best_bid=best_bid,
                    best_ask=best_ask,
                    bid_size=bid_size,
                    ask_size=ask_size,
                    spread=spread,
                    mid_price=mid_price
                )
                
                # Store snapshot
                self.current_snapshots[asset_id] = snapshot
                self.orderbook_data[asset_id].append(snapshot)
                
                # Check for ATH and ATL
                self.check_ath(asset_id, market_name, best_bid, bid_size, 'bid')
                self.check_ath(asset_id, market_name, best_ask, ask_size, 'ask')
                self.check_atl(asset_id, market_name, best_bid, bid_size, 'bid')
                self.check_atl(asset_id, market_name, best_ask, ask_size, 'ask')
                
                # Check for best matches (pairs under $1)
                self.check_best_matches()
                
                # Track latency
                process_time = (time.time() - process_start) * 1000
                self.update_latencies.append(process_time)
                
                # Log every update for real-time visibility
                avg_latency = sum(self.update_latencies) / len(self.update_latencies) if self.update_latencies else 0
                self.log(f"📊 {market_name}: Ask ${best_ask:.2f} | Bid ${best_bid:.2f} | Latency: {process_time:.2f}ms | Avg: {avg_latency:.2f}ms")
                
        except Exception as e:
            self.log(f"❌ Error processing book message: {str(e)}", "ERROR")
    
    def fetch_single_orderbook(self, token_id: str, market_name: str) -> tuple:
        """Fetch a single orderbook (for parallel execution)"""
        try:
            request_start = time.time()
            url = f"{self.api_base}/book"
            response = self.session.get(url, params={'token_id': token_id}, timeout=config.API_TIMEOUT)
            request_time = (time.time() - request_start) * 1000
            
            if response.status_code == 200:
                return (token_id, market_name, response.json(), request_time, None)
            else:
                return (token_id, market_name, None, request_time, f"HTTP {response.status_code}")
        except Exception as e:
            return (token_id, market_name, None, 0, str(e))
    
    def poll_orderbooks(self):
        """Poll orderbooks via REST API with parallel requests"""
        try:
            self.log("🔄 Starting orderbook polling (parallel mode)...")
            
            # Create a thread pool for parallel requests
            executor = ThreadPoolExecutor(max_workers=10)
            
            while self.running:
                poll_start = time.time()
                
                # Collect all tasks to execute in parallel
                tasks = []
                for event_id, match in self.subscribed_markets.items():
                    for market in match.markets:
                        # Parse clobTokenIds and outcomes
                        token_ids_str = market.get('clobTokenIds', '[]')
                        outcomes_str = market.get('outcomes', '[]')
                        try:
                            token_ids = json.loads(token_ids_str) if isinstance(token_ids_str, str) else token_ids_str
                            outcomes = json.loads(outcomes_str) if isinstance(outcomes_str, str) else outcomes_str
                        except:
                            token_ids = []
                            outcomes = []
                        
                        # Submit all orderbook fetches in parallel
                        for idx, token_id in enumerate(token_ids):
                            if token_id:
                                outcome_name = outcomes[idx] if idx < len(outcomes) else f"Option {idx+1}"
                                market_name = f"{market.get('question', 'Unknown')} - {outcome_name}"
                                future = executor.submit(self.fetch_single_orderbook, token_id, market_name)
                                tasks.append(future)
                
                # Wait for all requests to complete
                for future in as_completed(tasks):
                    token_id, market_name, data, request_time, error = future.result()
                    
                    if error:
                        self.log(f"⚠️ Error fetching {token_id[:20]}...: {error}", "WARNING")
                    elif data:
                        self.process_orderbook_data(token_id, market_name, data, request_time)
                
                # Calculate total poll cycle time
                poll_time = (time.time() - poll_start) * 1000  # Convert to ms
                self.update_latencies.append(poll_time)
                
                # Log performance every 10 cycles
                if len(self.update_latencies) % 10 == 0:
                    avg_latency = sum(self.update_latencies) / len(self.update_latencies)
                    self.log(f"⚡ Avg poll cycle: {avg_latency:.0f}ms | Last: {poll_time:.0f}ms")
                
                # Sleep between polls
                time.sleep(1)
            
            executor.shutdown(wait=True)
                        
        except Exception as e:
            self.log(f"❌ Polling error: {str(e)}", "ERROR")
    
    def process_orderbook_data(self, token_id: str, market_name: str, data: Dict, request_time: float = 0):
        """Process orderbook data from REST API"""
        try:
            # Parse orderbook
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            
            if not bids or not asks:
                return
            
            # Bids are highest first (best bid is highest price someone will pay)
            best_bid = float(bids[0]['price']) if bids else 0
            bid_size = float(bids[0]['size']) if bids else 0
            
            # Asks are sorted high to low, but we want LOWEST ask (best price to buy)
            # Find the minimum ask price
            min_ask = min(asks, key=lambda x: float(x['price']))
            best_ask = float(min_ask['price'])
            ask_size = float(min_ask['size'])
            
            spread = best_ask - best_bid
            mid_price = (best_bid + best_ask) / 2
            
            # Create snapshot
            snapshot = OrderbookSnapshot(
                timestamp=time.time(),
                market_id=token_id,
                market_name=market_name,
                best_bid=best_bid,
                best_ask=best_ask,
                bid_size=bid_size,
                ask_size=ask_size,
                spread=spread,
                mid_price=mid_price
            )
            
            # Store snapshot
            self.current_snapshots[token_id] = snapshot
            self.orderbook_data[token_id].append(snapshot)
            
            # Check for ATH and ATL
            self.check_ath(token_id, market_name, best_bid, bid_size, 'bid')
            self.check_ath(token_id, market_name, best_ask, ask_size, 'ask')
            self.check_atl(token_id, market_name, best_bid, bid_size, 'bid')
            self.check_atl(token_id, market_name, best_ask, ask_size, 'ask')
            
            # Log update (less verbose)
            if len(self.orderbook_data[token_id]) % 10 == 0:  # Log every 10th update
                self.log(f"📊 {market_name}: Bid ${best_bid:.4f} ({bid_size:.1f}) | Ask ${best_ask:.4f} ({ask_size:.1f}) | Spread ${spread:.4f}")
            
        except Exception as e:
            self.log(f"❌ Error processing orderbook: {str(e)}", "ERROR")
    
    def check_ath(self, market_id: str, market_name: str, price: float, size: float, side: str):
        """Check and update ATH records"""
        key = f"{market_id}_{side}"
        
        if key not in self.ath_records or price > self.ath_records[key].price:
            self.ath_records[key] = ATHRecord(
                market_id=market_id,
                market_name=market_name,
                price=price,
                size=size,
                timestamp=time.time(),
                side=side
            )
            self.log(f"🚀 NEW ATH! {market_name} {side.upper()}: ${price:.4f} (size: {size:.1f})", "WARNING")
    
    def check_atl(self, market_id: str, market_name: str, price: float, size: float, side: str):
        """Check and update ATL (All-Time Low) records"""
        key = f"{market_id}_{side}"
        
        if key not in self.atl_records or price < self.atl_records[key].price:
            self.atl_records[key] = ATLRecord(
                market_id=market_id,
                market_name=market_name,
                price=price,
                size=size,
                timestamp=time.time(),
                side=side
            )
            self.log(f"📉 NEW ATL! {market_name} {side.upper()}: ${price:.4f} (size: {size:.1f})", "WARNING")
    
    def check_best_matches(self):
        """Check for best matches where both sides total under $1"""
        try:
            # Group snapshots by event and market type
            event_markets = defaultdict(lambda: defaultdict(list))
            
            for snapshot in self.current_snapshots.values():
                # Parse market name to extract event and type
                parts = snapshot.market_name.split(' - ')
                if len(parts) < 2:
                    continue
                
                event_name = parts[0]
                outcome = parts[1]
                
                # Determine market type
                market_type = 'Moneyline'
                if 'Spread' in event_name:
                    market_type = 'Spread'
                elif 'O/U' in event_name or 'Over/Under' in event_name:
                    market_type = 'O/U'
                
                event_markets[event_name][market_type].append({
                    'snapshot': snapshot,
                    'outcome': outcome
                })
            
            # Check each event's market types for pairs
            for event_name, market_types in event_markets.items():
                for market_type, outcomes in market_types.items():
                    if len(outcomes) == 2:
                        # We have a pair
                        side1 = outcomes[0]
                        side2 = outcomes[1]
                        
                        total = side1['snapshot'].best_ask + side2['snapshot'].best_ask
                        
                        # Create unique key for this market pair
                        pair_key = f"{event_name}_{market_type}"
                        
                        # Check if total changed
                        if pair_key not in self.last_totals or abs(self.last_totals[pair_key] - total) > 0.001:
                            # Record this total
                            record = TotalRecord(
                                event_id=pair_key,
                                event_title=event_name,
                                market_type=market_type,
                                side1_name=side1['outcome'],
                                side1_price=side1['snapshot'].best_ask,
                                side2_name=side2['outcome'],
                                side2_price=side2['snapshot'].best_ask,
                                total=total,
                                timestamp=time.time(),
                                is_best=(total < 1.0)
                            )
                            self.total_records.append(record)
                            self.last_totals[pair_key] = total
                            
                            # If under $1, it's a best match
                            if total < 1.0:
                                best_match = BestMatch(
                                    event_id=pair_key,
                                    event_title=event_name,
                                    market_type=market_type,
                                    side1_name=side1['outcome'],
                                    side1_price=side1['snapshot'].best_ask,
                                    side2_name=side2['outcome'],
                                    side2_price=side2['snapshot'].best_ask,
                                    total=total,
                                    timestamp=time.time()
                                )
                                self.best_matches.append(best_match)
                                self.log(f"🎯 BEST MATCH! {event_name} {market_type}: ${total:.2f} ({side1['outcome']}: ${side1['snapshot'].best_ask:.2f} + {side2['outcome']}: ${side2['snapshot'].best_ask:.2f})", "WARNING")
                                
                                # Auto-execute arbitrage if enabled
                                if self.arbitrage_executor and self.arbitrage_executor.should_execute(total):
                                    self.execute_arbitrage(
                                        event_name=event_name,
                                        market_type=market_type,
                                        side1_name=side1['outcome'],
                                        side1_price=side1['snapshot'].best_ask,
                                        side1_market_name=side1['snapshot'].market_name,
                                        side2_name=side2['outcome'],
                                        side2_price=side2['snapshot'].best_ask,
                                        side2_market_name=side2['snapshot'].market_name,
                                        total=total
                                    )
        
        except Exception as e:
            self.log(f"❌ Error checking best matches: {str(e)}", "ERROR")
    
    def execute_arbitrage(self, event_name: str, market_type: str, 
                         side1_name: str, side1_price: float, side1_market_name: str,
                         side2_name: str, side2_price: float, side2_market_name: str,
                         total: float):
        """Execute arbitrage trade"""
        try:
            # Get token IDs
            side1_token_id = self.market_to_token.get(side1_market_name)
            side2_token_id = self.market_to_token.get(side2_market_name)
            
            if not side1_token_id or not side2_token_id:
                self.log(f"❌ Cannot execute: Token IDs not found", "ERROR")
                return
            
            # Calculate profit percentage
            profit_percent = ((1.0 - total) / total) * 100
            
            # Create opportunity
            opportunity = ArbitrageOpportunity(
                event_title=event_name,
                market_type=market_type,
                side1_token_id=side1_token_id,
                side1_name=side1_name,
                side1_price=side1_price,
                side2_token_id=side2_token_id,
                side2_name=side2_name,
                side2_price=side2_price,
                total=total,
                profit_percent=profit_percent,
                timestamp=time.time()
            )
            
            # Execute
            self.log(f"🚀 Executing arbitrage: {event_name} ({market_type}) - {profit_percent:.2f}% profit", "WARNING")
            execution = self.arbitrage_executor.execute_arbitrage(opportunity)
            
            if execution.success:
                self.log(f"✅ Arbitrage executed successfully! Orders: {execution.order1_id}, {execution.order2_id}", "WARNING")
            else:
                self.log(f"❌ Arbitrage execution failed: {execution.error}", "ERROR")
                
        except Exception as e:
            self.log(f"❌ Error executing arbitrage: {str(e)}", "ERROR")
    
    def start(self):
        """Start monitoring"""
        self.running = True
        self.log("🚀 Orderbook monitor started!")
        
        # Use WebSocket for real-time updates
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect_websocket())
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        self.log("🛑 Orderbook monitor stopped")
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            'running': self.running,
            'subscribed_markets': len(self.subscribed_markets),
            'ath_records': len(self.ath_records),
            'total_updates': sum(len(data) for data in self.orderbook_data.values())
        }
    
    def get_current_orderbooks(self) -> List[Dict]:
        """Get current orderbook snapshots"""
        return [asdict(snapshot) for snapshot in self.current_snapshots.values()]
    
    def get_ath_records(self) -> List[Dict]:
        """Get all ATH records"""
        return [asdict(record) for record in self.ath_records.values()]
    
    def get_atl_records(self) -> List[Dict]:
        """Get all ATL records"""
        return [asdict(record) for record in self.atl_records.values()]
    
    def get_logs(self, count: int = 100) -> List[Dict]:
        """Get recent logs"""
        return list(self.logs)[-count:]
    
    def get_best_matches(self) -> List[Dict]:
        """Get all best matches (pairs under $1)"""
        return [asdict(match) for match in self.best_matches]
    
    def get_total_records(self, limit: int = 100) -> List[Dict]:
        """Get historical total records"""
        return [asdict(record) for record in self.total_records[-limit:]]

# Global monitor instance
monitor = OrderbookMonitor()

if __name__ == "__main__":
    # Test mode
    print("🚀 Polymarket Orderbook Monitor - Test Mode")
    
    # Fetch upcoming matches
    matches = monitor.get_upcoming_sports_matches(hours_ahead=48)
    
    if matches:
        print(f"\n📅 Found {len(matches)} upcoming matches:")
        for i, match in enumerate(matches[:5], 1):
            print(f"  {i}. {match.title}")
            print(f"     Ends: {match.end_time}")
        
        # Subscribe to first match
        if matches:
            monitor.subscribe_to_match(matches[0])
            print(f"\n✅ Subscribed to: {matches[0].title}")
            print("🔌 Starting WebSocket connection...")
            
            try:
                monitor.start()
            except KeyboardInterrupt:
                print("\n🛑 Stopping monitor...")
                monitor.stop()
    else:
        print("❌ No upcoming sports matches found")
