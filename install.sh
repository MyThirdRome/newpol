#!/bin/bash
#
# Polymarket Orderbook Monitor - Installation Script
# Installs all dependencies and sets up the application on a fresh Ubuntu/Debian server
#

set -e  # Exit on error

echo "=========================================="
echo "Polymarket Orderbook Monitor Installation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  Please do not run as root. Run as a regular user with sudo privileges."
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -qq

# Install Python 3.11 and pip
echo "🐍 Installing Python 3.11..."
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# Install system dependencies
echo "📚 Installing system dependencies..."
sudo apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3.11-dev

# Create application directory
APP_DIR="$HOME/polymarket-orderbook-monitor"
echo "📁 Creating application directory: $APP_DIR"

if [ -d "$APP_DIR" ]; then
    echo "⚠️  Directory already exists. Backing up to ${APP_DIR}.backup"
    mv "$APP_DIR" "${APP_DIR}.backup.$(date +%s)"
fi

mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Clone repository (or copy files if already present)
if [ -f "/tmp/orderbook-monitor.tar.gz" ]; then
    echo "📦 Extracting from archive..."
    tar -xzf /tmp/orderbook-monitor.tar.gz -C "$APP_DIR"
else
    echo "📥 Cloning repository..."
    # If running from the repo directory, copy files
    if [ -f "$OLDPWD/orderbook_monitor.py" ]; then
        cp -r "$OLDPWD"/* "$APP_DIR/"
    else
        echo "⚠️  Please run this script from the orderbook monitor directory"
        echo "   or place files in /tmp/orderbook-monitor.tar.gz"
        exit 1
    fi
fi

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
SERVICE_FILE="/tmp/polymarket-orderbook.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Polymarket Orderbook Monitor
After=network.target

[Service]
Type=simple
User=$USER
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

sudo mv "$SERVICE_FILE" /etc/systemd/system/polymarket-orderbook.service
sudo systemctl daemon-reload

# Configure firewall (if ufw is installed)
if command -v ufw &> /dev/null; then
    echo "🔥 Configuring firewall..."
    sudo ufw allow 5001/tcp comment "Polymarket Orderbook Monitor"
fi

# Create start/stop scripts
echo "📝 Creating management scripts..."

cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
nohup python web_app.py > logs/app.log 2>&1 &
echo $! > app.pid
echo "✅ Polymarket Orderbook Monitor started (PID: $(cat app.pid))"
echo "📊 Dashboard: http://localhost:5001"
EOF

cat > stop.sh << 'EOF'
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
EOF

cat > status.sh << 'EOF'
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
EOF

chmod +x start.sh stop.sh status.sh

# Create README for the installation
cat > INSTALL_README.md << 'EOF'
# Polymarket Orderbook Monitor - Installation Complete

## Quick Start

### Manual Start/Stop
```bash
# Start the monitor
./start.sh

# Check status
./status.sh

# Stop the monitor
./stop.sh
```

### Using systemd (recommended for production)
```bash
# Start service
sudo systemctl start polymarket-orderbook

# Enable auto-start on boot
sudo systemctl enable polymarket-orderbook

# Check status
sudo systemctl status polymarket-orderbook

# View logs
sudo journalctl -u polymarket-orderbook -f

# Stop service
sudo systemctl stop polymarket-orderbook
```

## Access Dashboard

Open your browser and navigate to:
- Local: http://localhost:5001
- Remote: http://YOUR_SERVER_IP:5001

## Configuration

Edit `config.py` to customize:
- API endpoints
- Update intervals
- Port number
- Logging settings

## Subscribe to Matches

1. Open the dashboard
2. Use the API to subscribe to a match by slug:
```bash
curl -X POST http://localhost:5001/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"event_slug": "mlb-lad-phi-2025-10-06"}'
```

3. Click "Start Monitor" in the dashboard

## Logs

- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Systemd logs: `sudo journalctl -u polymarket-orderbook`

## Troubleshooting

### Port already in use
```bash
# Find process using port 5001
sudo lsof -i :5001

# Kill the process
sudo kill -9 <PID>
```

### Permission issues
```bash
# Ensure correct ownership
sudo chown -R $USER:$USER ~/polymarket-orderbook-monitor
```

### Python dependencies
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

## Updating

```bash
cd ~/polymarket-orderbook-monitor
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
./stop.sh
./start.sh
```

## Uninstall

```bash
# Stop service
sudo systemctl stop polymarket-orderbook
sudo systemctl disable polymarket-orderbook

# Remove service file
sudo rm /etc/systemd/system/polymarket-orderbook.service
sudo systemctl daemon-reload

# Remove application
rm -rf ~/polymarket-orderbook-monitor
```
EOF

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "📁 Installation directory: $APP_DIR"
echo "📊 Dashboard will be available at: http://localhost:5001"
echo ""
echo "🚀 Quick Start:"
echo "   cd $APP_DIR"
echo "   ./start.sh"
echo ""
echo "📖 For more information, see: $APP_DIR/INSTALL_README.md"
echo ""
echo "⚙️  To enable auto-start on boot:"
echo "   sudo systemctl enable polymarket-orderbook"
echo "   sudo systemctl start polymarket-orderbook"
echo ""
