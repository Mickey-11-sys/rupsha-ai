"""
config.py
Works in Local, Colab, AND Hugging Face.
"""

import os
from dotenv import load_dotenv

# ── Step 1: Load .env file if it exists ──
load_dotenv()

# ── Step 2: Try Colab Secrets ──
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    try:
        from google.colab import userdata
        GROQ_API_KEY = userdata.get("GROQ_API_KEY")
        print("✅ Loaded GROQ_API_KEY from Colab Secrets")
    except Exception:
        pass

# ── Step 3: Final check ──
if not GROQ_API_KEY:
    print("⚠️  WARNING: GROQ_API_KEY not found.")
    print("   Add it to Colab Secrets (key icon on the left sidebar)")

# ── AI SETTINGS ──
MODEL_NAME = os.environ.get("MODEL_NAME", "openai/gpt-oss-120b")
MAX_TOKENS = 1024
TEMPERATURE = 0.7
MAX_HISTORY = 20

# ── IDENTITY ──
AGENT_NAME = "RUPSHA"
USER_NAME = os.environ.get("USER_NAME", "Friend")

# ── BENGALI ──
BENGALI_PRONOUN_STYLE = os.environ.get("BENGALI_PRONOUN_STYLE", "informal")

# ── PATHS ──
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.getcwd()

LOG_FILE = os.path.join(BASE_DIR, "rupsha_log.txt")
DB_FILE = os.path.join(BASE_DIR, "rupsha_memory.db")
VECTOR_DB_PATH = os.path.join(BASE_DIR, "data", "vector_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
os.makedirs(VECTOR_DB_PATH, exist_ok=True)
