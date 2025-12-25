#!/bin/bash

#############################################################################
# DigitalOcean Droplet Initial Setup Script
# Run this on a fresh Ubuntu 22.04 droplet
#
# Usage: sudo bash deploy_setup.sh
#############################################################################

set -e  # Exit on any error

echo "============================================"
echo "🚀 Telegram Bot Server Setup"
echo "============================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Update system packages
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install required packages
echo "📦 Installing required packages..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    ufw \
    fail2ban \
    certbot \
    python3-certbot-nginx \
    htop \
    curl \
    wget

# Create application user (non-root)
echo "👤 Creating application user..."
if ! id -u botuser > /dev/null 2>&1; then
    useradd -m -s /bin/bash botuser
    echo "✅ User 'botuser' created"
else
    echo "ℹ️ User 'botuser' already exists"
fi

# Create application directory
echo "📁 Creating application directory..."
mkdir -p /opt/telegram-bot
chown botuser:botuser /opt/telegram-bot

# Configure UFW Firewall
echo "🔥 Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
echo "y" | ufw enable
echo "✅ Firewall configured"

# Configure fail2ban
echo "🛡️ Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban
echo "✅ fail2ban configured"

# Set timezone to UTC
echo "🕐 Setting timezone to UTC..."
timedatectl set-timezone UTC

echo ""
echo "============================================"
echo "✅ Server setup complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Clone your repository to /opt/telegram-bot"
echo "2. Run the deploy.sh script as root"
echo ""
