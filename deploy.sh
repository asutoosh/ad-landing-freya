#!/bin/bash

#############################################################################
# Deployment Script for Telegram Bot
# Deploys/updates the bot on DigitalOcean droplet
#
# Usage: sudo bash deploy.sh
#############################################################################

set -e  # Exit on any error

echo "============================================"
echo "🚀 Deploying Telegram Bot"
echo "============================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

APP_DIR="/opt/telegram-bot"
GITHUB_REPO="git@github.com:asutoosh/ad-landing-freya.git"

# Clone or update repository
echo "📥 Getting latest code from GitHub..."
if [ -d "$APP_DIR/.git" ]; then
    echo "Repository exists, pulling latest changes..."
    cd $APP_DIR
    sudo -u botuser git pull
else
    echo "Cloning repository..."
    rm -rf $APP_DIR
    sudo -u botuser git clone $GITHUB_REPO $APP_DIR
    cd $APP_DIR
fi

# Create storage directory
echo "📁 Creating storage directory..."
sudo -u botuser mkdir -p $APP_DIR/storage

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "$APP_DIR/venv" ]; then
    sudo -u botuser python3 -m venv $APP_DIR/venv
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
sudo -u botuser $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u botuser $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

# Check if .env file exists
if [ ! -f "$APP_DIR/.env" ]; then
    echo "⚠️ WARNING: .env file not found!"
    echo "Please create $APP_DIR/.env with your configuration"
    echo "You can copy from .env.example and fill in your values"
    exit 1
fi

# Set proper permissions
echo "🔒 Setting permissions..."
chown -R botuser:botuser $APP_DIR
chmod 600 $APP_DIR/.env  # Protect sensitive credentials
chmod +x $APP_DIR/bot.py
chmod +x $APP_DIR/worker.py

# Copy systemd service files
echo "⚙️ Installing systemd services..."
cp $APP_DIR/telegram-bot.service /etc/systemd/system/
cp $APP_DIR/telegram-worker.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable and restart services
echo "🔄 Starting services..."
systemctl enable telegram-bot
systemctl enable telegram-worker
systemctl restart telegram-bot
systemctl restart telegram-worker

# Wait a moment for services to start
sleep 3

# Check service status
echo ""
echo "============================================"
echo "📊 Service Status"
echo "============================================"
systemctl status telegram-bot --no-pager -l || true
echo ""
systemctl status telegram-worker --no-pager -l || true

echo ""
echo "============================================"
echo "✅ Deployment complete!"
echo "============================================"
echo ""
echo "Useful commands:"
echo "  View bot logs:    sudo journalctl -u telegram-bot -f"
echo "  View worker logs: sudo journalctl -u telegram-worker -f"
echo "  Restart bot:      sudo systemctl restart telegram-bot"
echo "  Restart worker:   sudo systemctl restart telegram-worker"
echo "  Check status:     sudo systemctl status telegram-bot telegram-worker"
echo ""
