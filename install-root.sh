#!/bin/bash
#
# Polymarket Orderbook Monitor - Root Installation Script
# For installation on servers where you're logged in as root
#

set -e  # Exit on error

echo "=========================================="
echo "Polymarket Orderbook Monitor Installation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script must be run as root"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt-get update -qq

# Install Python 3.11 and pip
echo "🐍 Installing Python 3.11..."
apt-get install -y python3.11 python3.11-venv python3-pip

# Install system dependencies
echo "📚 Installing system dependencies..."
apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3.11-dev

# Create application directory
APP_DIR="/opt/polymarket-orderbook-monitor"
echo "📁 Creating application directory: $APP_DIR"

if [ -d "$APP_DIR" ]; then
    echo "⚠️  Directory already exists. Backing up to ${APP_DIR}.backup"
    mv "$APP_DIR" "${APP_DIR}.backup.$(date +%s)"
fi

mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Clone repository
echo "📥 Downloading application..."
git clone https://github.com/MyThirdRome/newpol.git .

# Create Python virtual environment
echo "🔧 Creating Python virtual environment..."
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Create systemd service file
echo "⚙️  Creating systemd service..."
cat > /etc/systemd/system/polymarket-orderbook.service << EOF
[Unit]
Description=Polymarket Orderbook Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/web_app.py
Restart=always
RestartSec=10
StandardOutput=append:$APP_DIR/logs/app.log
StandardError=append:$APP_DIR/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

# Configure firewall (if ufw is installed)
if command -v ufw &> /dev/null; then
    echo "🔥 Configuring firewall..."
    ufw allow 5001/tcp comment "Polymarket Orderbook Monitor"
fi

# Create start/stop scripts
echo "📝 Creating management scripts..."

cat > start.sh << 'EOFSCRIPT'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
nohup python web_app.py > logs/app.log 2>&1 &
echo $! > app.pid
echo "✅ Polymarket Orderbook Monitor started (PID: $(cat app.pid))"
echo "📊 Dashboard: http://localhost:5001"
EOFSCRIPT

cat > stop.sh << 'EOFSCRIPT'
#!/bin/bash
cd "$(dirname "$0")"
if [ -f app.pid ]; then
    PID=$(cat app.pid)
    kill $PID 2>/dev/null && echo "✅ Stopped process $PID" || echo "⚠️  Process not running"
    rm app.pid
else
    echo "⚠️  No PID file found"
    pkill -f "python.*web_app.py" && echo "✅ Stopped all matching processes"
fi
EOFSCRIPT

cat > status.sh << 'EOFSCRIPT'
#!/bin/bash
cd "$(dirname "$0")"
if [ -f app.pid ]; then
    PID=$(cat app.pid)
    if ps -p $PID > /dev/null; then
        echo "✅ Running (PID: $PID)"
        echo "📊 Dashboard: http://localhost:5001"
    else
        echo "❌ Not running (stale PID file)"
    fi
else
    echo "❌ Not running"
fi
EOFSCRIPT

chmod +x start.sh stop.sh status.sh

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "📁 Installation directory: $APP_DIR"
echo "📊 Dashboard will be available at: http://YOUR_SERVER_IP:5001"
echo ""
echo "🚀 Quick Start:"
echo "   cd $APP_DIR"
echo "   ./start.sh"
echo ""
echo "⚙️  To enable auto-start on boot:"
echo "   systemctl enable polymarket-orderbook"
echo "   systemctl start polymarket-orderbook"
echo ""
echo "📖 View logs:"
echo "   tail -f $APP_DIR/logs/app.log"
echo ""
