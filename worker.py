"""
Task Worker - Background process for sending scheduled messages
Continuously monitors tasks.json and sends messages when due
"""

import os
import time
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, RetryAfter
from dotenv import load_dotenv

from utils import (
    get_pending_tasks,
    update_task_status,
    ensure_storage
)

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/your_channel")
MAX_RETRIES = 3
POLL_INTERVAL = 5  # Check for tasks every 5 seconds


async def safe_send(bot, method_name, **kwargs):
    """
    Safely send message with RetryAfter/FloodWait handling.
    
    Args:
        bot: Bot instance
        method_name: Name of bot method to call (e.g., 'copy_message', 'send_message')
        **kwargs: Arguments to pass to the method
        
    Returns:
        Result of the method call or None if failed
    """
    max_attempts = 3
    base_delay = 1.0
    
    for attempt in range(max_attempts):
        try:
            method = getattr(bot, method_name)
            return await method(**kwargs)
            
        except RetryAfter as e:
            # Telegram told us exactly how long to wait
            wait_time = e.retry_after + 1
            print(f"⚠️ FloodWait: Telegram requested {wait_time}s wait. Sleeping...")
            await asyncio.sleep(wait_time)
            
        except TelegramError as e:
            # Other Telegram errors - don't retry certain types
            error_msg = str(e).lower()
            if "blocked" in error_msg or "deactivated" in error_msg:
                print(f"🚫 User blocked bot or deactivated")
                return None
            
            # Retry on other errors with exponential backoff
            if attempt < max_attempts - 1:
                delay = base_delay * (2 ** attempt)
                print(f"⚠️ Error: {e}. Retrying in {delay}s... (attempt {attempt + 1}/{max_attempts})")
                await asyncio.sleep(delay)
            else:
                print(f"❌ Failed after {max_attempts} attempts: {e}")
                return None
                
    return None



