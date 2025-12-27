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
    get_task_stats as db_get_task_stats
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
    
    # Task 1: 30 seconds - Text with button
    if msg_30s_id > 0:
        task_schedule.append({
            "type": "msg_30s",
            "delay": 30,
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
    
    # Task 3: 2 hours - Final message (sent to ALL users)

    if msg_2h_id > 0:
        task_schedule.append({
            "type": "msg_2h",
            "delay": 7200,
            "payload": {
                "message_id": msg_2h_id,
                "source_channel_id": source_channel_id,
                "check_membership": False
            }
        })
    
    task_ids = []
    
    print(f"📋 Creating {len(task_schedule)} tasks for user {chat_id}:")
    for schedule_item in task_schedule:
        send_time = start_time + schedule_item["delay"]
        task_id = create_task(
            chat_id=chat_id,
            task_type=schedule_item["type"],
            send_at=send_time,
            payload=schedule_item["payload"]
        )
        from datetime import datetime
        send_time_str = datetime.fromtimestamp(send_time).strftime('%H:%M:%S')
        print(f"  └─ {schedule_item['type']}: {schedule_item['delay']}s delay (at {send_time_str})")
        task_ids.append(task_id)
    
    return task_ids

