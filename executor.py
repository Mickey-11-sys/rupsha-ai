"""
executor.py
RUPSHA's hands + brain wiring. Runs steps, observes results, retries, remembers.
"""

import sys
import os

try:
    _D = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _D = '/content/RUPSHA'
if _D not in sys.path:
    sys.path.insert(0, _D)

from tools import create_default_toolkit
from observer import observe                      # EDIT: import observer
from retry_logic import retry_step, should_retry  # EDIT: import retry
from plan_memory import save_plan                 # EDIT: import memory

_toolkit = create_default_toolkit()


def _call_llm(prompt, temperature=0.3, max_tokens=800):
    """Helper to call Groq LLM for summarization and answer crafting."""
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM error: {e}"


def execute_step(step, previous_outputs=None):
    """
    Runs one step from the plan.
    step: dict like {"step": 1, "action": "search_web", "input": "latest AI news"}
    previous_outputs: dict of step_number -> result
    Returns: result string
    """

    action = step.get("action")
    input_data = step.get("input", "")

    # Replace step_N_output references with actual results
    if previous_outputs and isinstance(input_data, str):
        if input_data.startswith("step_") and "_output" in input_data:
            step_num = input_data.replace("step_", "").replace("_output", "")
            input_data = previous_outputs.get(f"step_{step_num}", input_data)

    # ═════════════════════════════════════════════════════════════════
    # ACTION DISPATCHER
    # Maps planner action names → registry tool names
    # ═════════════════════════════════════════════════════════════════
    if action == "search_web":
        result = _toolkit.execute("web_search", {"query": str(input_data)})

    elif action == "calculate":
        result = _toolkit.execute("calculator", {"expression": str(input_data)})

    elif action == "run_python":
        result = _toolkit.execute("python_executor", {"code": str(input_data)})

    elif action == "summarize":
        prompt = f"""You are RUPSHA, a warm companion. Summarize the following into a nice, readable summary for Soumya. Keep it friendly but informative:

{input_data}

Summary:"""
        result = _call_llm(prompt, temperature=0.3, max_tokens=600)

    elif action == "answer":
        prompt = f"""You are RUPSHA, a warm, playful, slightly naughty female companion talking to Soumya.
Share this information in a warm, teasing way. Use emojis. Call him by name.

Here is what you found:
{input_data}

Your reply (warm, playful, include the actual findings):"""
        result = _call_llm(prompt, temperature=0.7, max_tokens=800)

    else:
        result = f"❌ Unknown action: {action}"

    # Print a preview so you can see what happened
    preview = result[:200].replace("\n", " ") if result else "EMPTY"
    print(f"     📄 Result preview: {preview}...")

    return result


# ═══════════════════════════════════════════════════════════════════════
# EDIT: Replaced execute_plan with Observer + Retry + Memory version
# ═══════════════════════════════════════════════════════════════════════

def execute_plan(plan, original_request=""):
    """
    Runs all steps in order with Observer + Retry + Memory.
    EDIT: Added original_request param so Plan Memory knows what to save.
    Returns: (outputs dict, final_answer string)
    """
    outputs = {}
    final_answer = "Done!"
    plan_success = True  # EDIT: track if whole plan succeeded

    for step in plan:
        step_num = step.get("step", 0)
        action = step.get("action", "unknown")
        print(f"  🔧 Step {step_num}: {action}...")

        # EDIT: ─── OBSERVER + RETRY LOOP ─────────────────────────────
        attempt = 0
        current_step = step
        result = None

        while attempt <= 3:
            attempt += 1
            result = execute_step(current_step, outputs)

            # EDIT: Observer checks the result
            tool_name = {"search_web": "web_search", "calculate": "calculator", "run_python": "python_executor"}.get(action, action)
            verdict = observe(tool_name, result)

            if verdict["status"] == "pass":
                print(f"     ✅ Observer: PASS ({verdict['confidence']})")
                break  # Good result, move to next step

            # EDIT: Failed — should we retry?
            print(f"     ⚠️ Observer: FAIL — {verdict['reason']}")
            if not should_retry(verdict, attempt):
                plan_success = False
                break

            # EDIT: Try to fix the step
            new_step = retry_step(current_step, attempt, verdict)
            if new_step is None:
                plan_success = False
                break
            current_step = new_step
        # EDIT: ─── END RETRY LOOP ────────────────────────────────────

        outputs[f"step_{step_num}"] = result

        if action == "answer":
            final_answer = result

        # EDIT: If a non-answer step failed, craft honest reply and stop
        if not plan_success and action != "answer":
            final_answer = _call_llm(
                f"RUPSHA tried to help Soumya with '{original_request}' but a step failed. "
                f"Be warm, playful, and honest. Mention what went wrong: {result[:200]}",
                0.7, 600
            )
            break

        print(f"     ✅ Done")

    # EDIT: ─── SAVE SUCCESSFUL PLAN ─────────────────────────────────
    if plan_success and original_request:
        save_plan(original_request, plan)

    return outputs, final_answer
