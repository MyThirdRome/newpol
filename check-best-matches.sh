#!/bin/bash
#
# Check for best matches (pairs under $1)
#

echo "=========================================="
echo "Checking for Best Matches (Under \$1)"
echo "=========================================="
echo ""

# Check if server is running
if ! curl -s http://localhost:5001/api/status > /dev/null 2>&1; then
    echo "❌ Server is not running!"
    echo "Start it with: ./start.sh"
    exit 1
fi

echo "📊 Historical Best Matches:"
echo "------------------------------------------"
curl -s http://localhost:5001/api/best-matches | python3 -c "
import sys, json
try:
    matches = json.load(sys.stdin)
    if matches:
        print(f'Found {len(matches)} best matches:')
        for m in matches:
            print(f\"  🎯 {m['event_title']} ({m['market_type']})\")
            print(f\"     {m['side1_name']}: \${m['side1_price']:.2f}\")
            print(f\"     {m['side2_name']}: \${m['side2_price']:.2f}\")
            print(f\"     Total: \${m['total']:.2f}\")
            print()
    else:
        print('No best matches found yet (none under \$1.00)')
except:
    print('Error reading data')
"

echo ""
echo "📈 Current Market Totals:"
echo "------------------------------------------"
curl -s http://localhost:5001/api/total-records?limit=50 | python3 -c "
import sys, json
from collections import defaultdict

try:
    records = json.load(sys.stdin)
    
    # Get latest record for each market
    latest = {}
    for r in records:
        key = f\"{r['event_title']}_{r['market_type']}\"
        if key not in latest or r['timestamp'] > latest[key]['timestamp']:
            latest[key] = r
    
    # Sort by total (lowest first)
    sorted_records = sorted(latest.values(), key=lambda x: x['total'])
    
    if sorted_records:
        for r in sorted_records[:10]:  # Show top 10
            status = '🎯 BEST' if r['is_best'] else 'Normal'
            print(f\"{r['event_title']} ({r['market_type']})\")
            print(f\"  {r['side1_name']}: \${r['side1_price']:.2f}\")
            print(f\"  {r['side2_name']}: \${r['side2_price']:.2f}\")
            print(f\"  Total: \${r['total']:.2f} [{status}]\")
            print()
    else:
        print('No records yet. Make sure monitor is running.')
except Exception as e:
    print(f'Error: {e}')
"

echo ""
echo "=========================================="
echo "💡 Tips:"
echo "  - Best matches are pairs with total < \$1.00"
echo "  - Current totals around \$1.01-\$1.02 are close!"
echo "  - Keep monitoring for price changes"
echo "=========================================="
