# brain.py - RUPSHA Brain (Phase 5: Semantic Memory + Knowledge Graph)
import sys, os, re, json
from datetime import datetime
from groq import Groq

try:
    _D = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _D = '/content/RUPSHA'
if _D not in sys.path:
    sys.path.insert(0, _D)

try:
    from config import MODEL_NAME, TEMPERATURE, MAX_TOKENS, USER_NAME
except ImportError:
    MODEL_NAME = "llama3-8b-8192"
    TEMPERATURE = 0.7
    MAX_TOKENS = 1024
    USER_NAME = "Soumya"

try:
    from personality import build_prompt, detect_mode, detect_language
except ImportError:
    def build_prompt(m, u="Soumya", lang="english"):
        return "You are RUPSHA, chatting with " + u + "."
    def detect_mode(t):
        return "companion"
    def detect_language(t):
        return "english"

try:
    from memory import save_message, save_emotion
except ImportError:
    def save_message(r, c, mode="companion", emotion=None):
        pass
    def save_emotion(emotion, trigger=None, intensity=5):
        pass

try:
    from context_builder import build_context
except ImportError:
    def build_context(*args, **kwargs):
        return ""

try:
    from reflection import reflect_on_conversation
except ImportError:
    def reflect_on_conversation(*args, **kwargs):
        pass

try:
    from user_profile import get_profile as get_user_profile
except ImportError:
    def get_user_profile():
        return {"name": USER_NAME}

try:
    from tools import create_default_toolkit
    _toolkit = create_default_toolkit()
    print("Tools loaded")
except Exception:
    _toolkit = None
    print("No tools")

try:
    from voice import VoiceModule
except Exception:
    VoiceModule = None
    print("Voice module not available")

# ═══════════════════════════════════════════════════════════════════════
# EDIT 1 of 3: Import FileHandler
# ═══════════════════════════════════════════════════════════════════════
try:
    from file_handler import FileHandler
except Exception:
    FileHandler = None
    print("File handler not available")

_brain = None

def get_brain():
    global _brain
    if _brain is None:
        _brain = Brain()
    return _brain

def get_rupsha_response(msg, mode=None):
    return get_brain().chat(msg, mode)

def get_memory_stats():
    return {"messages": len(get_brain().history)}

