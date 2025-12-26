# 🚀 Telegram Bot Deployment Reference
## Complete Deployment Record - December 25, 2025

This document contains the **actual deployment steps** used to successfully deploy the Telegram bot on DigitalOcean, including all troubleshooting steps encountered and resolved.

---

## 📋 Server Specifications

**Provider:** DigitalOcean  
**Hostname:** `tg-ad-landing-bot`  
**IP Address:** `138.68.57.241`  
**OS:** Ubuntu 24.04.3 LTS  
**Kernel:** Linux 6.8.0-71-generic x86_64  
**RAM:** 1GB (Basic Droplet - $6/month)  
**Storage:** 23.17GB SSD  

---

## 🔐 Initial Access

### 1. SSH Connection
```bash
ssh root@138.68.57.241
```

### 2. Password Change
Upon first login, Ubuntu forced a password change:
```
You are required to change your password immediately (administrator enforced).
Current password: [entered]
New password: [new password]
Retype new password: [confirmed]
```

---

## 📦 Step 1: Server Provisioning

### Download and Run Setup Script
```bash
wget https://raw.githubusercontent.com/asutoosh/ad-landing-freya/main/deploy_setup.sh
chmod +x deploy_setup.sh
sudo bash deploy_setup.sh
```

### Issue Encountered: SSH Configuration Prompt
During package updates, the system prompted:
```
Configuring openssh-server
A new version (/tmp/tmp.RMdSFR0003) or configuration file /etc/ssh/sshd_config is available,
but the version installed currently has been locally modified.

What do you want to do about modified configuration file sshd_config?

  install the package maintainer's version
  keep the locally-installed version (currently highlighted)
  show the differences between the versions
  show a side-by-side difference between the versions
  show a 3-way difference between available versions
  do a 3-way merge between available versions
  start a new shell to examine the situation
```

**Solution:** Selected **"keep the locally-installed version"** (pressed Enter)

**Reason:** DigitalOcean's SSH configuration is already optimized and working. Keeping it prevents SSH access issues.

### Setup Script Output
```bash
✅ Server setup complete!

Next steps:
1. Clone your repository to /opt/telegram-bot
2. Run the deploy.sh script as root
```

---

## 📥 Step 2: Clone Repository

### Issue Encountered: Permission Error
First attempt with deploy.sh failed:
```bash
wget https://raw.githubusercontent.com/asutoosh/ad-landing-freya/main/deploy.sh
chmod +x deploy.sh
sudo bash deploy.sh
```

**Error:**
```
fatal: could not create work tree dir '/opt/telegram-bot': Permission denied
```

### Solution: Manual Directory Setup
```bash
# Create directory with proper ownership
sudo mkdir -p /opt/telegram-bot
sudo chown -R botuser:botuser /opt/telegram-bot

# Clone repository as botuser
sudo -u botuser git clone https://github.com/asutoosh/ad-landing-freya.git /opt/telegram-bot

# Verify files
ls -la /opt/telegram-bot
```

**Output:**
```
total 80
drwxr-xr-x 5 botuser botuser  4096 Dec 25 22:16 .
drwxr-xr-x 3 root    root     4096 Dec 25 22:16 ..
-rw-r--r-- 1 botuser botuser 22901 Dec 25 22:16 COMPLETE_SYSTEM_DOCUMENTATION.md
-rw-r--r-- 1 botuser botuser 18789 Dec 25 22:16 DEPLOYMENT_GUIDE.md
-rw-r--r-- 1 botuser botuser 24614 Dec 25 22:16 bot.py
-rw-r--r-- 1 botuser botuser 10664 Dec 25 22:16 database.py
-rw-r--r-- 1 botuser botuser  3222 Dec 25 22:16 deploy.sh
-rw-r--r-- 1 botuser botuser  2084 Dec 25 22:16 deploy_setup.sh
-rw-r--r-- 1 botuser botuser   161 Dec 25 22:16 requirements.txt
...
```

---

## ⚙️ Step 3: Configure Environment Variables

### Create .env File
```bash
sudo nano /opt/telegram-bot/.env
```

### Environment Configuration
```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=7123456789:AAHRxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Channel Configuration
CHANNEL_URL=https://t.me/+wazirforexalerts
SOURCE_CHANNEL_ID=-1003232273065
TARGET_CHANNEL_ID=-1003232273065

# Admin Configuration
ADMIN_USER_ID=1977988206

# Broadcast Settings
BROADCAST_BATCH_SIZE=10

# Message IDs from source channel
MSG_IMMEDIATE_ID=124
MSG_30S_ID=127
MSG_3MIN_ID=128
MSG_2H_ID=0

# Storage
STORAGE_DIR=./storage

# Telethon API Credentials
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+917847041321

# Cache and timing
RESULTS_CACHE_HOURS=1
CLEANUP_DELAY_MINUTES=15
```

