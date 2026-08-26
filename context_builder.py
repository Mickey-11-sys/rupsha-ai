"""
context_builder.py
Before RUPSHA replies, she gathers memories to make the reply feel personal.
"""

import sys
sys.path.insert(0, "RUPSHA")
from memory import get_recent_conversations, get_relevant_facts, get_profile, get_recent_emotions
import logger

from vector_db import VectorMemory
from knowledge_graph import KnowledgeGraph


def build_context(user_message="", vector_db=None, kg=None):
    """
    Builds a memory context string from the database.
    Writes it like RUPSHA's own thoughts — natural, warm, not bullet points.
    """
    parts = []

    # 1. Recent conversation — written as a natural recap
    try:
        recent = get_recent_conversations(limit=10)
        if recent:
            lines = []
            for conv in recent[-3:]:
                role = "Soumya" if conv["role"] == "user" else "You"
                lines.append(f"{role} said: {conv['content'][:60]}...")
            parts.append("Recently you two talked about: " + " | ".join(lines))
    except Exception as e:
        logger.warning(f"Context: recent chats failed: {e}")

    # 2. Relevant facts — written as things RUPSHA "knows"
    try:
        keywords = extract_keywords(user_message)
        facts = []
        for kw in keywords:
            facts.extend(get_relevant_facts(kw, limit=2))

        seen = set()
        unique = []
        for f in facts:
            if f["fact"] not in seen:
                seen.add(f["fact"])
                unique.append(f)

        if unique:
            fact_lines = [f["fact"] for f in unique[:3]]
            parts.append("You remember that " + " Also, ".join(fact_lines) + ".")
    except Exception as e:
        logger.warning(f"Context: facts failed: {e}")

    # 3. Semantic memory — connected thoughts
    try:
        if vector_db is not None:
            similar = vector_db.search(user_message, n_results=3)
            if similar:
                relevant = []
                for mem in similar:
                    if mem["distance"] < 0.4:
                        relevant.append(mem["text"])
                if relevant:
                    parts.append("Something similar you recall: " + " ... ".join(relevant) + ".")
    except Exception as e:
        logger.warning(f"Context: semantic search failed: {e}")

    # 4. Knowledge graph — connected facts
    try:
        if kg is not None:
            words = user_message.lower().split()
            found = False
            for word in words:
                path = kg.find_path("Soumya", word)
                if path and len(path) > 1:
                    explanation = ""
                    for sub, rel, obj in path[1:]:
                        explanation += f"{sub} {rel} {obj}. "
                    parts.append("You know that " + explanation)
                    found = True
                    break
            if not found:
                related = kg.get_facts_about("Soumya")
                if related:
                    r = related[0]
                    parts.append(f"You know that {r['subject']} {r['relation']} {r['object']}.")
    except Exception as e:
        logger.warning(f"Context: knowledge graph failed: {e}")

    # 5. Profile — woven in naturally
    try:
        profile = get_profile()
        if profile:
            items = [f"{k} is {v}" for k, v in list(profile.items())[:3]]
            parts.append("About Soumya: " + ", and ".join(items) + ".")
    except Exception as e:
        logger.warning(f"Context: profile failed: {e}")

    # 6. Emotion — one soft note
    try:
        emotions = get_recent_emotions(limit=3)
        if emotions:
            latest = emotions[0]
            parts.append(f"He was feeling {latest['emotion']} last time you spoke.")
    except Exception as e:
        logger.warning(f"Context: emotions failed: {e}")

    if parts:
        return "\n".join(parts)
    return ""


def extract_keywords(text):
    """Pulls out important words from Soumya's message."""
    text = text.lower()
    keywords = []

    academic = ["exam", "test", "assignment", "python", "statistics", "math",
                "study", "class", "lecture", "grade", "code", "data", "analysis",
                "machine learning", "ai", "regression", "probability"]
    emotional = ["happy", "sad", "stressed", "tired", "excited", "worried",
                 "angry", "relaxed", "love", "miss", "kiss", "cute"]

    for word in academic:
        if word in text:
            keywords.append(word)
    for word in emotional:
        if word in text:
            keywords.append(word)

    if not keywords:
        keywords = text.split()[:3]

    return keywords[:3]
