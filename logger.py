"""
logger.py
RUPSHA's diary. Every action, error, and chat is recorded here.
"""

import os
from datetime import datetime
import sys

sys.path.insert(0, "RUPSHA")
from config import LOG_FILE

def _write(level, message):
    """Private helper. Writes one line to the log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}"
    print(line)  # Also show in Colab output
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass  # If log fails, don't crash RUPSHA

def info(message):
    _write("INFO", message)

def warning(message):
    _write("WARNING", message)

def error(message):
    _write("ERROR", message)

def log_chat(user_msg, bot_reply):
    _write("CHAT", f"Soumya: {user_msg[:60]}...")
    _write("CHAT", f"RUPSHA: {bot_reply[:60]}...")