### Secure the File
```bash
sudo chmod 600 /opt/telegram-bot/.env
sudo chown botuser:botuser /opt/telegram-bot/.env
```

---

## 🚀 Step 4: Deploy Application

### Run Deployment Script
```bash
cd /opt/telegram-bot
sudo bash deploy.sh
```

### Deployment Script Actions
```
📥 Getting latest code from GitHub...
Repository exists, pulling latest changes...
Already up to date.

📁 Creating storage directory...

🐍 Setting up Python virtual environment...

📦 Installing Python dependencies...
Successfully installed:
- python-telegram-bot==21.9
- python-dotenv==1.0.1
- telethon==1.36.0
- cryptg==0.4.0
[+ all dependencies]

🔒 Setting permissions...

⚙️ Installing systemd services...

🔄 Starting services...
Created symlink /etc/systemd/system/multi-user.target.wants/telegram-bot.service
Created symlink /etc/systemd/system/multi-user.target.wants/telegram-worker.service
```

### Service Status After Initial Start
```
● telegram-bot.service - Telegram Ad Bot - Main Bot Process
     Loaded: loaded (/etc/systemd/system/telegram-bot.service; enabled)
     Active: active (running) since Thu 2025-12-25 22:22:10 UTC; 3s ago
   Main PID: 1551 (python)
      Tasks: 2 (limit: 1107)
     Memory: 28.4M (peak: 28.6M)
        CPU: 455ms

● telegram-worker.service - Telegram Ad Bot - Worker Process
     Loaded: loaded (/etc/systemd/system/telegram-worker.service; enabled)
     Active: active (running) since Thu 2025-12-25 22:22:10 UTC; 3s ago
   Main PID: 1554 (python)
      Tasks: 2 (limit: 1107)
     Memory: 26.0M (peak: 26.1M)
        CPU: 414ms
```

---

## 🔐 Step 5: Telethon Authentication

### Issue: Virtual Environment Not Created
First attempt failed because venv didn't exist yet:
```bash
cd /opt/telegram-bot
sudo -u botuser /opt/telegram-bot/venv/bin/python setup_telethon.py
```

**Error:**
```
sudo: /opt/telegram-bot/venv/bin/python: command not found
```

**Reason:** The virtual environment is created by `deploy.sh`, which we ran after trying to set up Telethon.

### Correct Order: Deploy First, Then Telethon
```bash
# 1. Deploy creates venv
sudo bash deploy.sh

# 2. Then setup Telethon
cd /opt/telegram-bot
sudo -u botuser /opt/telegram-bot/venv/bin/python setup_telethon.py
```

### Telethon Setup Process
```
🔐 Telethon Authentication Setup
==================================================
Phone: +917847041321
==================================================
Please enter your phone (or bot token): 917847041321
Please enter the code you received: 63169
Signed in successfully as F; remember to not break the ToS or you will risk an account ban!

✅ Authentication successful!
✅ Session saved to 'user_session.session'

🎉 You can now use /results command in your bot!
```

**Important Notes:**
- Phone number format: Can use with or without `+` prefix
- Code: 5-digit code received in Telegram app
- 2FA: If enabled, password prompt will appear
- Session file: Saved as `user_session.session` in project root

---

## 🔄 Step 6: Final Service Restart

### Restart Services with New Telethon Session
```bash
sudo systemctl restart telegram-bot telegram-worker
```

### Verify Services Running
```bash
sudo systemctl status telegram-bot telegram-worker
```

### View Live Logs
```bash
sudo journalctl -u telegram-bot -u telegram-worker -f
```

### Log Output (Successful Start)
```
Dec 25 22:22:58 tg-ad-landing-bot telegram-bot[1551]: ✅ Database initialized successfully
Dec 25 22:22:58 tg-ad-landing-bot telegram-bot[1551]: 🤖 Starting bot...
Dec 25 22:22:58 tg-ad-landing-bot telegram-bot[1551]: 📁 Storage directory: /opt/telegram-bot/storage
Dec 25 22:22:58 tg-ad-landing-bot telegram-bot[1551]: 👤 Admin user ID: 1977988206
Dec 25 22:22:58 tg-ad-landing-bot telegram-bot[1551]: 📡 Source channel ID: -1003232273065
Dec 25 22:22:58 tg-ad-landing-bot telegram-bot[1551]: 📢 Broadcast batch size: 10
Dec 25 22:22:58 tg-ad-landing-bot telegram-bot[1551]: ✅ Bot is running! Press Ctrl+C to stop.
```

---

## ✅ Deployment Complete!

### Summary of Working Services
- ✅ `telegram-bot.service` - Active and running
- ✅ `telegram-worker.service` - Active and running
- ✅ Database initialized
- ✅ Telethon authenticated
- ✅ Auto-restart enabled
- ✅ Auto-start on boot enabled
- ✅ Firewall configured
- ✅ fail2ban active

