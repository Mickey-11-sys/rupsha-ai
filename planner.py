
"""
planner.py
RUPSHA's project manager. Breaks big tasks into steps.
"""

import sys
import os
import json
import re

import config
BASE_DIR = config.BASE_DIR
USER_NAME = config.USER_NAME

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq import Groq


def _is_simple_chat(user_request):
    """
    Quick check: is this just casual conversation?
    Returns True if we should skip planning entirely.
    """
    user_lower = user_request.lower().strip()

    chat_phrases = [
        "how are you", "i miss you", "i love you", "tell me a joke",
        "what's up", "whats up", "sup", "hii", "hello", "hey",
        "good morning", "good night", "good evening", "good afternoon",
        "you are cute", "you're cute", "you are beautiful", "you're beautiful",
        "i'm sad", "i'm happy", "i'm tired", "i'm bored",
        "how was your day", "did you miss me", "do you love me",
        "bby", "baby", "darling", "sweetheart", "my love"
    ]

    for phrase in chat_phrases:
        if phrase in user_lower:
            return True

    words = user_lower.split()
    if len(words) <= 3:
        math_words = ["calculate", "compute", "sum", "plus", "minus", "times", "divided"]
        search_words = ["search", "find", "look up", "what is", "who is", "when is"]
        if not any(w in user_lower for w in math_words + search_words):
            return True

    return False


def _extract_math(text):
    """
    Pulls out clean math expressions from natural language.
    """
    clean = text.lower()
    replacements = [
        ("calculate", ""), ("compute", ""), ("what is", ""),
        ("plus", "+"), ("minus", "-"), ("times", "*"), ("divided by", "/"),
        ("multiplied by", "*"), ("and", ""), ("then", ""),
    ]
    for old, new in replacements:
        clean = clean.replace(old, new)

    expressions = []
    pattern = r"[\d\s\.\+\-\*/\(\)]+"
    matches = re.findall(pattern, clean)

    for match in matches:
        expr = match.strip()
        expr = re.sub(r"[+\-*/\s]+$", "", expr)
        digits = re.findall(r"\d", expr)
        operators = re.findall(r"[+\-*/]", expr)
        if len(digits) >= 2 and len(operators) >= 1 and len(expr) >= 3:
            expressions.append(expr)

    return expressions


def create_plan(user_request):
    """
    Asks the LLM to break the user's request into steps.
    Returns: list of step dicts, or empty list for simple chat.
    """

    if _is_simple_chat(user_request):
        return []

    math_expressions = _extract_math(user_request)
    if len(math_expressions) >= 2:
        steps = []
        for i, expr in enumerate(math_expressions, 1):
            steps.append({
                "step": i,
                "action": "calculate",
                "input": expr
            })
        steps.append({
            "step": len(math_expressions) + 1,
            "action": "answer",
            "input": f"Here are the results: " + " then ".join([f"step_{i}_output" for i in range(1, len(math_expressions)+1)])
        })
        return steps

    client = Groq(api_key=config.GROQ_API_KEY)

    system_prompt = f"""You are RUPSHA's internal planner. Your job is ONLY to break tasks into steps.
You receive {USER_NAME}'s request and output a JSON list of steps.

CRITICAL RULE: If the request is simple chat, greeting, emotional talk, flirting, or casual conversation, output: []
Create a plan ONLY if the request involves ANY of these:
- Finding/searching/looking up information
- Calculating math
- Running Python code
- Multiple actions combined (search AND summarize, calculate AND explain, etc.)

Available actions:
- search_web: search the internet for current info
- calculate: do math (use clean expressions like "10 + 20", not full sentences)
- run_python: execute Python code
- summarize: summarize text into a nice reply
- answer: give a final warm reply to {USER_NAME}

Rules:
1. Output ONLY valid JSON. No extra text, no markdown.
2. If simple chat -> output: []
3. Each step must use one of the available actions.
4. If a step needs the output of a previous step, use "input": "step_N_output"
5. Keep steps simple — one action per step.
6. For calculate steps, use ONLY the math expression, no words.

Example 1:
Request: "How are you?"
Output: []

Example 2:
Request: "Find latest AI news and tell me"
Output: [
  {{"step": 1, "action": "search_web", "input": "latest AI news 2026"}},
  {{"step": 2, "action": "summarize", "input": "step_1_output"}},
  {{"step": 3, "action": "answer", "input": "step_2_output"}}
]

Example 3:
Request: "Calculate 10 + 20"
Output: [
  {{"step": 1, "action": "calculate", "input": "10 + 20"}},
  {{"step": 2, "action": "answer", "input": "step_1_output"}}
]"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Request: {user_request}\nOutput:"}
    ]

    try:
        response = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=messages,
            temperature=0.1,
            max_tokens=config.MAX_TOKENS,
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else parts[0]
            if raw.startswith("json"):
                raw = raw[4:]

        plan = json.loads(raw.strip())

        if not isinstance(plan, list):
            return None

        return plan

    except Exception as e:
        print(f"Planner error: {e}")
        return None


if __name__ == "__main__":
    test = create_plan("Find latest AI news and tell me")
    print(json.dumps(test, indent=2))
