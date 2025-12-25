"""
Telegram Ad Bot - Main bot process
Handles /start, /stop, and /send commands
"""

import os
import asyncio
import time
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.error import TelegramError
from dotenv import load_dotenv

from utils import (
    add_user,
    create_user_tasks,
    cancel_user_tasks,
    get_all_users,
    ensure_storage,
    track_button_click
)

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/your_channel")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
BROADCAST_BATCH_SIZE = int(os.getenv("BROADCAST_BATCH_SIZE", "10"))

# Channel forwarding configuration
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", "0"))
MSG_IMMEDIATE_ID = int(os.getenv("MSG_IMMEDIATE_ID", "0"))

# Cache for /results command (to avoid rate limits)
RESULTS_CACHE = None
RESULTS_CACHE_TIME = 0
RESULTS_CACHE_DURATION = int(os.getenv("RESULTS_CACHE_HOURS", "1")) * 3600  # Convert hours to seconds


# ===== COMMAND HANDLERS =====

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.
    First time: Saves user info, creates scheduled tasks, sends welcome message.
    Returning users: Shows a different welcome back message with Join button.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Extract deep-link payload (ad tracking)
    payload = None
    if context.args:
        payload = " ".join(context.args)
    
    # Check if user already exists
    users = get_all_users()
    existing_user = any(u.get("chat_id") == chat_id for u in users)
    
    if existing_user:
        # Returning user - show welcome back message with Join button
        keyboard = [[InlineKeyboardButton("🔥 Join Channel", url=CHANNEL_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👋 Welcome back!\n\n"
            "Glad to see you again! 🎉\n\n"
            "Join our channel for exclusive updates and premium content:",
            reply_markup=reply_markup
        )
        print(f"✅ Returning user {user.id} used /start")
        return
    
    # New user - save data and create tasks
    user_data = {
        "chat_id": chat_id,
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "start_payload": payload,
        "timestamp_utc": datetime.utcnow().isoformat()
    }
    
    add_user(user_data)
    
    # Create scheduled tasks
    start_time = int(time.time())
    task_ids = create_user_tasks(chat_id, start_time)
    
    print(f"✅ User {user.id} started bot. Created {len(task_ids)} tasks. Payload: {payload}")
    
    # Send immediate welcome message by copying from source channel (no "Forwarded from" tag)
    if SOURCE_CHANNEL_ID and MSG_IMMEDIATE_ID:
        try:
            # Create "Get The Access" button
            keyboard = [[InlineKeyboardButton("🚀 Get The Access", url=CHANNEL_URL)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=SOURCE_CHANNEL_ID,
                message_id=MSG_IMMEDIATE_ID,
                reply_markup=reply_markup
            )
        except TelegramError as e:
            print(f"⚠️ Could not copy immediate message: {e}")
    else:
        # Fallback text if message ID not configured
        await update.message.reply_text(
            "🎉 Welcome! You've just unlocked exclusive content!\n"
            "Stay tuned for amazing updates! 🚀"
        )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /stop command.
    Cancels all pending tasks for the user.
    """
    chat_id = update.effective_chat.id
    
    cancelled_count = cancel_user_tasks(chat_id)
    
    await update.message.reply_text(
        f"✅ Unsubscribed successfully.\n"
        f"Cancelled {cancelled_count} pending messages.\n\n"
        f"You won't receive any more automated messages.\n"
        f"Send /start anytime to subscribe again."
    )
    
    print(f"🛑 User {chat_id} stopped bot. Cancelled {cancelled_count} tasks.")


async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /faq command.
    Shows frequently asked questions about the service.
    """
    chat_id = update.effective_chat.id
    
    faq_text = (
        "❓ **Frequently Asked Questions**\n\n"
        
        "**Q: Is this service free?**\n"
        "A: Yes! Our signals and educational content are completely free.\n\n"
        
        "**Q: What signals are provided?**\n"
        "A: We provide:\n"
        "• Forex trading signals\n"
        "• Entry/exit points\n"
        "• Take profit levels\n"
        "• Stop loss recommendations\n\n"
        
        "**Q: Can I copy-trade the signals?**\n"
        "A: Absolutely! Our signals are designed to be easy to copy-trade. "
        "Follow the exact entry points and risk management provided.\n\n"
        
        "**Q: Can I learn from this?**\n"
        "A: Yes! We share:\n"
        "• Market analysis\n"
        "• Trading strategies\n"
        "• Risk management techniques\n"
        "• Real-time results\n\n"
        
        "**Q: How do I get started?**\n"
        "A: Simply join our channel to receive all signals and updates!"
    )
    
    # Add join button
    keyboard = [[InlineKeyboardButton("🚀 Join Channel Now", url=CHANNEL_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(faq_text, parse_mode="Markdown", reply_markup=reply_markup)
    print(f"❓ User {chat_id} viewed FAQ")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /about command.
    Shows information about the bot and service.
    """
    chat_id = update.effective_chat.id
    
    about_text = (
        "ℹ️ **About Us**\n\n"
        
        "We are a professional forex trading community providing:\n\n"
        
        "📊 **Free Forex Signals**\n"
        "High-quality trading signals with clear entry/exit points\n\n"
        
        "📚 **Education**\n"
        "Market analysis and trading strategies to help you learn\n\n"
        
        "📈 **Real Results**\n"
        "Track our performance with transparent position updates\n\n"
        
        "🎯 **Our Mission**\n"
        "Help traders succeed through education, signals, and community support.\n\n"
        
        "Join our channel to start your trading journey! 🚀"
    )
    
    # Add join button
    keyboard = [[InlineKeyboardButton("🔥 Join Our Community", url=CHANNEL_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(about_text, parse_mode="Markdown", reply_markup=reply_markup)
    print(f"ℹ️ User {chat_id} viewed About")


async def results_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /results command with caching.
    Fetches latest 5 position status messages from @wazirforexalerts using Telethon.
    Caches results based on RESULTS_CACHE_HOURS environment variable (default: 1 hour).
    """
    global RESULTS_CACHE, RESULTS_CACHE_TIME
    
    chat_id = update.effective_chat.id
    
    try:
        # Send "fetching" message
        status_msg = await update.message.reply_text("📊 Fetching latest results...")
        
        # Check if cache is still valid
        current_time = time.time()
        if RESULTS_CACHE and (current_time - RESULTS_CACHE_TIME) < RESULTS_CACHE_DURATION:
            # Serve from cache
            await status_msg.edit_text(RESULTS_CACHE)
            print(f"📊 User {chat_id} - served from cache (age: {int(current_time - RESULTS_CACHE_TIME)}s)")
            return
        
        # Cache expired or doesn't exist - fetch fresh data
        # Import Telethon async client (not sync)
        try:
            from telethon import TelegramClient  # Use async client
        except ImportError:
            await status_msg.edit_text(
                "❌ Telethon not installed.\n\n"
                "Run: `pip install telethon`"
            )
            return
        
        # Get API credentials from environment
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        phone = os.getenv("TELEGRAM_PHONE")
        
        if not api_id or not api_hash:
            await status_msg.edit_text(
                "❌ Missing Telethon credentials!\n\n"
                "Add to .env:\n"
                "TELEGRAM_API_ID=your_id\n"
                "TELEGRAM_API_HASH=your_hash\n"
                "TELEGRAM_PHONE=+1234567890\n\n"
                "Get API credentials from: https://my.telegram.org"
            )
            return
        
        if not phone:
            await status_msg.edit_text(
                "❌ Missing phone number!\n\n"
                "Add to .env:\n"
                "TELEGRAM_PHONE=+1234567890\n\n"
                "(Your personal Telegram phone number)"
            )
            return
        
        # Create Telethon async client
        session_file = 'user_session'
        client = TelegramClient(session_file, int(api_id), api_hash)
        
        try:
            await client.connect()
            
            # Check if already authorized
            if not await client.is_user_authorized():
                await status_msg.edit_text(
                    "⚠️ First-time setup required!\n\n"
                    "Run: python setup_telethon.py\n"
                    "Complete phone verification, then restart bot."
                )
                await client.disconnect()
                return
            
            # Fetch messages from @wazirforexalerts
            channel_username = 'wazirforexalerts'
            position_updates = []
            
            async for message in client.iter_messages(channel_username, limit=100):
                if not message.text:
                    continue
                
                text = message.text
                
                # Filter: Must have "Position Status"
                if "Position Status" not in text:
                    continue
                
                # Filter: Must have "Take Profit" OR "Hit SL"
                if not ("Take Profit" in text or "Hit SL" in text):
                    continue
                
                # Clean the message
                clean_text = text
                clean_text = clean_text.replace("Any inquiries Dm @zubarekhan01", "")
                clean_text = clean_text.replace("WAZIR FOREX ALERTS", "")
                
                # Remove extra blank lines
                lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
                clean_text = '\n'.join(lines)
                
                # Add emoji based on result type
                if "Take Profit" in clean_text:
                    clean_text = "✅ " + clean_text
                elif "Hit SL" in clean_text:
                    clean_text = "❌ " + clean_text
                
                position_updates.append(clean_text)
                
                # Stop after 5 valid messages
                if len(position_updates) >= 5:
                    break
            
            await client.disconnect()
            
            if not position_updates:
                await status_msg.edit_text("⚠️ No position status updates found.")
                return
            
            # Format with separators
            separator = "\n" + "─" * 30 + "\n\n"
            final_message = separator.join(position_updates)
            final_message = f"📊 **Latest Trading Results**\n{separator}{final_message}"
            
            # Update cache
            RESULTS_CACHE = final_message
            RESULTS_CACHE_TIME = current_time
            
            # Send formatted results
            await status_msg.edit_text(final_message)
            print(f"📊 User {chat_id} - fetched fresh data, cached for 5min ({len(position_updates)} results)")
            
        except Exception as e:
            await client.disconnect()
            raise e
        
    except Exception as e:
        print(f"❌ Error fetching results: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}\n\n"
            "Make sure Telethon is configured correctly with your phone number."
        )




async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /send command (admin only).
    Deprecated - now using /chat in source channel instead.
    """
    user_id = update.effective_user.id
    
    # Check if admin
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ This command is admin-only.")
        return
    
    await update.message.reply_text(
        "📢 *New Broadcast Method*\n\n"
        "The `/send` command has been replaced!\n\n"
        "**To broadcast a message:**\n"
        f"1. Go to your source channel (ID: {SOURCE_CHANNEL_ID})\n"
        "2. Post a message starting with `/chat`\n"
        "3. The bot will automatically forward it to all users in batches\n\n"
        "Example: `/chat Hello everyone! New update!`",
        parse_mode="Markdown"
    )


async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle broadcast message from admin.
    Forwards the message to all users in batches.
    """
    # Check if this is from a user (not a channel)
    if not update.effective_user:
        return
    
    user_id = update.effective_user.id
    
    # Check if admin and in broadcast mode
    if user_id != ADMIN_USER_ID:
        return
        
    if not context.user_data.get("awaiting_broadcast"):
        return
    
    # Clear broadcast mode
    context.user_data["awaiting_broadcast"] = False
    
    message = update.message
    users = get_all_users()
    
    if not users:
        await message.reply_text("⚠️ No users to broadcast to.")
        return
    
    # Send "processing" message
    status_msg = await message.reply_text(
        f"📤 Broadcasting to {len(users)} users...\n"
        f"Please wait..."
    )
    
    success_count = 0
    fail_count = 0
    blocked_count = 0
    
    # Process in batches
    for i in range(0, len(users), BROADCAST_BATCH_SIZE):
        batch = users[i:i+BROADCAST_BATCH_SIZE]
        
        # Forward to all users in batch simultaneously
        results = await asyncio.gather(*[
            message.forward(chat_id=user["chat_id"])
            for user in batch
        ], return_exceptions=True)
        
        # Count successes/failures
        for result in results:
            if isinstance(result, Exception):
                error_msg = str(result)
                if "blocked" in error_msg.lower() or "user is deactivated" in error_msg.lower():
                    blocked_count += 1
                else:
                    fail_count += 1
            else:
                success_count += 1
        
        # Small delay between batches to respect rate limits
        if i + BROADCAST_BATCH_SIZE < len(users):
            await asyncio.sleep(0.5)
    
    # Report results to admin
    result_text = (
        f"✅ *Broadcast Complete!*\n\n"
        f"📊 Results:\n"
        f"✅ Sent: {success_count}\n"
        f"🚫 Blocked/Deactivated: {blocked_count}\n"
        f"❌ Failed: {fail_count}\n"
        f"📈 Total users: {len(users)}"
    )
    
    await status_msg.edit_text(result_text, parse_mode="Markdown")
    
    print(f"📢 Broadcast completed: {success_count} sent, {blocked_count} blocked, {fail_count} failed")


async def handle_chat_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle messages from source channel that start with /chat.
    Automatically broadcast them to all users.
    """
    # Only process channel posts from source channel
    if not update.channel_post:
        return
    
    if update.channel_post.chat.id != SOURCE_CHANNEL_ID:
        return
    
    message = update.channel_post
    text = message.text or message.caption or ""
    
    # Check if message starts with /chat
    if not text.startswith("/chat"):
        return
    
    print(f"📢 Broadcast triggered from channel: {text[:50]}...")
    
    users = get_all_users()
    
    if not users:
        print("⚠️ No users to broadcast to")
        return
    
    success_count = 0
    fail_count = 0
    blocked_count = 0
    
    # Process in batches
    for i in range(0, len(users), BROADCAST_BATCH_SIZE):
        batch = users[i:i+BROADCAST_BATCH_SIZE]
        
        # Copy to all users in batch simultaneously (no "Forwarded from" tag)
        # Create "Join Now" button for each message
        keyboard = [[InlineKeyboardButton("⚡ Join Now", url=CHANNEL_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        results = await asyncio.gather(*[
            context.bot.copy_message(
                chat_id=user["chat_id"],
                from_chat_id=SOURCE_CHANNEL_ID,
                message_id=message.message_id,
                reply_markup=reply_markup
            )
            for user in batch
        ], return_exceptions=True)
        
        # Count successes/failures
        for result in results:
            if isinstance(result, Exception):
                error_msg = str(result)
                if "blocked" in error_msg.lower() or "user is deactivated" in error_msg.lower():
                    blocked_count += 1
                else:
                    fail_count += 1
            else:
                success_count += 1
        
        # Small delay between batches
        if i + BROADCAST_BATCH_SIZE < len(users):
            await asyncio.sleep(0.5)
    
    print(f"📢 Broadcast complete: {success_count} sent, {blocked_count} blocked, {fail_count} failed")


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle button clicks from inline keyboards.
    Tracks all button interactions for analytics.
    """
    query = update.callback_query
    await query.answer()  # Acknowledge the button click
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    button_data = query.data
    
    # Track the click
    track_button_click(chat_id, button_data)
    print(f"🔘 User {user_id} clicked button: {button_data}")
    
    # Handle different button types
    if button_data == "join_channel":
        await query.edit_message_text(
            f"🚀 Join our channel here:\n{CHANNEL_URL}\n\n"
            "Click 'Verify' when you've joined!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ I Joined!", callback_data="verify")
            ]])
        )
    
    elif button_data == "verify":
        await query.edit_message_text(
            "🎉 Awesome! Thanks for joining!\n\n"
            "You'll now receive exclusive trading signals and updates. 📊"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "🤖 **Bot Commands**\n\n"
        "/start - Subscribe to updates\n"
        "/stop - Unsubscribe from updates\n"
        "/results - View latest trading results\n"
        "/faq - Frequently asked questions\n"
        "/about - About us and our service\n"
        "/help - Show this help message\n\n"
        "You'll receive exclusive content and updates automatically!"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command (admin only)."""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ This command is admin-only.")
        return
    
    from utils import get_user_count, get_task_stats, get_button_stats
    
    user_count = get_user_count()
    task_stats = get_task_stats()
    button_stats = get_button_stats()
    
    stats_text = (
        f"📊 *Bot Statistics*\n\n"
        f"👥 Total Users: {user_count}\n\n"
        f"📋 Tasks:\n"
        f"• Pending: {task_stats['pending']}\n"
        f"• Sent: {task_stats['sent']}\n"
        f"• Failed: {task_stats['failed']}\n"
        f"• Cancelled: {task_stats['cancelled']}\n"
        f"• Total: {task_stats['total']}\n\n"
        f"🔘 Button Clicks:\n"
        f"• Total: {button_stats['total_clicks']}\n"
        f"• Join Channel: {button_stats['join_channel']}\n"
        f"• Verify: {button_stats['verify']}"
    )
    
    await update.message.reply_text(stats_text, parse_mode="Markdown")


# ===== MAIN =====

def main():
    """Start the bot."""
    
    # Validate required environment variables
    errors = []
    
    if not BOT_TOKEN:
        errors.append("❌ TELEGRAM_BOT_TOKEN not set!")
    
    if ADMIN_USER_ID == 0:
        errors.append("⚠️ ADMIN_USER_ID not set (admin commands won't work)")
    
    if SOURCE_CHANNEL_ID == 0:
        errors.append("⚠️ SOURCE_CHANNEL_ID not set (message forwarding won't work)")
    
    if MSG_IMMEDIATE_ID == 0:
        errors.append("⚠️ MSG_IMMEDIATE_ID not set (no immediate welcome message)")
    
    # Fatal errors
    if not BOT_TOKEN:
        print("\n".join(errors))
        print("\n💡 Check your .env file and ensure all required variables are set.")
        return
    
    # Warnings only (non-fatal)
    if len(errors) > 1:  # More than just BOT_TOKEN missing
        print("\n⚠️ Warnings:")
        for error in errors[1:]:  # Skip BOT_TOKEN as it's handled above
            print(f"  {error}")
        print()
    
    # Ensure storage exists
    ensure_storage()
    
    print("🤖 Starting bot...")
    print(f"📁 Storage directory: {os.path.abspath('storage')}")
    print(f"👤 Admin user ID: {ADMIN_USER_ID}")
    print(f"📡 Source channel ID: {SOURCE_CHANNEL_ID}")
    print(f"📢 Broadcast batch size: {BROADCAST_BATCH_SIZE}")
    
    # Build application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("faq", faq_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("results", results_command))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    
    # Add callback query handler for button clicks
    app.add_handler(CallbackQueryHandler(button_callback_handler))
    
    # Add channel post handler for /chat broadcasts
    app.add_handler(MessageHandler(
        filters.UpdateType.CHANNEL_POST & filters.ALL,
        handle_chat_broadcast
    ))
    
    # Add message handler for old broadcast (deprecated)
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND & ~filters.UpdateType.CHANNEL_POST,
        handle_broadcast_message
    ))
    
    print("✅ Bot is running! Press Ctrl+C to stop.")
    
    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