---

## 🧪 Testing & Verification

### Bot Commands to Test
```
/start    - Welcome message + scheduled tasks
/help     - Command list
/about    - Bot information
/faq      - FAQ information
/results  - Trading results (Telethon)
/stats    - User statistics (admin only)
/send     - Broadcast messages (admin only)
```

### Scheduled Message Timeline
After `/start`:
- ✅ **Immediate:** Video message (MSG_IMMEDIATE_ID)
- ✅ **30 seconds:** Text message (MSG_30S_ID)
- ✅ **3 minutes:** Images + text (MSG_3MIN_ID)
- ✅ **15 minutes after 3min:** Cleanup + farewell message

---

## 📊 Monitoring Commands

### View Logs
```bash
# Bot logs only
sudo journalctl -u telegram-bot -f

# Worker logs only
sudo journalctl -u telegram-worker -f

# Both together
sudo journalctl -u telegram-bot -u telegram-worker -f

# Last 100 lines
sudo journalctl -u telegram-bot -n 100 --no-pager

# Filter errors only
sudo journalctl -u telegram-bot -n 100 --no-pager | grep ERROR
```

### Service Management
```bash
# Check status
sudo systemctl status telegram-bot telegram-worker

# Restart services
sudo systemctl restart telegram-bot telegram-worker

# Stop services
sudo systemctl stop telegram-bot telegram-worker

# Start services
sudo systemctl start telegram-bot telegram-worker

# Disable auto-start
sudo systemctl disable telegram-bot telegram-worker

# Enable auto-start
sudo systemctl enable telegram-bot telegram-worker
```

### System Monitoring
```bash
# CPU, RAM, disk usage
htop

# Disk space
df -h

# Memory usage
free -h

# Service memory
sudo systemctl status telegram-bot telegram-worker

# Process list
ps aux | grep python
```

---

## 🔄 Update Procedure

### When You Make Code Changes

```bash
# 1. SSH into server
ssh root@138.68.57.241

# 2. Pull latest code
cd /opt/telegram-bot
sudo -u botuser git pull

# 3. Restart services
sudo systemctl restart telegram-bot telegram-worker

# 4. Verify
sudo journalctl -u telegram-bot -u telegram-worker -f
```

### If Requirements Changed
```bash
cd /opt/telegram-bot
sudo -u botuser /opt/telegram-bot/venv/bin/pip install -r requirements.txt
sudo systemctl restart telegram-bot telegram-worker
```

---

## 🔧 Troubleshooting Reference

### Issue: Bot Not Responding

**Check if running:**
```bash
sudo systemctl status telegram-bot
```

**View errors:**
```bash
sudo journalctl -u telegram-bot -n 50
```

**Restart:**
```bash
sudo systemctl restart telegram-bot
```

### Issue: Database Locked

**Symptom:** "Database is locked" error in logs

**Solution:**
```bash
sudo systemctl restart telegram-bot telegram-worker
```

### Issue: Telethon Session Expired

**Symptom:** `/results` command fails

**Solution:** Regenerate session
```bash
cd /opt/telegram-bot
rm user_session.session*
sudo -u botuser /opt/telegram-bot/venv/bin/python setup_telethon.py
sudo systemctl restart telegram-bot
```

### Issue: Worker Not Sending Messages

**Check worker logs:**
```bash
sudo journalctl -u telegram-worker -f
```

**Common causes:**
- SOURCE_CHANNEL_ID incorrect
- Bot not admin in source channel
- Message IDs don't exist
- Bot token invalid

**Verify configuration:**
```bash
sudo nano /opt/telegram-bot/.env
```

### Issue: Permission Errors

**Fix all permissions:**
```bash
sudo chown -R botuser:botuser /opt/telegram-bot
sudo chmod 600 /opt/telegram-bot/.env
sudo chmod 644 /opt/telegram-bot/*.py
```

### Issue: Out of Memory

**Check memory:**
```bash
free -h
htop
```

**Solution:** Upgrade droplet or restart services
```bash
sudo systemctl restart telegram-bot telegram-worker
```

---

## 🔐 Security Configuration

### Firewall Status
```bash
sudo ufw status
```

**Output:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

### fail2ban Status
```bash
sudo systemctl status fail2ban
sudo fail2ban-client status sshd
```

### File Permissions
```bash
# .env file (sensitive)
-rw------- 1 botuser botuser .env

# Session file (sensitive)
-rw-r--r-- 1 botuser botuser user_session.session

# Application directory
drwxr-xr-x 5 botuser botuser /opt/telegram-bot
```

---

## 💾 Backup Procedures

