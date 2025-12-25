"""
SQLite Database Module for Telegram Bot
Replaces JSON storage with atomic, concurrent-safe database operations.
"""

import sqlite3
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

# Database path
DB_PATH = Path("storage/bot.db")


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database with schema."""
    DB_PATH.parent.mkdir(exist_ok=True)
    
    with get_db() as conn:
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                start_payload TEXT,
                timestamp_utc TEXT
            )
        """)
        
        # Tasks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                chat_id INTEGER,
                task_type TEXT,
                send_at INTEGER,
                status TEXT,
                retries INTEGER,
                payload TEXT
            )
        """)
        
        # Button clicks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS button_clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                button_type TEXT,
                timestamp TEXT
            )
        """)
        
        # Indexes for performance
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_pending 
            ON tasks(status, send_at)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_button_clicks_chat 
            ON button_clicks(chat_id)
        """)
        
        conn.commit()
        print("✅ Database initialized successfully")


def add_user(user_data: Dict[str, Any]) -> bool:
    """
    Add or update user in database.
    
    Args:
        user_data: Dictionary with user information
        
    Returns:
        True if successful
    """
    try:
        with get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users 
                (chat_id, user_id, username, first_name, last_name, start_payload, timestamp_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data.get('chat_id'),
                user_data.get('user_id'),
                user_data.get('username'),
                user_data.get('first_name'),
                user_data.get('last_name'),
                user_data.get('start_payload'),
                user_data.get('timestamp_utc')
            ))
            conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error adding user: {e}")
        return False


def get_all_users() -> List[Dict[str, Any]]:
    """
    Get all users from database.
    
    Returns:
    List of user dictionaries
    """
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM users")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching users: {e}")
        return []


def create_task(chat_id: int, task_type: str, send_at: int, payload: Dict[str, Any]) -> str:
    """
    Create a new scheduled task.
    
    Args:
        chat_id: Telegram chat ID
        task_type: Type of task
        send_at: Unix timestamp when to send
        payload: Message content and metadata
        
    Returns:
        Task ID (UUID)
    """
    task_id = uuid.uuid4().hex
    
    try:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO tasks 
                (id, chat_id, task_type, send_at, status, retries, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                chat_id,
                task_type,
                send_at,
                "pending",
                0,
                json.dumps(payload)
            ))
            conn.commit()
        return task_id
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return ""


def get_pending_tasks() -> List[Dict[str, Any]]:
    """
    Get all pending tasks that are ready to be sent.
    
    Returns:
        List of pending task dictionaries
    """
    now = int(time.time())
    
    try:
        with get_db() as conn:
            cursor = conn.execute("""
                SELECT * FROM tasks 
                WHERE status = 'pending' AND send_at <= ?
                ORDER BY send_at ASC
            """, (now,))
            
            tasks = []
            for row in cursor.fetchall():
                task = dict(row)
                task['payload'] = json.loads(task['payload'])
                tasks.append(task)
            return tasks
    except Exception as e:
        print(f"❌ Error fetching pending tasks: {e}")
        return []


def update_task_status(task_id: str, status: str, increment_retry: bool = False) -> bool:
    """
    Update task status and optionally increment retry counter.
    
    Args:
        task_id: Task ID to update
        status: New status
        increment_retry: Whether to increment retry counter
        
    Returns:
        True if successful
    """
    try:
        with get_db() as conn:
            if increment_retry:
                conn.execute("""
                    UPDATE tasks 
                    SET status = ?, retries = retries + 1
                    WHERE id = ?
                """, (status, task_id))
            else:
                conn.execute("""
                    UPDATE tasks 
                    SET status = ?
                    WHERE id = ?
                """, (status, task_id))
            conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating task: {e}")
        return False


def cancel_user_tasks(chat_id: int) -> int:
    """
    Cancel all pending tasks for a user.
    
    Args:
        chat_id: Telegram chat ID
        
    Returns:
        Number of tasks cancelled
    """
    try:
        with get_db() as conn:
            cursor = conn.execute("""
                UPDATE tasks 
                SET status = 'cancelled'
                WHERE chat_id = ? AND status = 'pending'
            """, (chat_id,))
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        print(f"❌ Error cancelling tasks: {e}")
        return 0


def track_button_click(chat_id: int, button_type: str) -> bool:
    """
    Track a button click for a user.
    
    Args:
        chat_id: Telegram chat ID
        button_type: Type of button clicked
        
    Returns:
        True if successful
    """
    try:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO button_clicks (chat_id, button_type, timestamp)
                VALUES (?, ?, ?)
            """, (chat_id, button_type, datetime.utcnow().isoformat()))
            conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error tracking button click: {e}")
        return False


def get_user_button_clicks(chat_id: int) -> List[Dict[str, Any]]:
    """
    Get all button clicks for a user.
    
    Args:
        chat_id: Telegram chat ID
        
    Returns:
        List of button click records
    """
    try:
        with get_db() as conn:
            cursor = conn.execute("""
                SELECT button_type, timestamp 
                FROM button_clicks 
                WHERE chat_id = ?
                ORDER BY timestamp DESC
            """, (chat_id,))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching button clicks: {e}")
        return []


def get_user_count() -> int:
    """Get total number of users."""
    try:
        with get_db() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM users")
            return cursor.fetchone()['count']
    except Exception as e:
        print(f"❌ Error getting user count: {e}")
        return 0


def get_task_stats() -> Dict[str, int]:
    """
    Get statistics about tasks.
    
    Returns:
        Dictionary with task counts by status
    """
    try:
        with get_db() as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM tasks 
                GROUP BY status
            """)
            
            stats = {
                "pending": 0,
                "sent": 0,
                "failed": 0,
                "cancelled": 0,
                "total": 0
            }
            
            for row in cursor.fetchall():
                stats[row['status']] = row['count']
                stats['total'] += row['count']
            
            return stats
    except Exception as e:
        print(f"❌ Error getting task stats: {e}")
        return {"pending": 0, "sent": 0, "failed": 0, "cancelled": 0, "total": 0}


def get_button_stats() -> Dict[str, int]:
    """
    Get statistics about button clicks.
    
    Returns:
        Dictionary with click counts by button type
    """
    try:
        with get_db() as conn:
            cursor = conn.execute("""
                SELECT button_type, COUNT(*) as count 
                FROM button_clicks 
                GROUP BY button_type
            """)
            
            stats = {
                "total_clicks": 0,
                "join_channel": 0,
                "verify": 0
            }
            
            for row in cursor.fetchall():
                stats[row['button_type']] = row['count']
                stats['total_clicks'] += row['count']
            
            return stats
    except Exception as e:
        print(f"❌ Error getting button stats: {e}")
        return {"total_clicks": 0, "join_channel": 0, "verify": 0}
