"""
app.py
Hugging Face Spaces entry point.
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")
os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'

def find_rupsha_folder():
    try:
        folder = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(os.path.join(folder, "config.py")):
            return folder
    except NameError:
        pass
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "config.py")):
        return cwd
    for sub in ["RUPSHA", "rupsha-public"]:
        path = os.path.join(cwd, sub)
        if os.path.exists(os.path.join(path, "config.py")):
            return path
    return cwd

BASE_DIR = find_rupsha_folder()
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import config
from memory import init_database
from ui import demo

if not config.GROQ_API_KEY:
    print("⚠️ WARNING: GROQ_API_KEY not set. Add it in Settings → Secrets")

init_database()

print("=" * 50)
print("🌸 RUPSHA on Hugging Face")
print("=" * 50)
if config.GROQ_API_KEY:
    print("✅ GROQ_API_KEY found")
else:
    print("❌ GROQ_API_KEY missing!")
print(f"👤 User: {config.USER_NAME}")
print(f"🤖 Model: {config.MODEL_NAME}")
print("=" * 50)

# ============================================
# THIS IS THE MISSING PART — ADD IT
# ============================================
if __name__ == "__main__":
    print("🚀 Starting Gradio server...")
    demo.launch(
        share=True,
        server_name="0.0.0.0",
        server_port=7860
    )
