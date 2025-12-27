#!/bin/bash
# Telegram Bot Deployment Diagnostic Script
# Checks database, services, logs, and environment

echo "🔍 Telegram Bot Deployment Diagnostics"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  Running as root. Bot should run as 'botuser'"
fi

echo "📁 Working Directory Check:"
cd /opt/telegram-bot || { echo "❌ /opt/telegram-bot does not exist!"; exit 1; }
echo "✅ Directory exists: $(pwd)"
echo ""

echo "📂 Database Check:"
if [ -f "storage/bot.db" ]; then
    echo "✅ Database file exists"
    ls -lh storage/bot.db
    echo ""
    
    echo "📊 Database Contents:"
    sqlite3 storage/bot.db "SELECT COUNT(*) as user_count FROM users;" 2>/dev/null && \
        echo "  Users: $(sqlite3 storage/bot.db 'SELECT COUNT(*) FROM users;')" || \
        echo "❌ Could not query users table"
    
    sqlite3 storage/bot.db "SELECT COUNT(*) as pending FROM tasks WHERE status='pending';" 2>/dev/null && \
        echo "  Pending tasks: $(sqlite3 storage/bot.db 'SELECT COUNT(*) FROM tasks WHERE status='"'"'pending'"'"';')" || \
        echo "❌ Could not query tasks table"
    
    sqlite3 storage/bot.db "SELECT COUNT(*) as sent FROM tasks WHERE status='sent';" 2>/dev/null && \
        echo "  Sent tasks: $(sqlite3 storage/bot.db 'SELECT COUNT(*) FROM tasks WHERE status='"'"'sent'"'"';')" || \
        echo "❌ Could not query tasks table"
else
    echo "❌ Database file does not exist at storage/bot.db"
fi
echo ""

echo "🔐 Permissions Check:"
echo "Storage directory:"
ls -ld storage/
if [ -f "storage/bot.db" ]; then
    echo "Database file:"
    ls -l storage/bot.db
fi
echo ""

echo "🤖 Service Status:"
systemctl is-active --quiet telegram-bot && echo "✅ Bot service: RUNNING" || echo "❌ Bot service: STOPPED"
systemctl is-active --quiet telegram-worker && echo "✅ Worker service: RUNNING" || echo "❌ Worker service: STOPPED"
echo ""

echo "📋 Recent Bot Logs (last 20 lines):"
echo "-----------------------------------"
journalctl -u telegram-bot -n 20 --no-pager
echo ""

echo "📋 Recent Worker Logs (last 20 lines):"
echo "---------------------------------------"
journalctl -u telegram-worker -n 20 --no-pager
echo ""

echo "🔧 Environment Variables Check:"
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    echo "Checking critical variables..."
    
    grep -q "TELEGRAM_BOT_TOKEN=" .env && echo "  ✅ TELEGRAM_BOT_TOKEN set" || echo "  ❌ TELEGRAM_BOT_TOKEN missing"
    grep -q "SOURCE_CHANNEL_ID=" .env && echo "  ✅ SOURCE_CHANNEL_ID set" || echo "  ❌ SOURCE_CHANNEL_ID missing"
    grep -q "MSG_IMMEDIATE_ID=" .env && echo "  ✅ MSG_IMMEDIATE_ID set" || echo "  ❌ MSG_IMMEDIATE_ID missing"
    grep -q "MSG_30S_ID=" .env && echo "  ✅ MSG_30S_ID set" || echo "  ❌ MSG_30S_ID missing"
    grep -q "MSG_3MIN_ID=" .env && echo "  ✅ MSG_3MIN_ID set" || echo "  ❌ MSG_3MIN_ID missing"
else
    echo "❌ .env file does not exist!"
fi
echo ""

echo "🐍 Python Dependencies:"
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    source venv/bin/activate
    pip list | grep -E "(python-telegram-bot|python-dotenv|telethon)"
    deactivate
else
    echo "❌ Virtual environment not found"
fi
echo ""

echo "📊 Summary:"
echo "==========="
echo "Run this to view live logs:"
echo "  Bot: sudo journalctl -u telegram-bot -f"
echo "  Worker: sudo journalctl -u telegram-worker -f"
echo ""
echo "To restart services:"
echo "  sudo systemctl restart telegram-bot"
echo "  sudo systemctl restart telegram-worker"
