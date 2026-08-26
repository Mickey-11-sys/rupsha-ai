"""
observer.py
RUPSHA's quality checker. Every tool result passes through here.
"""

def observe(tool_name: str, raw_result: str) -> dict:
    """
    Checks if a tool result is good enough to trust.
    Returns: {"status": "pass" or "fail", "confidence": 0.0-1.0, "reason": "...", "suggestion": "..."}
    """
    if raw_result is None or raw_result == "":
        return {"status": "fail", "confidence": 0.0, "reason": "Tool returned nothing", "suggestion": "Try broader keywords"}

    result = str(raw_result).strip()

    # Hard error
    if result.startswith("❌"):
        return {"status": "fail", "confidence": 0.0, "reason": result[:80], "suggestion": "Check parameters"}

    # Empty search
    empty_signals = ["no results found", "no results", "nothing found", "0 results"]
    if any(s in result.lower() for s in empty_signals):
        return {"status": "fail", "confidence": 0.1, "reason": "Search returned zero results", "suggestion": "Try broader keywords"}

    # Too short
    if len(result) < 20:
        return {"status": "fail", "confidence": 0.2, "reason": f"Too short ({len(result)} chars)", "suggestion": "Try again"}

    # Python no output
    if tool_name == "python_executor" and "no output" in result.lower():
        return {"status": "fail", "confidence": 0.3, "reason": "Python ran but no output", "suggestion": "Add print() statements"}

    # Calculator error
    if tool_name == "calculator" and "error" in result.lower():
        return {"status": "fail", "confidence": 0.0, "reason": "Calculator error", "suggestion": "Use clean math like '10 + 20'"}

    # All good
    confidence = min(0.5 + (len(result) / 2000), 0.95)
    return {"status": "pass", "confidence": round(confidence, 2), "reason": f"Good result ({len(result)} chars)", "suggestion": None}
