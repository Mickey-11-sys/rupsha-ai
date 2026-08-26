# ============================================================
# file_handler.py  —  RUPSHA's Hands (Any File Type)
# ============================================================

import os
import base64


class FileHandler:

    def process(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return "none", None

        ext = os.path.splitext(file_path)[1].lower()

        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']:
            return "image", self._encode_image(file_path)

        if ext == '.pdf':
            return "text", self._read_pdf(file_path)

        if ext in ['.py', '.txt', '.js', '.html', '.css', '.json', '.md',
                   '.csv', '.java', '.cpp', '.c', '.h', '.sql', '.xml',
                   '.yaml', '.yml', '.ini', '.cfg', '.log', '.r', '.ipynb']:
            return "text", self._read_text(file_path)

        try:
            return "text", self._read_text(file_path)
        except Exception as e:
            return "error", f"Unsupported file ({ext}): {e}"

    def _encode_image(self, path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        ext = os.path.splitext(path)[1].lower()
        mime = "image/jpeg" if ext in ['.jpg', '.jpeg'] else \
               "image/png" if ext == '.png' else \
               "image/webp" if ext == '.webp' else "image/jpeg"
        return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}

    def _read_text(self, path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if len(text) > 6000:
            text = text[:6000] + "\n\n[...file truncated...]"
        return text

    def _read_pdf(self, path):
        try:
            import PyPDF2
            text = ""
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if not text.strip():
                return "[PDF contains no extractable text]"
            if len(text) > 5000:
                text = text[:5000] + "\n\n[...PDF truncated...]"
            return text
        except ImportError:
            return "[PyPDF2 not installed. Run: !pip install PyPDF2]"
        except Exception as e:
            return f"[PDF read error: {e}]"
