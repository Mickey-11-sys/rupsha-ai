# ============================================================
# vision.py  —  RUPSHA's Eyes
# ============================================================
# WHAT:  Encodes images for Groq's vision model
# WHY:   So RUPSHA can see photos, graphs, screenshots, memes
# HOW:   Converts image → base64 data URL for the LLM
# ============================================================

import base64
import os


class VisionModule:
    """
    RUPSHA's eyes. One helper: prepare_image_message.
    The actual 'seeing' happens in brain.py using Groq vision API.
    """

    def __init__(self, groq_client):
        self.client = groq_client

    def prepare_image_message(self, image_path):
        """
        WHAT:  Reads an image file and returns the API-ready image block.
        WHY:   Groq vision needs base64-encoded images inside the message.
        HOW:   Detects file type, encodes to base64, returns dict.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')

        ext = os.path.splitext(image_path)[1].lower()
        if ext in ['.jpg', '.jpeg']:
            mime = "image/jpeg"
        elif ext == '.png':
            mime = "image/png"
        elif ext == '.webp':
            mime = "image/webp"
        else:
            mime = "image/jpeg"  # fallback

        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime};base64,{b64}"
            }
        }
