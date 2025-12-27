#!/bin/bash
# Reset Database for Testing
# CAUTION: This will delete all users and tasks!

echo "⚠️  DATABASE RESET SCRIPT"
echo "========================="
echo ""
echo "This will:"
echo "  1. Stop both bot services"
echo "  2. Backup existing database"
echo "  3. Delete database file"
echo "  4. Restart services (triggers re-initialization)"
echo ""

read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Cancelled"
    exit 0
fi

cd /opt/telegram-bot || { echo "❌ /opt/telegram-bot does not exist!"; exit 1; }

echo ""
echo "1️⃣  Stopping services..."
sudo systemctl stop telegram-bot
sudo systemctl stop telegram-worker
echo "✅ Services stopped"

echo ""
echo "2️⃣  Backing up database..."
if [ -f "storage/bot.db" ]; then
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="storage/bot.db.backup_${timestamp}"
    cp storage/bot.db "$backup_file"
    echo "✅ Backup created: $backup_file"
else
    echo "⚠️  No database file to backup"
fi

echo ""
echo "3️⃣  Deleting database..."
if [ -f "storage/bot.db" ]; then
    rm storage/bot.db
    echo "✅ Database deleted"
else
    echo "⚠️  Database file already doesn't exist"
fi

echo ""
echo "4️⃣  Restarting services..."
sudo systemctl start telegram-bot
sleep 2
sudo systemctl start telegram-worker
sleep 2

echo ""
echo "📊 Service Status:"
systemctl is-active --quiet telegram-bot && echo "  ✅ Bot: RUNNING" || echo "  ❌ Bot: STOPPED"
systemctl is-active --quiet telegram-worker && echo "  ✅ Worker: RUNNING" || echo "  ❌ Worker: STOPPED"

echo ""
echo "📋 Checking if database was recreated..."
sleep 3
if [ -f "storage/bot.db" ]; then
    echo "✅ Database recreated successfully!"
    ls -lh storage/bot.db
else
    echo "❌ Database was NOT recreated - check logs!"
    echo ""
    echo "Bot logs:"
    journalctl -u telegram-bot -n 30 --no-pager
fi

echo ""
echo "✅ Reset complete!"
echo ""
echo "📖 View logs with:"
echo "  sudo journalctl -u telegram-bot -f"
echo "  sudo journalctl -u telegram-worker -f"