async def send_task_message(bot: Bot, task: dict) -> bool:
    """
    Send a scheduled task message by forwarding from source channel.
    
    Args:
        bot: Telegram Bot instance
        task: Task dictionary
        
    Returns:
        True if sent successfully, False otherwise
    """
    chat_id = task["chat_id"]
    payload = task["payload"]
    task_type = task.get("task_type", "")
    
    try:
        # Handle cleanup task - delete all messages and send farewell
        if task_type == "msg_cleanup":
            print(f"🧹 Starting cleanup for user {chat_id}")
            
            try:
                # Delete all messages in the chat (from both sides if possible)
                # Note: We can only delete messages sent by the bot
                # The most reliable way is to use deleteMyMessages, but we'll try a different approach
                
                # Get chat history and delete bot messages
                # Unfortunately, python-telegram-bot doesn't have a direct "delete all my messages" method
                # So we'll send the farewell message and note that message deletion is limited by Telegram API
                
                farewell_msg = payload.get("farewell_message", "Thanks for using this bot! Nice to meet you 👋")
                
                # Send farewell message with FloodWait protection
                result = await safe_send(
                    bot,
                    'send_message',
                    chat_id=chat_id,
                    text=farewell_msg
                )
                
                if result:
                    print(f"✅ Cleanup completed for user {chat_id}")
                    return True
                else:
                    print(f"❌ Cleanup failed for user {chat_id}")
                    return False
                
            except TelegramError as e:
                error_msg = str(e)
                if "blocked" in error_msg.lower() or "user is deactivated" in error_msg.lower():
                    print(f"🚫 User {chat_id} blocked bot or account deactivated")
                    return False
                print(f"❌ Error during cleanup for {chat_id}: {e}")
                return False
        
        
        # Check if button click verification is required
        if payload.get("check_button_click", False):
            required_button = payload.get("required_button")
            
            if required_button:
                # Check button clicks using database
                from utils import get_user_button_clicks
                button_clicks = get_user_button_clicks(chat_id)
                
                # Check if user clicked the required button
                clicked = any(click.get('button_type') == required_button for click in button_clicks)
                
                if clicked:
                    print(f"✅ User {chat_id} clicked '{required_button}' button. Skipping 2h message.")
                    return True  # Mark as successful so it's not retried
        
        # Copy message from source channel (no "Forwarded from" tag)
        source_channel_id = payload.get("source_channel_id")
        message_id = payload.get("message_id")
        
        if not source_channel_id or not message_id:
            print(f"❌ Missing source_channel_id or message_id in payload")
            return False
        
        
        # Create dual-button layout: URL for direct access + callback for tracking
        keyboard = [
            [InlineKeyboardButton("⭐ Join Now", url=CHANNEL_URL)],
            [InlineKeyboardButton("✅ I Joined", callback_data="join_channel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        
        # Copy the message (removes "Forwarded from" attribution) with join button
        # Use safe_send to handle FloodWait/RetryAfter
        result = await safe_send(
            bot,
            'copy_message',
            chat_id=chat_id,
            from_chat_id=source_channel_id,
            message_id=message_id,
            reply_markup=reply_markup
        )
        
        return result is not None
        
    except TelegramError as e:
        error_msg = str(e)
        
        # Check if user blocked bot or deleted account
        if "blocked" in error_msg.lower() or "user is deactivated" in error_msg.lower():
            print(f"🚫 User {chat_id} blocked bot or account deactivated")
            return False  # Don't retry
        
        # Check if message not found in channel
        if "message to forward not found" in error_msg.lower():
            print(f"❌ Message {message_id} not found in channel {source_channel_id}")
            return False  # Don't retry
        
        print(f"❌ Error sending to {chat_id}: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False



async def process_tasks(bot: Bot):
    """
    Main worker loop - processes pending tasks.
    """
    print("⏳ Worker started. Checking for tasks every 5 seconds...")
    
    while True:
        try:
            # Get all pending tasks that are due
            pending_tasks = get_pending_tasks()
            
            if pending_tasks:
                print(f"📋 Found {len(pending_tasks)} pending tasks")
            
            for task in pending_tasks:
                task_id = task["id"]
                retries = task.get("retries", 0)
                
                print(f"📤 Sending task {task_id} (type: {task['task_type']}) to {task['chat_id']}")
                
                # Try to send message
                success = await send_task_message(bot, task)
                
                if success:
                    # Mark as sent
                    update_task_status(task_id, "sent")
                    print(f"✅ Task {task_id} sent successfully")
                    
                elif retries < MAX_RETRIES:
                    # Increment retry counter, keep as pending
                    update_task_status(task_id, "pending", increment_retry=True)
                    print(f"🔄 Task {task_id} failed, will retry (attempt {retries + 1}/{MAX_RETRIES})")
                    
                else:
                    # Max retries exceeded, mark as failed
                    update_task_status(task_id, "failed")
                    print(f"❌ Task {task_id} failed after {MAX_RETRIES} attempts")
            
            # Sleep before next check
            await asyncio.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n🛑 Worker stopped by user")
            break
            
        except Exception as e:
            print(f"❌ Worker error: {e}")
            await asyncio.sleep(POLL_INTERVAL)


async def main():
    """Initialize bot and start worker."""
    
    if not BOT_TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not set in .env file!")
        return
    
    # Ensure storage exists
    ensure_storage()
    
    print("🤖 Initializing worker...")
    print(f"📁 Storage directory: {os.path.abspath('storage')}")
    print(f"🔄 Max retries: {MAX_RETRIES}")
    print(f"⏱️ Poll interval: {POLL_INTERVAL}s")
    
    # Create bot instance
    bot = Bot(token=BOT_TOKEN)
    
    # Test bot connection
    try:
        bot_info = await bot.get_me()
        print(f"✅ Connected as @{bot_info.username}")
    except Exception as e:
        print(f"❌ Could not connect to Telegram: {e}")
        return
    
    # Start processing tasks
    await process_tasks(bot)


if __name__ == "__main__":
    asyncio.run(main())
