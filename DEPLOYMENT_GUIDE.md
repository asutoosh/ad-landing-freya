# 🚀 DigitalOcean Deployment Guide

Complete guide to deploying your Telegram bot on a DigitalOcean droplet.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Step 1: Create DigitalOcean Droplet](#step-1-create-digitalocean-droplet)
- [Step 2: Initial Server Setup](#step-2-initial-server-setup)
- [Step 3: Deploy the Application](#step-3-deploy-the-application)
- [Step 4: Configure Environment Variables](#step-4-configure-environment-variables)
- [Step 5: Setup Telethon Session](#step-5-setup-telethon-session)
- [Step 6: Start Services](#step-6-start-services)
- [Step 7: Verify Deployment](#step-7-verify-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required:
- ✅ DigitalOcean account ([sign up here](https://www.digitalocean.com/))
- ✅ SSH key configured ([guide](https://docs.digitalocean.com/products/droplets/how-to/add-ssh-keys/))
- ✅ Telegram bot token (from [@BotFather](https://t.me/BotFather))
- ✅ Telegram API credentials (from [my.telegram.org](https://my.telegram.org))
- ✅ GitHub repository access (already set up: `asutoosh/ad-landing-freya`)

### Optional:
- Domain name (for SSL/webhook mode)
- Basic Linux command line knowledge

---

## Step 1: Create DigitalOcean Droplet

### 1.1 Log into DigitalOcean Dashboard
Go to [cloud.digitalocean.com](https://cloud.digitalocean.com/)

### 1.2 Create New Droplet
Click **"Create"** → **"Droplets"**

### 1.3 Choose Configuration

**Image:**
- Distribution: **Ubuntu 22.04 LTS**

**Droplet Size (Choose one):**
- **Basic - $6/month** (1GB RAM, 1 vCPU, 25GB SSD) - Minimum recommended
- **Basic - $12/month** (2GB RAM, 1 vCPU, 50GB SSD) - **Recommended for production**
- **Basic - $18/month** (2GB RAM, 2 vCPU, 60GB SSD) - For high traffic (1000+ users)

**Datacenter Region:**
- Choose closest to your target audience (e.g., New York, Singapore, Frankfurt)

**Authentication:**
- Select your **SSH Key** (recommended)
- Or use password (less secure)

**Hostname:**
- Set a memorable name like `telegram-bot-prod`

### 1.4 Create Droplet
Click **"Create Droplet"** and wait ~60 seconds

### 1.5 Note Your IP Address
Copy the droplet's IP address (e.g., `159.89.123.45`)

---

## Step 2: Initial Server Setup

### 2.1 SSH into Your Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

Replace `YOUR_DROPLET_IP` with your actual IP address.

### 2.2 Run Server Provisioning Script

This script installs all required packages and configures security.

```bash
# Download the setup script
wget https://raw.githubusercontent.com/asutoosh/ad-landing-freya/main/deploy_setup.sh

# Make it executable
chmod +x deploy_setup.sh

# Run the setup
sudo bash deploy_setup.sh
```

**What this script does:**
- ✅ Updates system packages
- ✅ Installs Python 3, pip, git, nginx
- ✅ Creates dedicated `botuser` (non-root)
- ✅ Configures UFW firewall
- ✅ Installs fail2ban for security
- ✅ Sets timezone to UTC

This takes **2-5 minutes**. When done, you'll see:
```
✅ Server setup complete!
```

---

## Step 3: Deploy the Application

### 3.1 Set Up SSH Key for GitHub (If Using Private Repo)

If your repository is private, configure SSH access:

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Display public key
cat ~/.ssh/id_ed25519.pub
```

Copy the output and add it to GitHub:
- Go to GitHub → Settings → SSH and GPG keys → New SSH key
- Paste the key and save

### 3.2 Run Deployment Script

```bash
# Download deployment script
wget https://raw.githubusercontent.com/asutoosh/ad-landing-freya/main/deploy.sh

# Make it executable
chmod +x deploy.sh

# Run deployment
sudo bash deploy.sh
```

**If the script fails at the .env check**, that's expected! Continue to Step 4.

---

## Step 4: Configure Environment Variables

### 4.1 Create .env File

```bash
cd /opt/telegram-bot
sudo -u botuser nano .env
```

### 4.2 Paste Configuration

Copy your `.env` file content from your local machine. **Example:**

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=7123456789:AAHRxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Channel Configuration
CHANNEL_URL=https://t.me/YourChannel
SOURCE_CHANNEL_ID=-1001234567890
TARGET_CHANNEL_ID=-1001234567890

# Admin Configuration
ADMIN_USER_ID=123456789

# Broadcast Settings
BROADCAST_BATCH_SIZE=10

# Message IDs from source channel
MSG_IMMEDIATE_ID=123
MSG_30S_ID=124
MSG_3MIN_ID=125
MSG_2H_ID=0

# Storage
STORAGE_DIR=./storage

# Telethon API Credentials
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+1234567890

# Cache and timing
RESULTS_CACHE_HOURS=1
CLEANUP_DELAY_MINUTES=15
```

### 4.3 Save and Exit
- Press `Ctrl + O` to save
- Press `Enter` to confirm
- Press `Ctrl + X` to exit

### 4.4 Secure the File

```bash
sudo chmod 600 /opt/telegram-bot/.env
sudo chown botuser:botuser /opt/telegram-bot/.env
```

---

## Step 5: Setup Telethon Session

The bot needs to authenticate with Telegram for the `/results` command.

### 5.1 Run Telethon Setup

```bash
cd /opt/telegram-bot
sudo -u botuser /opt/telegram-bot/venv/bin/python setup_telethon.py
```

### 5.2 Follow Prompts

You'll be asked to:
1. Enter your phone number (e.g., `+1234567890`)
2. Enter the code sent to your Telegram app
3. If you have 2FA, enter your password

### 5.3 Verify Session Created

```bash
ls -la /opt/telegram-bot/*.session
```

You should see `user_session.session`

---

## Step 6: Start Services

Now that everything is configured, start the bot services.

### 6.1 Run Deployment Again

```bash
sudo bash /root/deploy.sh
```

This will:
- ✅ Install all Python dependencies
- ✅ Set up systemd services
- ✅ Start bot and worker processes
- ✅ Enable auto-start on boot

### 6.2 Verify Services Running

```bash
sudo systemctl status telegram-bot telegram-worker
```

You should see **"active (running)"** in green for both services.

---

## Step 7: Verify Deployment

### 7.1 Check Logs

**Bot logs:**
```bash
sudo journalctl -u telegram-bot -f
```

**Worker logs:**
```bash
sudo journalctl -u telegram-worker -f
```

Press `Ctrl + C` to exit log view.

### 7.2 Test Bot Functionality

1. Open Telegram and find your bot
2. Send `/start` - You should get a welcome message
3. Send `/help` - Check if commands work
4. Send `/about` - Verify response
5. As admin, test `/stats` command

### 7.3 Test Scheduled Messages

1. Start the bot with `/start`
2. Wait for scheduled messages to arrive (30s, 3min, etc.)
3. Check worker logs to see task processing

---

## Monitoring & Maintenance

### View Live Logs

```bash
# Bot logs
sudo journalctl -u telegram-bot -f

# Worker logs  
sudo journalctl -u telegram-worker -f

# Both together
sudo journalctl -u telegram-bot -u telegram-worker -f
```

### Restart Services

```bash
# Restart bot
sudo systemctl restart telegram-bot

# Restart worker
sudo systemctl restart telegram-worker

# Restart both
sudo systemctl restart telegram-bot telegram-worker
```

### Update Code from GitHub

```bash
cd /opt/telegram-bot
sudo -u botuser git pull
sudo systemctl restart telegram-bot telegram-worker
```

### Check Service Status

```bash
sudo systemctl status telegram-bot telegram-worker
```

### View Error Logs (Last 100 lines)

```bash
sudo journalctl -u telegram-bot -n 100 --no-pager
sudo journalctl -u telegram-worker -n 100 --no-pager
```

### Database Backup

```bash
# Backup database
sudo cp /opt/telegram-bot/storage/bot_database.db /opt/telegram-bot/storage/bot_database_backup_$(date +%Y%m%d).db

# List backups
ls -lh /opt/telegram-bot/storage/*.db
```

### Monitor System Resources

```bash
# CPU, RAM usage
htop

# Disk space
df -h

# Check service memory usage
sudo systemctl status telegram-bot telegram-worker
```

---

## Troubleshooting

### ❌ Bot Not Responding

**Check if services are running:**
```bash
sudo systemctl status telegram-bot telegram-worker
```

**If stopped, start them:**
```bash
sudo systemctl start telegram-bot telegram-worker
```

**Check logs for errors:**
```bash
sudo journalctl -u telegram-bot -n 50
```

### ❌ "Invalid Token" Error

Your bot token is incorrect.

**Fix:**
```bash
sudo nano /opt/telegram-bot/.env
```
Update `TELEGRAM_BOT_TOKEN` with correct value from @BotFather, then:
```bash
sudo systemctl restart telegram-bot
```

### ❌ Database Locked Error

Multiple processes accessing the database.

**Fix:**
```bash
sudo systemctl restart telegram-bot telegram-worker
```

### ❌ Telethon Session Invalid

**Regenerate session:**
```bash
cd /opt/telegram-bot
rm user_session.session*
sudo -u botuser /opt/telegram-bot/venv/bin/python setup_telethon.py
sudo systemctl restart telegram-bot
```

### ❌ Worker Not Sending Messages

**Check worker logs:**
```bash
sudo journalctl -u telegram-worker -f
```

**Common issues:**
- SOURCE_CHANNEL_ID incorrect
- Bot not admin in source channel
- Message IDs don't exist

### ❌ "Permission Denied" Errors

**Fix permissions:**
```bash
sudo chown -R botuser:botuser /opt/telegram-bot
sudo chmod 600 /opt/telegram-bot/.env
```

### ❌ Out of Memory

**Upgrade droplet** or **restart services** to clear memory:
```bash
sudo systemctl restart telegram-bot telegram-worker
```

### ❌ Can't Connect via SSH

**Check firewall:**
```bash
sudo ufw status
sudo ufw allow ssh
```

---

## Advanced: SSL/HTTPS Setup (Optional)

If you have a domain name and want webhook mode instead of polling:

### Configure DNS

Point your domain to your droplet IP:
```
A Record: bot.yourdomain.com → YOUR_DROPLET_IP
```

### Install SSL Certificate

```bash
sudo certbot --nginx -d bot.yourdomain.com
```

### Configure Webhook

Modify your bot code to use webhooks instead of polling (requires additional configuration).

---

## Security Best Practices

✅ **Never commit .env file to GitHub** (already in `.gitignore`)  
✅ **Keep system updated:**
```bash
sudo apt update && sudo apt upgrade -y
```

✅ **Monitor fail2ban:**
```bash
sudo fail2ban-client status sshd
```

✅ **Regular backups** of database and `.env` file  
✅ **Use SSH keys** instead of passwords  
✅ **Change default SSH port** (advanced users)

---

## Quick Command Reference

```bash
# View logs
sudo journalctl -u telegram-bot -f
sudo journalctl -u telegram-worker -f

# Restart services
sudo systemctl restart telegram-bot telegram-worker

# Update code
cd /opt/telegram-bot && sudo -u botuser git pull && sudo systemctl restart telegram-bot telegram-worker

# Check status
sudo systemctl status telegram-bot telegram-worker

# View errors
sudo journalctl -u telegram-bot -n 100 --no-pager | grep ERROR
```

---

## 🎉 Deployment Complete!

Your Telegram bot is now running 24/7 on DigitalOcean!

**Questions or issues?** Check the troubleshooting section or review the logs.

**Repository:** [github.com/asutoosh/ad-landing-freya](https://github.com/asutoosh/ad-landing-freya)
