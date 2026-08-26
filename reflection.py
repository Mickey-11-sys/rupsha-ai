"""
reflection.py
After conversations, RUPSHA thinks: "What did I learn about Soumya today?"
"""

import sys
sys.path.insert(0, "RUPSHA")
from memory import save_fact
import logger

def reflect_on_conversation(user_messages, bot_replies):
    """
    Simple keyword-based reflection.
    Returns: number of new facts learned.
    """
    all_text = " ".join(user_messages).lower()
    facts_found = []

    if any(word in all_text for word in ["exam", "test", "quiz"]):
        facts_found.append(("Soumya mentioned an exam or test.", "academic", 0.7))
    if "assignment" in all_text:
        facts_found.append(("Soumya has an assignment.", "academic", 0.8))
    if any(word in all_text for word in ["python", "coding", "programming"]):
        facts_found.append(("Soumya is working with Python.", "academic", 0.8))
    if any(word in all_text for word in ["tired", "sleepy", "exhausted"]):
        facts_found.append(("Soumya seemed tired.", "personal", 0.6))
    if any(word in all_text for word in ["happy", "excited", "great"]):
        facts_found.append(("Soumya was in a good mood.", "personal", 0.6))
    if any(word in all_text for word in ["stress", "tension", "anxious"]):
        facts_found.append(("Soumya was feeling stressed.", "personal", 0.7))
    if "coffee" in all_text:
        facts_found.append(("Soumya likes coffee.", "preference", 0.5))
    if "tea" in all_text:
        facts_found.append(("Soumya likes tea.", "preference", 0.5))

    saved = 0
    for fact, category, confidence in facts_found:
        save_fact(fact, category, confidence)
        saved += 1

    logger.info(f"Reflection: learned {saved} facts.")
    return saved
