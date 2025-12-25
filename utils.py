"""
Storage utilities for Telegram Bot
Now uses SQLite database instead of JSON for better scalability and concurrency.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import time

# Import database functions
from database import (
    init_db,
    add_user as db_add_user,
    get_all_users as db_get_all_users,
    create_task as db_create_task,
    get_pending_tasks as db_get_pending_tasks,
    update_task_status as db_update_task_status,
    cancel_user_tasks as db_cancel_user_tasks,
    get_user_count as db_get_user_count,
    get_task_stats as db_get_task_stats,
    track_button_click as db_track_button_click,
    get_button_stats as db_get_button_stats,
    get_user_button_clicks
)

# Keep storage directory for compatibility
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "./storage"))


def ensure_storage():
    """Initialize database (replaces JSON file creation)."""
    init_db()




# Wrapper functions for backward compatibility
# These maintain the same interface but use SQLite instead of JSON

def add_user(user_data: Dict[str, Any]) -> bool:
    """Add user to database."""
    return db_add_user(user_data)


def get_all_users() -> List[Dict[str, Any]]:
    """Get all users from database."""
    return db_get_all_users()


def create_task(chat_id: int, task_type: str, send_at: int, payload: Dict[str, Any]) -> str:
    """Create a new scheduled task in database."""
    return db_create_task(chat_id, task_type, send_at, payload)


def get_pending_tasks() -> List[Dict[str, Any]]:
    """Get all pending tasks from database."""
    return db_get_pending_tasks()


def update_task_status(task_id: str, status: str, increment_retry: bool = False) -> bool:
    """Update task status in database."""
    return db_update_task_status(task_id, status, increment_retry)


def cancel_user_tasks(chat_id: int) -> int:
    """Cancel all pending tasks for a user."""
    return db_cancel_user_tasks(chat_id)


def get_user_count() -> int:
    """Get total number of users."""
    return db_get_user_count()


def get_task_stats() -> Dict[str, int]:
    """Get task statistics."""
    return db_get_task_stats()


def track_button_click(chat_id: int, button_type: str) -> bool:
    """Track a button click."""
    return db_track_button_click(chat_id, button_type)


def get_button_stats() -> Dict[str, int]:
    """Get button click statistics."""
    return db_get_button_stats()


# Keep create_user_tasks as-is since it uses other functions


def create_user_tasks(chat_id: int, start_time: int) -> List[str]:
    """
    Create all scheduled tasks for a new user.
    
    Args:
        chat_id: Telegram chat ID
        start_time: Unix timestamp of /start command
        
    Returns:
        List of created task IDs
    """
    # Get configuration from environment
    source_channel_id = int(os.getenv("SOURCE_CHANNEL_ID", "0"))
    msg_30s_id = int(os.getenv("MSG_30S_ID", "0"))
    msg_3min_id = int(os.getenv("MSG_3MIN_ID", "0"))
    msg_2h_id = int(os.getenv("MSG_2H_ID", "0"))
    target_channel_id = int(os.getenv("TARGET_CHANNEL_ID", "0"))
    
    # Task schedule with message IDs
    task_schedule = []
    
    # Task 1: 40 seconds - Text with button
    if msg_30s_id > 0:
        task_schedule.append({
            "type": "msg_30s",
            "delay": 40,
            "payload": {
                "message_id": msg_30s_id,
                "source_channel_id": source_channel_id,
                "check_membership": False
            }
        })
    
    # Task 2: 3 minutes - Images + text
    if msg_3min_id > 0:
        task_schedule.append({
            "type": "msg_3min",
            "delay": 180,
            "payload": {
                "message_id": msg_3min_id,
                "source_channel_id": source_channel_id,
                "check_membership": False
            }
        })
    
    # Task 2.5: Cleanup - Delete all messages and send farewell
    # Runs after MSG_3MIN_ID + cleanup delay (default 15 minutes)
    cleanup_delay_minutes = int(os.getenv("CLEANUP_DELAY_MINUTES", "15"))
    cleanup_total_delay = 180 + (cleanup_delay_minutes * 60)  # 3min + cleanup delay
    
    task_schedule.append({
        "type": "msg_cleanup",
        "delay": cleanup_total_delay,
        "payload": {
            "farewell_message": "Thanks for using this bot! Nice to meet you 👋"
        }
    })
    
    # Task 3: 2 hours - Final message (only if user didn't click button)

    if msg_2h_id > 0:
        task_schedule.append({
            "type": "msg_2h",
            "delay": 7200,
            "payload": {
                "message_id": msg_2h_id,
                "source_channel_id": source_channel_id,
                "check_button_click": True,  # Check if user clicked button before sending
                "required_button": "join_channel"  # Skip if this button was clicked
            }
        })
    
    task_ids = []
    
    for schedule_item in task_schedule:
        task_id = create_task(
            chat_id=chat_id,
            task_type=schedule_item["type"],
            send_at=start_time + schedule_item["delay"],
            payload=schedule_item["payload"]
        )
        task_ids.append(task_id)
    
    return task_ids



def get_pending_tasks() -> List[Dict[str, Any]]:
    """
    Get all pending tasks that are ready to be sent.
    
    Returns:
        List of pending task dictionaries
    """
    ensure_storage()
    
    import time
    now = int(time.time())
    
    tasks = load_json(TASKS_FILE)
    
    pending = [
        task for task in tasks
        if task.get("status") == "pending" and task.get("send_at", float('inf')) <= now
    ]
    
    return pending


def update_task_status(task_id: str, status: str, increment_retry: bool = False) -> bool:
    """
    Update task status and optionally increment retry counter.
    
    Args:
        task_id: Task ID to update
        status: New status ('sent', 'failed', 'cancelled')
        increment_retry: Whether to increment retry counter
        
    Returns:
        True if successful
    """
    ensure_storage()
    
    tasks = load_json(TASKS_FILE)
    
    for task in tasks:
        if task.get("id") == task_id:
            task["status"] = status
            if increment_retry:
                task["retries"] = task.get("retries", 0) + 1
            break
    
    return save_json_atomic(TASKS_FILE, tasks)


def cancel_user_tasks(chat_id: int) -> int:
    """
    Cancel all pending tasks for a user.
    
    Args:
        chat_id: Telegram chat ID
        
    Returns:
        Number of tasks cancelled
    """
    ensure_storage()
    
    tasks = load_json(TASKS_FILE)
    cancelled_count = 0
    
    for task in tasks:
        if task.get("chat_id") == chat_id and task.get("status") == "pending":
            task["status"] = "cancelled"
            cancelled_count += 1
    
    save_json_atomic(TASKS_FILE, tasks)
    return cancelled_count


def get_user_count() -> int:
    """Get total number of users."""
    return len(get_all_users())


def get_task_stats() -> Dict[str, int]:
    """
    Get statistics about tasks.
    
    Returns:
        Dictionary with task counts by status
    """
    ensure_storage()
    
    tasks = load_json(TASKS_FILE)
    
    stats = {
        "pending": 0,
        "sent": 0,
        "failed": 0,
        "cancelled": 0,
        "total": len(tasks)
    }
    
    for task in tasks:
        status = task.get("status", "unknown")
        if status in stats:
            stats[status] += 1
    
    return stats


def track_button_click(chat_id: int, button_type: str) -> bool:
    """
    Track a button click for a user.
    
    Args:
        chat_id: Telegram chat ID
        button_type: Type of button clicked (e.g., 'join_channel', 'verify')
        
    Returns:
        True if successful
    """
    ensure_storage()
    
    users = load_json(USERS_FILE)
    
    # Find the user
    user = next((u for u in users if u.get('chat_id') == chat_id), None)
    
    if user:
        # Initialize button_clicks if not exists
        if 'button_clicks' not in user:
            user['button_clicks'] = []
        
        # Add click record
        click_record = {
            "button_type": button_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        user['button_clicks'].append(click_record)
        
        return save_json_atomic(USERS_FILE, users)
    
    return False


def get_button_stats() -> Dict[str, int]:
    """
    Get statistics about button clicks.
    
    Returns:
        Dictionary with click counts by button type
    """
    ensure_storage()
    
    users = load_json(USERS_FILE)
    
    stats = {
        "total_clicks": 0,
        "join_channel": 0,
        "verify": 0
    }
    
    for user in users:
        clicks = user.get('button_clicks', [])
        stats["total_clicks"] += len(clicks)
        
        for click in clicks:
            button_type = click.get('button_type', '')
            if button_type in stats:
                stats[button_type] += 1
    
    return stats
