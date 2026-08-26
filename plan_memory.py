"""
plan_memory.py
RUPSHA remembers what worked. Stores successful task patterns.
"""

import sqlite3
import json
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rupsha_memory.db")


def _get_pattern_key(task: str):
    """Creates a fingerprint from a task description."""
    words = task.lower().split()
    fluff = {"the", "a", "an", "and", "or", "find", "search", "for", "me", "please", "can", "you", "get", "latest", "recent", "current"}
    content = [w for w in words if w not in fluff and len(w) > 2]
    pattern = " ".join(content[:3])
    return hashlib.md5(pattern.encode()).hexdigest()[:12], pattern


def save_plan(task: str, plan_steps: list):
    """Saves a successful plan."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS plan_memory (
                pattern_hash TEXT UNIQUE, pattern_text TEXT,
                action_sequence TEXT, success_count INTEGER DEFAULT 1,
                last_used TEXT
            )
        ''')
        ph, pt = _get_pattern_key(task)
        actions = json.dumps([s.get("action") for s in plan_steps if s.get("action") not in ("answer", "summarize")])
        c.execute("SELECT success_count FROM plan_memory WHERE pattern_hash = ?", (ph,))
        if c.fetchone():
            c.execute("UPDATE plan_memory SET success_count = success_count + 1, last_used = datetime('now') WHERE pattern_hash = ?", (ph,))
        else:
            c.execute("INSERT INTO plan_memory VALUES (?, ?, ?, 1, datetime('now'))", (ph, pt, actions))
        conn.commit()
        conn.close()
        print(f"💾 Plan memory saved: '{pt}'")
    except Exception as e:
        print(f"Memory save error: {e}")


def find_plan(task: str):
    """Looks for a similar successful plan. Returns action list or None."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS plan_memory (
                pattern_hash TEXT UNIQUE, pattern_text TEXT,
                action_sequence TEXT, success_count INTEGER DEFAULT 1,
                last_used TEXT
            )
        ''')
        ph, pt = _get_pattern_key(task)
        c.execute("SELECT action_sequence FROM plan_memory WHERE pattern_hash = ?", (ph,))
        row = c.fetchone()
        conn.close()
        if row:
            actions = json.loads(row[0])
            print(f"🧠 Plan memory hit: '{pt}' → {actions}")
            return actions
        return None
    except Exception as e:
        print(f"Memory lookup error: {e}")
        return None


def get_stats():
    """Returns how many plans RUPSHA remembers."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*), SUM(success_count) FROM plan_memory")
        p, u = c.fetchone()
        conn.close()
        return {"patterns": p or 0, "uses": u or 0}
    except:
        return {"patterns": 0, "uses": 0}
