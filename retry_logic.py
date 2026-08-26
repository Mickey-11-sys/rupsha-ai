"""
retry_logic.py
When a step fails, RUPSHA tries a smarter approach. Max 3 retries.
"""

import re


def _rephrase_search(query: str, attempt: int) -> str:
    """Makes search query broader."""
    query = query.strip()
    if attempt == 1:
        simple = re.sub(r'\b(find|search|look for|get me|show me|tell me about|the|latest|current|recent)\b', '', query, flags=re.IGNORECASE)
        simple = re.sub(r'\s+', ' ', simple).strip()
        return simple if simple else query + " tutorial"
    if attempt == 2:
        return query + " beginner guide"
    words = query.split()
    return " ".join(words[:3]) if len(words) > 3 else query + " explained"


def _fix_math(expression: str, attempt: int) -> str:
    """Cleans messy math expressions."""
    expr = expression.lower()
    for word in ["calculate", "compute", "what is", "find", "then", "and", "now"]:
        expr = expr.replace(word, "")
    expr = expr.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("multiplied by", "*").replace("divided by", "/")
    cleaned = re.sub(r'[^\d\+\-\*/\.\s\(\)]', '', expr)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'[\+\-\*/\s]+$', '', cleaned)
    return cleaned if cleaned and len(cleaned) >= 3 else "0 + 0"


def _fix_python(code: str, attempt: int) -> str:
    """Adds print() if missing."""
    if "print(" not in code:
        lines = code.strip().split('\n')
        last = lines[-1].strip()
        if last and not last.startswith(("print", "#", "import")):
            lines[-1] = f"print({last})"
            return '\n'.join(lines)
    return code


def retry_step(step: dict, attempt: int, observer_result: dict) -> dict:
    """Takes a failed step and creates a better version. Returns new step or None."""
    if attempt > 3:
        return None

    action = step.get("action")
    original_input = step.get("input", "")

    if action == "search_web":
        new_input = _rephrase_search(str(original_input), attempt)
        print(f"     🔄 Retry {attempt}: '{new_input}'")
        return {"step": step.get("step"), "action": "search_web", "input": new_input}

    elif action == "calculate":
        new_input = _fix_math(str(original_input), attempt)
        print(f"     🔄 Retry {attempt}: '{new_input}'")
        return {"step": step.get("step"), "action": "calculate", "input": new_input}

    elif action == "run_python":
        new_input = _fix_python(str(original_input), attempt)
        print(f"     🔄 Retry {attempt}: Python adjusted")
        return {"step": step.get("step"), "action": "run_python", "input": new_input}

    elif action in ("summarize", "answer"):
        print(f"     🔄 Retry {attempt}: LLM step failed. Cannot retry directly.")
        return None

    else:
        print(f"     🔄 Retry {attempt}: Unknown action '{action}'. Giving up.")
        return None


def should_retry(observer_result: dict, attempt: int) -> bool:
    """Checks if failure is worth retrying."""
    reason = observer_result.get("reason", "").lower()
    permanent = ["api key invalid", "rate limit", "blocked", "forbidden", "timeout after", "connection refused", "tool not found"]
    for signal in permanent:
        if signal in reason:
            print(f"     🚫 Permanent failure: {signal}. No retry.")
            return False
    if observer_result.get("confidence") == 0 and attempt >= 2:
        print(f"     🚫 Hard error on attempt {attempt}. Giving up.")
        return False
    return True
