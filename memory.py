"""
memory.py
RUPSHA's long-term memory. SQLite database — one file, no server needed.
"""

import sqlite3
import json
from datetime import datetime
import sys

sys.path.insert(0, "RUPSHA")
import logger

DB_FILE = "RUPSHA/rupsha_memory.db"


def get_connection():
    """Opens a connection to the SQLite file."""
    init_database()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Creates all tables if they don't exist yet. Safe to call multiple times."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            mode TEXT,
            emotion TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT NOT NULL,
            category TEXT,
            confidence REAL,
            created_at TEXT,
            last_accessed TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emotional_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            emotion TEXT NOT NULL,
            trigger TEXT,
            intensity INTEGER
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Memory database initialized.")


def save_message(role, content, mode="companion", emotion=None):
    """Saves one chat message to the database."""
    conn = get_connection()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO conversations (timestamp, role, content, mode, emotion)
        VALUES (?, ?, ?, ?, ?)
    """, (timestamp, role, content, mode, emotion))
    conn.commit()
    conn.close()


def get_recent_conversations(limit=15):
    """Returns the most recent messages as a list of dictionaries."""
    conn = get_connection()
    cursor = conn.execute("""
        SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "timestamp": row["timestamp"],
            "role": row["role"],
            "content": row["content"],
            "mode": row["mode"],
            "emotion": row["emotion"]
        })
    result.reverse()
    return result


def get_conversation_count():
    """Returns total number of messages stored."""
    conn = get_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM conversations")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def save_profile_fact(key, value):
    """Saves or updates a fact about Soumya."""
    conn = get_connection()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO user_profile (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
    """, (key, value, timestamp))
    conn.commit()
    conn.close()
    logger.info(f"Profile: {key} = {value}")


def get_profile():
    """Returns Soumya's profile as a dictionary."""
    conn = get_connection()
    cursor = conn.execute("SELECT key, value FROM user_profile")
    rows = cursor.fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}


def save_fact(fact, category="general", confidence=0.8):
    """Saves something RUPSHA learned about Soumya."""
    conn = get_connection()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO facts (fact, category, confidence, created_at, last_accessed)
        VALUES (?, ?, ?, ?, ?)
    """, (fact, category, confidence, timestamp, timestamp))
    conn.commit()
    conn.close()
    logger.info(f"Fact learned: {fact}")


def get_relevant_facts(query, limit=15):
    """Simple keyword search through learned facts."""
    conn = get_connection()
    cursor = conn.execute("""
        SELECT fact, category, confidence FROM facts
        WHERE fact LIKE ? ORDER BY last_accessed DESC LIMIT ?
    """, (f"%{query}%", limit))
    rows = cursor.fetchall()
    conn.close()
    return [{"fact": r["fact"], "category": r["category"], "confidence": r["confidence"]} for r in rows]


def get_all_facts():
    """Returns every fact RUPSHA knows."""
    conn = get_connection()
    cursor = conn.execute("SELECT fact, category, confidence FROM facts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"fact": r["fact"], "category": r["category"], "confidence": r["confidence"]} for r in rows]


def save_emotion(emotion, trigger=None, intensity=5):
    """Records how Soumya was feeling."""
    conn = get_connection()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO emotional_history (timestamp, emotion, trigger, intensity)
        VALUES (?, ?, ?, ?)
    """, (timestamp, emotion, trigger, intensity))
    conn.commit()
    conn.close()
    logger.info(f"Emotion: {emotion} ({intensity}/10)")


def get_recent_emotions(limit=5):
    """Returns recent emotional entries."""
    conn = get_connection()
    cursor = conn.execute("""
        SELECT * FROM emotional_history ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"timestamp": r["timestamp"], "emotion": r["emotion"], "trigger": r["trigger"], "intensity": r["intensity"]} for r in rows]