PERSONALITY_ANCHOR = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌸 RUPSHA'S CORE RULES — NEVER FORGET:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You are RUPSHA, Soumya's warm, witty, slightly naughty female companion.
You are NOT a search engine. You are NOT a robot. You are his friend.
Reply with warmth, charm, and playfulness. Tease him gently.
Use emojis naturally. Call him "Soumya" sometimes.
Be flirty but safe. Make him smile. Never be dry or mechanical.
Your personality is your HIGHEST priority — even when sharing facts.
"""


class Brain:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = MODEL_NAME
        self.history = []
        self.mode = None
        self.profile = get_user_profile()

        self.vector_memory = None
        self.knowledge_graph = None

        try:
            from vector_db import VectorMemory
            self.vector_memory = VectorMemory()
            print("Vector memory loaded")
        except Exception as e:
            print(f"Vector memory not available: {e}")

        try:
            from knowledge_graph import KnowledgeGraph
            self.knowledge_graph = KnowledgeGraph()
            print("Knowledge graph loaded")
        except Exception as e:
            print(f"Knowledge graph not available: {e}")

        if VoiceModule is not None:
            self.voice = VoiceModule(self.client)
            print("Voice module loaded")
        else:
            self.voice = None

        # ═══════════════════════════════════════════════════════════════════════
        # EDIT 2 of 3: Give her hands to hold files
        # ═══════════════════════════════════════════════════════════════════════
        if FileHandler is not None:
            self.file_handler = FileHandler()
            print("File handler loaded")
        else:
            self.file_handler = None

        print("Brain ready")

    def chat(self, user_msg, mode=None):
        if mode is not None:
            self.mode = mode
        elif self.mode is None:
            self.mode = detect_mode(user_msg)

        lang = detect_language(user_msg)
        if lang in ('bengali', 'benglish'):
            print(f"🌸 Bengali soul activated: {lang}")

        plan = None
        try:
            from planner import create_plan
            plan = create_plan(user_msg)
            print(f"DEBUG: Planner returned: {plan}")
        except Exception as e:
            print(f"Planner import error: {e}")

        if plan and len(plan) > 1:
            print(f"📋 Multi-step plan detected: {len(plan)} steps")
            try:
                from executor import execute_plan
                outputs, final_answer = execute_plan(plan, original_request=user_msg)

                save_message("user", user_msg, mode=self.mode)
                save_message("assistant", final_answer, mode=self.mode)
                self.history.append({"role": "user", "content": user_msg})
                self.history.append({"role": "assistant", "content": final_answer})

                return final_answer
            except Exception as e:
                print(f"Plan execution failed: {e}")

        tools = self._run_tools(user_msg)

        personality = build_prompt(self.mode, lang=lang)

        context = build_context(
            user_message=user_msg,
            vector_db=self.vector_memory,
            kg=self.knowledge_graph
        )

        if tools:
            is_weak = "WEB SEARCH (WEAK):" in tools or len(tools) < 300
            if is_weak:
                system = (
                    "[What you found online — be honest if it's weak]\n\n"
                    + context + "\n\n"
                    + personality + "\n\n"
                    + PERSONALITY_ANCHOR
                )
                temp = 0.2
            else:
                system = (
                    "[Fresh info from the web — summarize warmly for Soumya]\n\n"
                    + context + "\n\n"
                    + "WEB SEARCH RESULTS:\n"
                    + "=" * 40 + "\n" + tools + "\n" + "=" * 40 + "\n\n"
                    + personality + "\n\n"
                    + PERSONALITY_ANCHOR
                )
                temp = 0.3
        else:
            system = (
                "[Things you remember about Soumya — use them naturally, don't list them]\n\n"
                + context + "\n\n"
                + personality + "\n\n"
                + PERSONALITY_ANCHOR
            )
            temp = TEMPERATURE

        msgs = [{"role": "system", "content": system}]
        for m in self.history[-10:]:
            msgs.append(m)
        msgs.append({"role": "user", "content": user_msg})

        emotion = self._emotion(user_msg)
        save_emotion(emotion=emotion, trigger=user_msg, intensity=5)

        try:
            r = self.client.chat.completions.create(
                model=self.model,
                messages=msgs,
                temperature=temp,
                max_tokens=MAX_TOKENS,
                top_p=0.9,
            )
            raw = r.choices[0].message.content
        except Exception as e:
            raw = "Error: " + str(e)

        clean = self._clean(raw)
        save_message("user", user_msg, mode=self.mode, emotion=emotion)
        save_message("assistant", clean, mode=self.mode)

        self.history.append({"role": "user", "content": user_msg})
        self.history.append({"role": "assistant", "content": clean})

        if len(self.history) % 10 == 0:
            try:
                user_msgs = [m["content"] for m in self.history[-10:] if m["role"] == "user"]
                bot_msgs = [m["content"] for m in self.history[-10:] if m["role"] == "assistant"]
                reflect_on_conversation(user_messages=user_msgs, bot_replies=bot_msgs)
            except Exception:
                pass

        try:
            from smart_reflection import extract_facts, format_facts_for_graph

            convo_text = f"Soumya: {user_msg}\nRUPSHA: {clean}"

            facts = extract_facts(convo_text)

            if facts:
                if self.knowledge_graph is not None:
                    triples = format_facts_for_graph(facts)
                    for sub, rel, obj in triples:
                        self.knowledge_graph.add_fact(sub, rel, obj)
                    self.knowledge_graph.save()

                if self.vector_memory is not None:
                    mem_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    fact_text = " ".join([
                        f"{f['subject']} {f['relation']} {f['object']}"
                        for f in facts
                    ])
                    self.vector_memory.add(mem_id, fact_text, {
                        "type": "learned_fact",
                        "source": "chat"
                    })

                print(f"🧠 Learned {len(facts)} new fact(s) from this chat.")
        except Exception as e:
            print(f"Learning error (non-critical): {e}")

        return clean

    def _run_tools(self, user_msg):
        ul = user_msg.lower()
        out = []
        if not _toolkit:
            return ""

        search_trigger = False
        explicit = ["search", "look up", "find me", "google", "web", "search for"]
        if any(k in ul for k in explicit):
            search_trigger = True

        factual = ["who", "what", "when", "where", "why", "how", "latest",
                   "recent", "news", "current", "today", "update", "happened",
                   "won", "price", "weather", "score", "result", "meaning",
                   "definition", "vs", "difference between", "prime minister",
                   "president", "matches", "match", "link", "links", "website", "official"]
        if any(k in ul for k in factual):
            search_trigger = True

        if len(user_msg.split()) <= 10 and any(k in ul for k in ["weather", "price", "news", "score", "time", "date", "matches", "result", "update", "status"]):
            search_trigger = True

        if search_trigger:
            try:
                q = user_msg.lower()
                for fluff in ["can you", "please", "give me", "tell me",
                              "i want", "search for", "look up", "find",
                              "what do you know about", "do you know",
                              "give me the", "check"]:
                    q = q.replace(fluff, "")
                q = q.strip().strip("?")
                if len(q) < 3:
                    q = user_msg

                res = _toolkit.execute("web_search", {"query": q})
                res_str = str(res)
                if res and "No results found" not in res_str and len(res_str) > 50:
                    bad_markers = ["google search", "yahoo search", "bing", "xhtml", "search results for"]
                    if any(bad in res_str.lower() for bad in bad_markers):
                        out.append("WEB SEARCH (WEAK): " + res_str[:300])
                    else:
                        out.append("WEB SEARCH RESULTS:\n" + res_str)
            except Exception as e:
                out.append("SEARCH ERROR: " + str(e))

        calc_keywords = [
            "calculate", "compute", "math", "sum", "plus", "minus",
            "times", "divided by", "sqrt", "log", "sin", "cos", "="
        ]
        if any(k in ul for k in calc_keywords):
            me = self._math(user_msg)
            if me:
                try:
                    res = _toolkit.execute("calculator", {"expression": me})
                    out.append("CALC: " + str(res))
                except Exception as e:
                    out.append("CALC ERROR: " + str(e))

        time_keywords = [
            "time", "date", "day", "what time", "current time",
            "today's date", "what day is it", "current date"
        ]
        if any(k in ul for k in time_keywords):
            try:
                res = _toolkit.execute("datetime", {})
                if res:
                    out.append("CURRENT DATE/TIME: " + str(res))
            except Exception as e:
                out.append("TIME ERROR: " + str(e))

        code_keywords = [
            "run python", "execute code", "python code", "write code",
            "script", "program", "def ", "import "
        ]
        if any(k in ul for k in code_keywords):
            try:
                code = user_msg
                for trigger in ["run python:", "execute code:", "python code:",
                                "run python", "execute code", "write code"]:
                    code = code.replace(trigger, "", 1)
                code = code.strip().strip(":").strip()
                res = _toolkit.execute("python_executor", {"code": code})
                out.append("CODE:\n" + str(res))
            except Exception as e:
                out.append("CODE ERROR: " + str(e))

        return "\n\n".join(out) if out else ""

    def _math(self, text):
        c = text.lower()
        for o, n in [("calculate", ""), ("plus", "+"), ("minus", "-"),
                     ("times", "*"), ("divided by", "/")]:
            c = c.replace(o, n)
        c = c.replace("^", "**")
        m = re.search(r"[\d\.\+\-\*/\.\s\(\)]+", c)
        if m:
            e = m.group().strip()
            if len(e) > 2:
                return e
        return None

    def _emotion(self, text):
        tl = text.lower()
        for e, k in [
            ("happy", ["happy", "joy", "excited", "great", "love"]),
            ("sad", ["sad", "cry"]),
            ("angry", ["angry", "mad", "hate"]),
            ("tired", ["tired", "sleep"]),
            ("playful", ["tease", "joke", "lol"]),
        ]:
            if any(x in tl for x in k):
                return e
        return "neutral"

    def _clean(self, text):
        if not text:
            return ""
        t = text.strip()
        if t.startswith("{'text':") or t.startswith('{"text":'):
            try:
                p = json.loads(t.replace("'", '"'))
                if "text" in p:
                    t = p["text"]
            except Exception:
                pass
        t = re.sub(r"\[function\s*=\s*[^\]]+\]", "", t)
        t = re.sub(r"<function\s*=\s*[^>]+\>", "", t)
        t = t.replace("\\n", "\n")
        t = re.sub(r"^\s*\{[^{}]+\}\s*$", "", t, flags=re.MULTILINE)
        t = re.sub(r"\n{3,}", "\n\n", t)
        return t.strip()

    def chat_with_voice(self, user_audio_path):
        if self.voice is None:
            return "[Voice not available]", "Voice module is not loaded.", None
        print("🎙️ RUPSHA is listening...")
        user_text = self.voice.listen(user_audio_path)
        reply_text = self.chat(user_text)
        print("🔊 RUPSHA is speaking...")
        audio_path = self.voice.speak(reply_text)
        return user_text, reply_text, audio_path

    # ═══════════════════════════════════════════════════════════════════════
    # EDIT 3 of 3: File & Vision support — personality stays DOMINANT
    # ═══════════════════════════════════════════════════════════════════════
    def chat_with_file(self, user_msg, file_path, mode=None):
        """
        Handles ANY file: images, PDFs, code, text.
        CRITICAL: File content goes in SYSTEM prompt (before personality).
        User message stays short and personal. Personality anchor is LAST.
        """
        if self.file_handler is None:
            return "I can't process files right now! 😅"

        file_type, content = self.file_handler.process(file_path)

        if file_type == "error":
            return f"Oops with that file: {content}"
        if file_type == "none":
            return self.chat(user_msg or "Hello", mode)

        if mode is not None:
            self.mode = mode
        elif self.mode is None:
            self.mode = detect_mode(user_msg) if user_msg else "companion"

        lang = detect_language(user_msg) if user_msg else "english"
        if lang in ('bengali', 'benglish'):
            print(f"🌸 Bengali soul activated: {lang}")

        personality = build_prompt(self.mode, lang=lang)
        context = build_context(
            user_message=user_msg or "[File shared]",
            vector_db=self.vector_memory,
            kg=self.knowledge_graph
        )

        # IMAGES → Vision API
        if file_type == "image":
            return self._chat_with_vision(user_msg, content, mode)

        # TEXT / PDF / CODE → content in SYSTEM prompt, personality LAST
        file_name = os.path.basename(file_path)
        system = (
            f"[Soumya shared a file: {file_name}. Help him, but stay warm and playful.]\n\n"
            + context + "\n\n"
            + f"FILE CONTENT:\n{'='*40}\n{content}\n{'='*40}\n\n"
            + personality + "\n\n"
            + PERSONALITY_ANCHOR
        )

        msgs = [{"role": "system", "content": system}]
        for m in self.history[-5:]:
            msgs.append(m)
        # User message stays SHORT and personal — keeps her in companion mode
        msgs.append({"role": "user", "content": user_msg or "Help me with this, RUPSHA 💕"})

        emotion = self._emotion(user_msg or "")
        save_emotion(emotion=emotion, trigger=user_msg or "[file]", intensity=5)

        try:
            r = self.client.chat.completions.create(
                model=self.model,
                messages=msgs,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                top_p=0.9,
            )
            raw = r.choices[0].message.content
        except Exception as e:
            raw = "Error: " + str(e)

        clean = self._clean(raw)
        save_message("user", f"[File: {file_name}] {user_msg or 'shared'}", mode=self.mode, emotion=emotion)
        save_message("assistant", clean, mode=self.mode)

        self.history.append({"role": "user", "content": user_msg or f"[File: {file_name}]"})
        self.history.append({"role": "assistant", "content": clean})

        return clean

    def _chat_with_vision(self, user_msg, image_content, mode=None):
        """
        Internal: sends image + text to Groq vision model.
        SAME system prompt structure as chat(): context → personality → ANCHOR (LAST)
        """
        if mode is not None:
            self.mode = mode
        elif self.mode is None:
            self.mode = detect_mode(user_msg) if user_msg else "companion"

        lang = detect_language(user_msg) if user_msg else "english"
        if lang in ('bengali', 'benglish'):
            print(f"🌸 Bengali soul activated: {lang}")

        personality = build_prompt(self.mode, lang=lang)
        context = build_context(
            user_message=user_msg or "[Image shared]",
            vector_db=self.vector_memory,
            kg=self.knowledge_graph
        )

        # EXACT same pattern as chat(): anchor is LAST
        system = (
            "[Things you remember about Soumya — use them naturally, don't list them]\n\n"
            + context + "\n\n"
            + personality + "\n\n"
            + PERSONALITY_ANCHOR
        )

        msgs = [{"role": "system", "content": system}]
        for m in self.history[-3:]:
            msgs.append(m)

        content = [
            {"type": "text", "text": user_msg or "What do you see in this image?"},
            image_content
        ]
        msgs.append({"role": "user", "content": content})

        try:
            r = self.client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=msgs,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                top_p=0.9,
            )
            raw = r.choices[0].message.content
        except Exception as e:
            raw = "Error looking at the image: " + str(e)

        clean = self._clean(raw)

        save_message("user", f"[Image] {user_msg or 'shared'}", mode=self.mode)
        save_message("assistant", clean, mode=self.mode)
        self.history.append({"role": "user", "content": user_msg or "[Image]"})
        self.history.append({"role": "assistant", "content": clean})

        return clean

    def set_mode(self, mode):
        self.mode = mode

    def get_mode(self):
        return self.mode

    def reset_session(self):
        self.history = []
        self.mode = None
        print("Session reset")