### Database Backup
```bash
# Manual backup
sudo cp /opt/telegram-bot/storage/bot_database.db \
       /opt/telegram-bot/storage/backup_$(date +%Y%m%d_%H%M%S).db

# List backups
ls -lh /opt/telegram-bot/storage/*.db
```

### Environment Backup
```bash
# Backup .env (store securely!)
sudo cp /opt/telegram-bot/.env /root/.env.backup
```

### Session Backup
```bash
# Backup Telethon session
sudo cp /opt/telegram-bot/user_session.session /root/user_session.session.backup
```

---

## 📝 Deployment Timeline

| Time | Action | Status |
|------|--------|--------|
| 22:05 | SSH login | ✅ Success |
| 22:06 | Run deploy_setup.sh | ✅ Success |
| 22:09 | First deploy.sh attempt | ❌ Permission error |
| 22:16 | Manual directory creation | ✅ Success |
| 22:16 | Repository cloned | ✅ Success |
| 22:16 | .env file created | ✅ Success |
| 22:22 | deploy.sh completed | ✅ Success |
| 22:22 | Services started | ✅ Success |
| 22:22 | Telethon setup | ✅ Success |
| 22:23 | Final restart | ✅ Success |
| 22:23 | **Deployment Complete** | ✅ **LIVE** |

**Total Time:** ~18 minutes

---

## 🎯 Lessons Learned

### What Went Right
1. ✅ GitHub repository approach simplified deployment
2. ✅ Systemd services provide reliability
3. ✅ Automated scripts reduced manual steps
4. ✅ Comprehensive logging helps debugging

### Issues Encountered & Solutions
1. **SSH config prompt** → Keep locally-installed version
2. **Permission denied on clone** → Create directory first with proper ownership
3. **Venv not found** → Run deploy.sh before Telethon setup

### Best Practices Applied
1. ✅ Non-root user execution (botuser)
2. ✅ Secure file permissions (.env = 600)
3. ✅ Auto-restart on failure
4. ✅ Firewall configuration
5. ✅ Comprehensive logging
6. ✅ Version-pinned dependencies

---

## 🔗 Important Files & Locations

```
/opt/telegram-bot/                      # Application root
├── bot.py                              # Main bot process
├── worker.py                           # Background worker
├── database.py                         # Database operations
├── utils.py                            # Utility functions
├── .env                                # Environment variables (SECRET!)
├── requirements.txt                    # Python dependencies
├── user_session.session                # Telethon session (SECRET!)
├── storage/                            # Data directory
│   └── bot_database.db                 # SQLite database
└── venv/                               # Python virtual environment

/etc/systemd/system/                    # Systemd services
├── telegram-bot.service                # Bot service definition
└── telegram-worker.service             # Worker service definition

/root/                                  # Deployment scripts
├── deploy_setup.sh                     # Initial server setup
└── deploy.sh                           # Application deployment
```

---

## 📞 Quick Reference

### Repository
**GitHub:** `asutoosh/ad-landing-freya`  
**Clone URL:** `https://github.com/asutoosh/ad-landing-freya.git`

### Server
**IP:** `138.68.57.241`  
**Hostname:** `tg-ad-landing-bot`  
**User:** `root`  
**App User:** `botuser`  
**App Dir:** `/opt/telegram-bot`

### Services
**Bot Service:** `telegram-bot.service`  
**Worker Service:** `telegram-worker.service`

### Admin
**User ID:** `1977988206`  
**Channel ID:** `-1003232273065`

---

## 🎉 Final Notes

This deployment is **production-ready** and running successfully. The bot will:
- ✅ Start automatically on server boot
- ✅ Restart automatically if it crashes
- ✅ Log all activity to systemd journal
- ✅ Process scheduled messages reliably
- ✅ Handle rate limits gracefully

**Last Updated:** December 25, 2025  
**Status:** ✅ LIVE and OPERATIONAL  
**Deployment By:** Root user via SSH

---

*For future deployments, follow the same steps documented here. The deployment scripts can be improved based on the lessons learned from this deployment.*



if For testing prupose  !i used the bot and clear my databse ! how to ! 

Thought for 2s


Perfect question! Here's how to clear your database for testing:

🗑️ Clear Database (On DigitalOcean Server)
Method 1: Delete Database (Fresh Start)
bash
# SSH into your server
ssh root@138.68.57.241
# Stop services
sudo systemctl stop telegram-bot telegram-worker
# Backup current database (just in case)
sudo cp /opt/telegram-bot/storage/bot_database.db /opt/telegram-bot/storage/bot_database_backup_$(date +%Y%m%d_%H%M%S).db
# Delete database - it will be recreated on restart
sudo rm /opt/telegram-bot/storage/bot_database.db
# Restart services (creates fresh database)
sudo systemctl start telegram-bot telegram-worker
# Verify it's running
sudo journalctl -u telegram-bot -f