#!/usr/bin/env python3
"""
Configuration for Polymarket Orderbook Monitor
"""

# API Configuration
CLOB_API_BASE = "https://clob.polymarket.com"
DATA_API_BASE = "https://gamma-api.polymarket.com"
API_TIMEOUT = 10  # seconds

# Match Discovery
DEFAULT_HOURS_AHEAD = 48  # hours
MAX_MARKETS_PER_REQUEST = 100
SPORTS_TAGS = ['Sports', 'NBA', 'NFL', 'Soccer', 'Baseball', 'Hockey', 'Tennis', 'MMA', 'Boxing']

# Data Storage
MAX_ORDERBOOK_HISTORY = 1000  # snapshots per market
MAX_LOG_ENTRIES = 500  # log entries to keep

# Web Interface
WEB_HOST = '0.0.0.0'
WEB_PORT = 5001
WEB_DEBUG = False

# Update Intervals (seconds)
STATUS_UPDATE_INTERVAL = 2
ORDERBOOK_UPDATE_INTERVAL = 1
ATH_UPDATE_INTERVAL = 1
LOG_STREAM_INTERVAL = 0.5

# Logging
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ATH Detection
ATH_PRICE_THRESHOLD = 0.0001  # Minimum price difference to consider new ATH
ATH_FLASH_DURATION = 3000  # milliseconds to show "NEW!" badge

# Performance
ENABLE_THREADING = True
DAEMON_THREADS = True
