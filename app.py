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
init_database()
from ui import demo

print("=" * 50)
print("🌸 RUPSHA on Hugging Face")
print("=" * 50)
if config.GROQ_API_KEY:
    print("✅ GROQ_API_KEY found")
else:
    print("❌ GROQ_API_KEY missing! Add it in Settings → Secrets")
print(f"👤 User: {config.USER_NAME}")
print(f"🤖 Model: {config.MODEL_NAME}")
print("=" * 50)
