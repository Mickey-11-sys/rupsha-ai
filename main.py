"""
RUPSHA AI — Entry Point (Phase 3)
"""
import sys
import os

if "RUPSHA" not in sys.path:
    sys.path.insert(0, "RUPSHA")

import logger
import memory
import ui

def main():
    logger.info("RUPSHA starting up...")
    try:
        memory.init_database()
        print("✅ RUPSHA is ready! Click the Gradio link below...")
        ui.launch()
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        print("\n" + "=" * 50)
        print("TROUBLESHOOTING:")
        print("1. Did you add GROQ_API_KEY to Colab Secrets?")
        print("2. Did you run all cells in order?")
        print("3. Is the RUPSHA folder created?")
        print("=" * 50)

if __name__ == "__main__":
    main()
