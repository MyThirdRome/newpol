# Deployment Guide

## Fresh Server Installation

This guide will help you deploy the Polymarket Orderbook Monitor on a fresh Ubuntu/Debian server.

### Prerequisites

- Ubuntu 20.04+ or Debian 11+ server
- User account with sudo privileges
- Internet connection

### One-Command Installation

```bash
curl -sSL https://raw.githubusercontent.com/MyThirdRome/newpol/main/install.sh | bash
```

### Manual Installation

1. **Clone the repository:**
```bash
cd ~
git clone https://github.com/MyThirdRome/newpol.git
cd newpol
```

2. **Run the installation script:**
```bash
chmod +x install.sh
./install.sh
```

3. **Start the application:**
```bash
cd ~/polymarket-orderbook-monitor
./start.sh
```

### What Gets Installed

The installation script will:
- ✅ Install Python 3.11 and pip
- ✅ Install system dependencies (git, curl, build tools)
- ✅ Create a Python virtual environment
- ✅ Install all Python packages from requirements.txt
- ✅ Create systemd service for auto-start
- ✅ Configure firewall (if ufw is installed)
- ✅ Create management scripts (start.sh, stop.sh, status.sh)
- ✅ Set up logging directory

### Post-Installation

1. **Access the dashboard:**
   - Open browser: `http://YOUR_SERVER_IP:5001`

2. **Subscribe to a match:**
```bash
curl -X POST http://localhost:5001/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"event_slug": "mlb-lad-phi-2025-10-06"}'
```

3. **Start monitoring:**
   - Click "▶ Start Monitor" in the dashboard
   - Or use API: `curl -X POST http://localhost:5001/api/start`

### Production Deployment

For production use, enable the systemd service:

```bash
sudo systemctl enable polymarket-orderbook
sudo systemctl start polymarket-orderbook
```

This ensures the monitor:
- Starts automatically on server boot
- Restarts automatically if it crashes
- Logs to systemd journal

### Monitoring

**Check status:**
```bash
./status.sh
# or
sudo systemctl status polymarket-orderbook
```

**View logs:**
```bash
tail -f logs/app.log
# or
sudo journalctl -u polymarket-orderbook -f
```

### Security Considerations

1. **Firewall:** The script opens port 5001. Restrict access if needed:
```bash
sudo ufw allow from YOUR_IP to any port 5001
```

2. **Reverse Proxy:** For production, use nginx as a reverse proxy:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

3. **SSL/TLS:** Use Let's Encrypt for HTTPS:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Troubleshooting

**Port already in use:**
```bash
sudo lsof -i :5001
sudo kill -9 <PID>
```

**Python version issues:**
```bash
python3.11 --version
# If not found, install:
sudo apt-get install python3.11 python3.11-venv
```

**Permission denied:**
```bash
sudo chown -R $USER:$USER ~/polymarket-orderbook-monitor
chmod +x ~/polymarket-orderbook-monitor/*.sh
```

### Updating

```bash
cd ~/polymarket-orderbook-monitor
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
./stop.sh && ./start.sh
```

### Uninstalling

```bash
sudo systemctl stop polymarket-orderbook
sudo systemctl disable polymarket-orderbook
sudo rm /etc/systemd/system/polymarket-orderbook.service
rm -rf ~/polymarket-orderbook-monitor
```

## Docker Deployment (Alternative)

Coming soon...

## Support

For issues or questions, please open an issue on GitHub.
