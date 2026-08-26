"""
user_profile.py
Sets up Soumya's default profile when RUPSHA first wakes up.
"""

import sys
sys.path.insert(0, "RUPSHA")

from memory import save_profile_fact, get_profile
import config
import logger

def setup_profile():
    """Creates default profile if empty. Won't overwrite existing data."""
    existing = get_profile()
    if existing:
        logger.info("Profile already exists.")
        return

    save_profile_fact("name", config.USER_NAME)
    save_profile_fact("relationship", "closest friend")
    save_profile_fact("project", "Building RUPSHA AI from scratch")

    logger.info("Default profile created.")
    print("👤 Profile initialized for Soumya.")
