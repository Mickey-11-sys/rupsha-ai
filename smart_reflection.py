
import json
from groq import Groq
import config

client = Groq(api_key=config.GROQ_API_KEY)
USER_NAME = config.USER_NAME

def extract_facts(conversation_text):
    """
    Read a conversation and extract structured facts about the user.
    """
    if not conversation_text or len(conversation_text.strip()) < 20:
        return []

    prompt = f"""You are a memory extraction system. Read the conversation and extract facts about the user.

Conversation:
{conversation_text}

Extract facts in this EXACT JSON format. No extra text. Only JSON:
[
  {{"subject": "{USER_NAME}", "relation": "feels", "object": "stressed about exam", "confidence": 0.9}},
  {{"subject": "{USER_NAME}", "relation": "has_exam", "object": "Statistics", "confidence": 0.95}}
]

Rules:
- Subject is usually "{USER_NAME}" or "User".
- Relation is a simple verb: feels, has, likes, dislikes, studies, wants, etc.
- Object is the detail.
- Confidence: 0.0 (guess) to 1.0 (certain).
- If no clear facts, return an empty list: []
- Return ONLY valid JSON. No markdown, no explanation.
"""

    try:
        response = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You extract structured facts from conversations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```"):
            parts = content.split("```")
            for part in parts:
                clean = part.replace("json", "").strip()
                if clean.startswith("["):
                    content = clean
                    break

        facts = json.loads(content)

        if not isinstance(facts, list):
            return []

        good_facts = [f for f in facts if f.get("confidence", 0) > 0.6]
        return good_facts

    except Exception as e:
        print(f"Smart reflection error: {e}")
        return []

def format_facts_for_graph(facts):
    """
    Convert extracted facts into triples for the knowledge graph.
    """
    triples = []
    for fact in facts:
        sub = fact.get("subject", USER_NAME)
        rel = fact.get("relation", "related_to")
        obj = fact.get("object", "")
        if sub and rel and obj:
            triples.append((sub, rel, obj))
    return triples
