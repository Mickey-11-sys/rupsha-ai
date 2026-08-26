# ============================================================
# voice.py  —  RUPSHA's Clean Voice (No Technical Junk)
# ============================================================

import os
import re
import asyncio
import threading
import edge_tts


class VoiceModule:

    def __init__(self, groq_client):
        self.client = groq_client
        self.voice_folder = "/tmp/rupsha_voice"
        os.makedirs(self.voice_folder, exist_ok=True)

        self.voice_map = {
            'en': "en-GB-SoniaNeural",
            'bn': "bn-IN-TanishaaNeural",
        }

    def listen(self, audio_file_path):
        with open(audio_file_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                response_format="text"
            )
        return response

    def speak(self, text):
        if not text or not text.strip():
            return None

        clean_text = self._clean_for_voice(text)
        if not clean_text:
            return None

        # FINAL GUARD: strip any technical junk still at the start
        clean_text = self._strip_technical_start(clean_text)
        if not clean_text:
            return None

        lang = self._detect_lang(clean_text)
        voice_name = self.voice_map.get(lang, "en-GB-SoniaNeural")

        filename = f"reply_{os.urandom(4).hex()}.mp3"
        output_path = os.path.join(self.voice_folder, filename)

        try:
            self._run_tts_thread(clean_text, voice_name, output_path)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"🔊 Voice ready ({os.path.getsize(output_path)} bytes)")
                return output_path
            return None

        except Exception as e:
            print(f"❌ TTS failed: {e}")
            return None

    def _run_tts_thread(self, text, voice, output_path):
        def _async_worker():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._edge_generate(text, voice, output_path))
            finally:
                loop.close()

        t = threading.Thread(target=_async_worker)
        t.start()
        t.join()

    async def _edge_generate(self, text, voice, output_path):
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    # ---------- AGGRESSIVE CLEANING ----------
    def _clean_for_voice(self, text):
        text = self._remove_emojis(text)
        text = re.sub(r'\*\*|\*|__|_|`', '', text)
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]+`', '', text)
        text = re.sub(r'[━┏┓┗┛┃┣┫┳┻╋═║╔╗╚╝]', ' ', text)
        text = re.sub(r'={5,}', ' ', text)
        text = re.sub(r'-{5,}', ' ', text)

        # Remove system leakage
        text = re.sub(r'🌸\s*RUPSHA.*?NEVER FORGET:.*?(?=\n|$)', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'You are RUPSHA, Soumya\'s warm.*?(?=\n|$)', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Remove mechanical prefixes
        mechanical = [
            r'As an AI language model[,\.]?',
            r'As an AI assistant[,\.]?',
            r'As RUPSHA[,\.]?',
            r'As your (AI )?companion[,\.]?',
            r'I am RUPSHA[,\.]?',
            r'Sure[,\!\.]+ I (can|will|am)',
            r'Here is (my response|what I think)[:\.]?',
            r'Response[:\.]?',
            r'Answer[:\.]?',
            r'Note[:\.]?',
            r'Okay[,\.]?',
            r'Alright[,\.]?',
            r'Well[,\.]?',
        ]
        for pattern in mechanical:
            text = re.sub(pattern, '', text, count=1, flags=re.IGNORECASE)

        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        if len(text) > 800:
            text = text[:797] + "..."
        return text

    # ---------- FINAL SAFETY NET ----------
    def _strip_technical_start(self, text):
        """
        If the text still starts with technical junk (all caps, brackets, colons),
        strip everything up to the first normal sentence.
        """
        # Check if start looks technical
        technical_pattern = re.compile(
            r'^[^a-zA-Z]*(?:'
            r'WEB|SEARCH|SYSTEM|ASSISTANT|BOT|AI|USER|RESPONSE|ANSWER|'
            r'NOTE|DISCLAIMER|HERE IS|CALC|CODE|ERROR|RESULTS|'
            r'\[|\]|\(|\)|=|:|_|>|\||'
            r'🌸|━|═'
            r')[^.!?]*[.!?]?\s*',
            re.IGNORECASE
        )

        # Apply up to 3 times to catch layered junk
        for _ in range(3):
            new_text = technical_pattern.sub('', text)
            if new_text == text:
                break
            text = new_text

        return text.strip()

    def _remove_emojis(self, text):
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"
            "\U0001FA00-\U0001FA6F"
            "\U00002600-\U000026FF"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub(r' ', text)

    def _detect_lang(self, text):
        for char in text:
            if '\u0980' <= char <= '\u09FF':
                return 'bn'
        return 'en'
