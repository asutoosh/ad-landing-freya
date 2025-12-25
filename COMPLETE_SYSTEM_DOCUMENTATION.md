# Complete Bot System Documentation - Every Detail

## 📋 Table of Contents
1. [System Architecture](#architecture)
2. [The Complete Flow](#complete-flow)
3. [File-by-File Breakdown](#files)
4. [Timeline: What Happens When](#timeline)
5. [Database Schema](#database)
6. [Environment Variables](#environment)
7. [Every Feature Explained](#features)

---

## 🏗️ System Architecture {#architecture}

### Three-Process System

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   bot.py    │────▶│ database.py  │◀────│  worker.py   │
│   (Main)    │     │  (SQLite)    │     │ (Background) │
└─────────────┘     └──────────────┘     └──────────────┘
      │                                          │
      │                                          │
      ▼                                          ▼
 Handles user                            Sends scheduled
 interactions                            messages
 (/start, /stop, etc.)                   (after delays)
```

**How they work together:**
1. **User sends `/start`** → `bot.py` receives it
2. **Bot creates user + tasks** → Saves to `database.py` (SQLite)
3. **Worker constantly checks** → Reads pending tasks from database
4. **Worker sends messages** → Updates task status in database

---

## 🔄 The Complete Flow {#complete-flow}

### Timeline from User's First Interaction

```
T = 0 seconds (User sends /start)
├── bot.py receives /start command
├── Creates user record in SQLite
├── Sends immediate welcome message with video
├── Creates 4 scheduled tasks:
│   ├── Task 1: Send message at T+40s
│   ├── Task 2: Send message at T+3min
│   ├── Task 3: Send cleanup at T+18min
│   └── Task 4: Send 2h message at T+2h (if no button click)
└── Returns to user immediately

T = 40 seconds
├── worker.py wakes up (polls every 5s)
├── Queries database: "SELECT tasks WHERE send_at <= now"
├── Finds Task 1 is due
├── Copies message from source channel
├── Sends to user with "✅ I Joined" button
├── Updates task status to "sent"
└── User sees message

T = 3 minutes
├── worker.py finds Task 2 is due
├── Sends second message
└── User clicks "✅ I Joined" button
    ├── bot.py receives callback
    ├── Saves click to database
    └── Updates button to show "verify"

T = 18 minutes
├── worker.py finds cleanup task
├── Sends farewell message
└── Task complete

T = 2 hours
├── worker.py checks if user clicked button
├── IF clicked: Skip this task ✅
└── IF NOT clicked: Send 2h message ❌
```

---

## 📁 File-by-File Breakdown {#files}

### **bot.py** (Main Process) - 700 lines
**What it does:** Handles ALL user interactions

**Every Command:**

#### `/start` (Lines 52-102)
```
1. Extract user info (chat_id, username, first_name)
2. Check if user exists in database
3. If exists: Say "Welcome back!" and skip task creation
4. If new: 
   a. Save user to database
   b. Send immediate welcome with video (MSG_IMMEDIATE_ID)
   c. Create 4 scheduled tasks via utils.create_user_tasks()
5. Return welcome message to user
```

#### `/stop` (Lines 119-143)
```
1. Get chat_id
2. Call cancel_user_tasks(chat_id)
3. Database marks all pending tasks as "cancelled"
4. Send confirmation: "You've been unsubscribed"
```

#### `/faq` (Lines 161-186)
```
1. Build FAQ text from hardcoded content
2. Create "Join Channel" inline button
3. Send message with button
4. Log to console
```

#### `/about` (Lines 203-221)
```
1. Build about text
2. Create "Join Channel" button
3. Send message
```

#### `/results` (Lines 223-362)
```
COMPLEX FLOW:

1. Check cache:
   - If cache < 1 hour old: Return cached results ✅
   
2. If cache expired:
   a. Import Telethon async client
   b. Validate API credentials from .env
   c. Connect to Telegram as USER account
   d. Check if authorized (session file exists)
   e. Query @wazirforexalerts channel:
      - Fetch last 100 messages
      - Filter for "position" messages
      - Extract status info
   f. Build formatted message
   g. Cache for 1 hour
   h. Send to user
   
3. If errors: Send error message
```

#### `/send` (Lines 382-390)
```
DEPRECATED - Just shows message:
"Use /chat in source channel instead"
```

#### `/stats` (Admin Only, Lines 554-580)
```
1. Check if user_id == ADMIN_USER_ID
2. If not: Deny access
3. If yes:
   a. get_user_count() from database
   b. get_task_stats() from database
   c. get_button_stats() from database
   d. Format stats message
   e. Send to admin
```

#### **Button Click Handler** (Lines 582-611)
```
When user clicks ANY inline button:

1. Receive callback query (query.data = button type)
2. Acknowledge click (prevents loading spinner)
3. Extract chat_id and button_data
4. Save to database: track_button_click(chat_id, button_data)
5. Log to console
6. Update message based on button:
   - "join_channel" → Change to "verify" button
   - "verify" → Show success message
```

#### **Channel Broadcast Handler** (Lines 485-544)
```
When admin posts "/chat ..." in source channel:

1. Detect channel post (not regular message)
2. Check if text starts with "/chat"
3. Get all users from database
4. For each user (in batches of 10):
   a. Copy message to user
   b. Add "⚡ Join Now" button
   c. Handle FloodWait if rate limited:
      - Wait X seconds (Telegram tells us)
      - Retry automatically
   d. Track blocked users
5. Log results: X sent, Y blocked, Z failed
```

#### **Startup Validation** (Lines 628-651)
```
When bot starts:

1. Check TELEGRAM_BOT_TOKEN exists → Fatal if missing
2. Check ADMIN_USER_ID set → Warning if 0
3. Check SOURCE_CHANNEL_ID set → Warning if 0
4. Check MSG_IMMEDIATE_ID set → Warning if 0
5. If fatal errors: Exit immediately
6. If warnings: Show but continue
7. Initialize database (ensure tables exist)
8. Register all command handlers
9. Start polling for updates
```

---

### **worker.py** (Background Process) - 280 lines
**What it does:** Sends scheduled messages automatically

**Main Loop (Lines 195-235):**
```python
while True:  # Run forever
    1. Get current time
    2. Query database: get_pending_tasks()
       → SELECT * FROM tasks 
         WHERE status='pending' AND send_at <= NOW
    
    3. For each pending task:
       a. Call send_task_message(bot, task)
       b. If success: update_task_status(id, 'sent')
       c. If failure:
          - Increment retry count
          - If retries < 3: Keep as 'pending'
          - If retries >= 3: Mark as 'failed'
    
    4. Sleep 5 seconds
    5. Repeat
```

**send_task_message() Function (Lines 74-185):**
```
INPUT: task = {
  "id": "abc123",
  "chat_id": 1234567,
  "task_type": "msg_30s",
  "payload": {...}
}

PROCESS:

1. Extract chat_id and task_type
2. Extract payload (message details)

3. IF task_type == "msg_cleanup":
   a. Get farewell message from payload
   b. Send farewell using safe_send()
   c. Return success/failure

4. IF payload has "check_button_click":
   a. Load user from database
   b. Check button_clicks array
   c. If user clicked required button:
      → Skip this message (return True)
   d. If not clicked:
      → Continue to send

5. Copy message from source channel:
   a. Get source_channel_id and message_id
   b. Create "Join" keyboard buttons:
      - "⭐ Join Now" (URL button)
      - "✅ I Joined" (callback button)
   c. Use safe_send() to copy message
   d. Handle errors:
      - Blocked user → Return False
      - Rate limit → Wait and retry
      - Other errors → Retry with backoff

6. Return True if sent, False if failed
```

**safe_send() Helper (Lines 27-70):**
```
PURPOSE: Handle Telegram rate limits automatically

FLOW:
1. Try to call bot method (copy_message, send_message, etc.)
2. If RetryAfter error caught:
   a. Telegram says "wait X seconds"
   b. Sleep X+1 seconds
   c. Retry (up to 3 attempts)
3. If TelegramError caught:
   a. Check if "blocked" or "deactivated"
   b. If yes: Return None (don't retry)
   c. If no: Retry with exponential backoff
      - Attempt 1: wait 1s
      - Attempt 2: wait 2s
      - Attempt 3: wait 4s
4. If all attempts fail: Return None
5. If success: Return result
```

---

### **database.py** (Storage Layer) - 400 lines
**What it does:** All SQLite database operations

**Schema:**
```sql
CREATE TABLE users (
    chat_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    start_payload TEXT,
    timestamp_utc TEXT
);

CREATE TABLE tasks (
    id TEXT PRIMARY KEY,           -- UUID
    chat_id INTEGER,               -- Who to send to
    task_type TEXT,                -- "msg_30s", "msg_3min", etc.
    send_at INTEGER,               -- Unix timestamp when to send
    status TEXT,                   -- "pending", "sent", "failed", "cancelled"
    retries INTEGER,               -- How many times we tried
    payload TEXT                   -- JSON string with message details
);

CREATE TABLE button_clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    button_type TEXT,              -- "join_channel", "verify"
    timestamp TEXT
);

CREATE INDEX idx_tasks_pending ON tasks(status, send_at);
-- Makes queries like "SELECT WHERE status='pending' AND send_at<=X" FAST
```

**Key Functions:**

```python
add_user(user_data)
→ INSERT OR REPLACE INTO users VALUES (...)
→ If user exists: Updates record
→ If new: Creates record

create_task(chat_id, type, send_at, payload)
→ Generate UUID for task ID
→ INSERT INTO tasks VALUES (...)
→ Return task ID

get_pending_tasks()
→ SELECT * FROM tasks WHERE status='pending' AND send_at <= NOW
→ Parse JSON payload
→ Return list of task dicts

update_task_status(task_id, status, increment_retry)
→ UPDATE tasks SET status=? WHERE id=?
→ Optionally: SET retries = retries + 1

track_button_click(chat_id, button_type)
→ INSERT INTO button_clicks VALUES (...)
→ Timestamped automatically

get_button_stats()
→ SELECT button_type, COUNT(*) FROM button_clicks GROUP BY button_type
→ Returns: {"total_clicks": X, "join_channel": Y, "verify": Z}
```

---

### **utils.py** (Helper Functions) - 350 lines
**What it does:** Wrapper functions and task creation logic

**Key Function: create_user_tasks() (Lines 95-178)**
```python
INPUT: chat_id=123456, start_time=1735162800

PROCESS:
1. Load config from environment:
   - SOURCE_CHANNEL_ID
   - MSG_30S_ID, MSG_3MIN_ID, MSG_2H_ID
   - CLEANUP_DELAY_MINUTES

2. Build task schedule (list of dicts):
   
   Task 1 - 40 seconds later:
   {
     "type": "msg_30s",
     "delay": 40,
     "payload": {
       "message_id": MSG_30S_ID,
       "source_channel_id": SOURCE_CHANNEL_ID
     }
   }
   
   Task 2 - 3 minutes later:
   {
     "type": "msg_3min",
     "delay": 180,
     "payload": {...}
   }
   
   Task 3 - 18 minutes later (cleanup):
   {
     "type": "msg_cleanup",
     "delay": 1080,  # 3min + 15min
     "payload": {
       "farewell_message": "Thanks for using..."
     }
   }
   
   Task 4 - 2 hours later (conditional):
   {
     "type": "msg_2h",
     "delay": 7200,
     "payload": {
       "message_id": MSG_2H_ID,
       "check_button_click": True,
       "required_button": "join_channel"
     }
   }

3. For each schedule item:
   a. Calculate send_at = start_time + delay
   b. Call create_task(chat_id, type, send_at, payload)
   c. Returns task_id
   d. Collect all task_ids

4. Return list of task IDs: ["abc123", "def456", "ghi789", "jkl012"]
```

**Other Wrapper Functions:**
```python
add_user() → db_add_user()
get_all_users() → db_get_all_users()
cancel_user_tasks() → db_cancel_user_tasks()
# All just call database.py functions
```

---

### **run_bot.py** (Launcher) - 48 lines
**What it does:** Starts both bot.py and worker.py together

```python
PROCESS:

1. Start bot process:
   subprocess.Popen(["python", "bot.py"])
   → Runs in background, PID stored

2. Start worker process:
   subprocess.Popen(["python", "worker.py"])
   → Runs in background, PID stored

3. Print success message

4. Wait for Ctrl+C

5. On Ctrl+C:
   a. Terminate both processes
   b. Wait for clean shutdown
   c. Print "✅ Both stopped"
```

---

### **migrate_to_sqlite.py** (One-Time Script) - 80 lines
**What it does:** Converts old JSON files to SQLite

```python
PROCESS:

1. Initialize SQLite database (create tables)

2. Load users.json:
   a. Parse JSON
   b. For each user:
      - Call add_user(user_data)
      - If user has button_clicks:
        → Save each click to button_clicks table

3. Load tasks.json:
   a. Parse JSON
   b. For each task:
      - INSERT directly to preserve:
        → Original task ID
        → Original status
        → Original retries

4. Print summary:
   "✅ Migrated X users"
   "✅ Migrated Y tasks"
```

---

## ⏱️ Timeline: What Happens When {#timeline}

### Scenario 1: New User Joins

```
00:00:00 - User sends /start
         ├── bot.py: start_command() triggered
         ├── Check database: user exists? → No
         ├── Save user: add_user({chat_id, username, ...})
         ├── Send video: MSG_IMMEDIATE_ID from source channel
         ├── Create tasks: create_user_tasks(chat_id, now)
         │   └── Creates 4 tasks in database
         └── Reply: "Welcome! Check out this video"

00:00:05 - worker.py polls
         └── get_pending_tasks() → [] (none due yet)

00:00:10 - worker.py polls
         └── get_pending_tasks() → [] (none due yet)

00:00:40 - worker.py polls
         ├── get_pending_tasks() → [task_msg_30s]
         ├── send_task_message(task)
         │   ├── Copy MSG_30S_ID to user
         │   ├── Add buttons: "Join Now" + "I Joined"
         │   └── Success!
         ├── update_task_status(id, 'sent')
         └── Console: "✅ Task abc123 sent successfully"

00:01:20 - User clicks "✅ I Joined"
         ├── bot.py: button_callback_handler() triggered
         ├── query.data = "join_channel"
         ├── track_button_click(chat_id, "join_channel")
         │   └── INSERT INTO button_clicks
         ├── Update message text
         └── Show "verify" button

00:03:00 - worker.py polls
         ├── get_pending_tasks() → [task_msg_3min]
         ├── send_task_message(task)
         │   └── Copy MSG_3MIN_ID to user
         └── update_task_status(id, 'sent')

00:18:00 - worker.py polls
         ├── get_pending_tasks() → [task_cleanup]
         ├── send_task_message(task)
         │   ├── task_type == "msg_cleanup"
         │   └── Send: "Thanks for using this bot!"
         └── update_task_status(id, 'sent')

02:00:00 - worker.py polls
         ├── get_pending_tasks() → [task_msg_2h]
         ├── send_task_message(task)
         │   ├── check_button_click: True
         │   ├── Load user from database
         │   ├── Check button_clicks for "join_channel"
         │   ├── Found! User clicked at 00:01:20
         │   └── Skip message ✅
         └── update_task_status(id, 'sent')  # Marked sent but not actually sent
```

### Scenario 2: Returning User

```
00:00:00 - User sends /start (already exists)
         ├── bot.py: start_command() triggered
         ├── Check database: user exists? → Yes!
         ├── Don't create new tasks
         └── Reply: "✅ Returning user 1234567 used /start"
```

### Scenario 3: Admin Broadcasts

```
Admin posts in source channel: "/chat New signal alert! 📊"

00:00:00 - bot.py: handle_chat_broadcast() triggered
         ├── Detect: message.text starts with "/chat"
         ├── get_all_users() → 1500 users
         ├── Batch 1 (users 1-10):
         │   ├── Copy message to user 1 with "Join" button
         │   ├── Copy message to user 2
         │   ├── ...
         │   ├── Copy message to user 10
         │   └── Sleep 0.5s
         ├── Batch 2 (users 11-20):
         │   ├── Copy message to user 11
         │   ├── RATE LIMIT! RetryAfter 10s
         │   ├── Sleep 10 seconds
         │   ├── Retry user 11 → Success
         │   ├── Continue with users 12-20
         │   └── Sleep 0.5s
         ├── ... (continue for all 150 batches)
         └── Console: "✅ 1450 sent, 30 blocked, 20 failed"
```

---

## 🗄️ Database Schema Details {#database}

### users Table
```
chat_id       | user_id     | username   | first_name | last_name | start_payload | timestamp_utc
--------------|-------------|------------|------------|-----------|---------------|------------------
1977988206    | 1977988206  | "cogitosk" | "F"        | null      | null          | "2025-12-25..."
```

### tasks Table
```
id        | chat_id    | task_type    | send_at    | status    | retries | payload
----------|------------|--------------|------------|-----------|---------|---------------------------
abc123    | 1977988206 | "msg_30s"    | 1735162840 | "sent"    | 0       | "{\"message_id\": 56, ...}"
def456    | 1977988206 | "msg_3min"   | 1735162980 | "pending" | 0       | "{\"message_id\": 57, ...}"
ghi789    | 1977988206 | "msg_cleanup"| 1735163880 | "pending" | 0       | "{\"farewell_message\": ...}"
jkl012    | 1977988206 | "msg_2h"     | 1735170000 | "pending" | 0       | "{\"check_button_click\": ...}"
```

### button_clicks Table
```
id | chat_id    | button_type    | timestamp
---|------------|----------------|--------------------
1  | 1977988206 | "join_channel" | "2025-12-25T20:41:20"
2  | 1977988206 | "verify"       | "2025-12-25T20:41:35"
```

---

## 🔧 Environment Variables {#environment}

### `.env` File Contents
```bash
# Core Config
TELEGRAM_BOT_TOKEN=8557282195:AAE...  # Bot token from @BotFather
ADMIN_USER_ID=1977988206              # Your Telegram user ID
CHANNEL_URL=https://t.me/yourbot      # Public channel link

# Source Channel
SOURCE_CHANNEL_ID=-1003232273065      # Channel where messages stored
TARGET_CHANNEL_ID=-1003232273065      # Channel for membership check

# Message IDs (from source channel)
MSG_IMMEDIATE_ID=36                   # Video welcome
MSG_30S_ID=56                         # First text
MSG_3MIN_ID=57                        # Second message
MSG_2H_ID=50                          # Final reminder

# Telethon (for /results command)
TELEGRAM_API_ID=27436879
TELEGRAM_API_HASH=d4ef9bf420939c1a...
TELEGRAM_PHONE=+917847041321

# Timing
RESULTS_CACHE_HOURS=1                 # Cache /results for X hours
CLEANUP_DELAY_MINUTES=15              # Wait time before cleanup

# Broadcasting
BROADCAST_BATCH_SIZE=10               # Users per batch
```

---

## 🎯 Every Feature Explained {#features}

### 1. **User Onboarding Flow**
- User sends `/start`
- Gets immediate video welcome
- Receives 2 more messages over 3 minutes
- Gets farewell after 18 minutes
- Possibly gets 2h reminder (if they don't engage)

### 2. **Button Click Tracking**
- Every button click saved to database
- Used for analytics (/stats)
- Used to conditionally skip 2h message
- Tracked per user, per button type

### 3. **Task Scheduling System**
- All tasks created upfront (at /start)
- Worker polls every 5 seconds
- Sends messages when due
- Handles retries automatically (3 max)
- Updates status after each attempt

### 4. **Rate Limit Protection**
- `safe_send()` wrapper on all sends
- Detects Telegram's RetryAfter error
- Waits exact time Telegram requests
- Exponential backoff for other errors
- Prevents bot bans

### 5. **Channel Broadcasting**
- Admin posts "/chat ..." in source channel
- Bot auto-forwards to all users
- Removes "Forwarded from" tag
- Adds "Join" button automatically
- Batches of 10 with delays

### 6. **Results Fetching**
- Uses Telethon (user account client)
- Fetches from @wazirforexalerts
- Caches for 1 hour
- Filters for "position" messages
- Returns last 5 results

### 7. **Admin Commands**
- `/stats` - View user/task/button statistics
- `/send` - Shows deprecation message
- Broadcasts via `/chat` in channel

### 8. **Data Persistence**
- Everything in SQLite database
- Atomic transactions (no corruption)
- Survives bot restarts
- Worker picks up where it left off

### 9. **Error Handling**
- Blocked users: Skip and count
- Rate limits: Wait and retry
- Failed tasks: Retry 3 times then mark failed
- Missing env vars: Exit with clear error

### 10. **Cleanup Feature**
- Runs 15 min after 3-minute message
- Sends farewell
- Marks end of automated sequence

---

## 🔢 By The Numbers

**Total Lines of Code:** ~2,000
- bot.py: 700 lines
- worker.py: 280 lines
- database.py: 400 lines
- utils.py: 350 lines
- Other files: 270 lines

**Database Tables:** 3
- users
- tasks
- button_clicks

**Commands:** 8
- /start, /stop, /faq, /about, /results, /send, /stats, /help

**Task Types:** 4
- msg_30s, msg_3min, msg_cleanup, msg_2h

**Environment Variables:** 14

**Max Concurrent Users:** 10,000+ (with SQLite)

**Polling Interval:** 5 seconds

**Max Retries:** 3

**Broadcast Batch Size:** 10

**Cache Duration:** 1 hour

---

## 🎓 Summary

**Your bot is a sophisticated automated marketing system that:**

1. **Captures** users via /start
2. **Engages** them with timed messages
3. **Tracks** their interactions (button clicks)
4. **Broadcasts** updates from admin
5. **Scales** to thousands of users
6. **Survives** restarts and errors
7. **Respects** Telegram rate limits
8. **Provides** analytics for optimization

**Core Innovation:** Separation of concerns (bot handles input, worker handles output), allowing independent scaling and restart-safety.

**Ready for production!** 🚀
