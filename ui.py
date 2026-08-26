# ╔══════════════════════════════════════════════════════════════════════╗
# ║  RUPSHA — ui.py (Voice + Universal Files)                            ║
# ╚══════════════════════════════════════════════════════════════════════╝

import sys
import os

import config
BASE_DIR = config.BASE_DIR

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import gradio as gr
import traceback

from brain import get_brain, get_rupsha_response


def reset_chat():
    try:
        get_brain().reset_session()
    except Exception as e:
        print(f"Reset error: {e}")
    return [], "Active mode: Auto-detect", "Messages: 0", None, None


def respond(user_message, file_input, chat_history, mode_choice):
    if chat_history is None:
        chat_history = []

    has_text = user_message and user_message.strip()
    has_file = file_input is not None

    if not has_text and not has_file:
        return "", None, chat_history, "Active mode: —", "Messages: " + str(len(chat_history)), None

    mode_map = {"Auto": "auto", "Companion": "companion", "Work": "work"}
    selected = mode_map.get(mode_choice, "auto")

    try:
        brain = get_brain()

        if selected != "auto":
            brain.set_mode(selected)
            actual_mode = selected
        else:
            brain.set_mode(None)
            from personality import detect_mode
            actual_mode = detect_mode(user_message) if has_text else "companion"

        if has_file:
            reply = brain.chat_with_file(user_message, file_input)
        else:
            reply = get_rupsha_response(user_message)

        if reply is None:
            reply = "Hmm, I spaced out for a second... 😅"
        reply = str(reply)

        audio_path = None
        try:
            if brain.voice is not None:
                audio_path = brain.voice.speak(reply)
                print(f"DEBUG TTS: audio_path = {audio_path}")
            else:
                print("DEBUG TTS: brain.voice is None")
        except Exception as ve:
            print(f"DEBUG TTS ERROR: {ve}")
            traceback.print_exc()

        display_user = user_message if has_text else "📎 [File]"
        if has_file and has_text:
            display_user = f"📎 {user_message}"
        chat_history = chat_history + [
            {"role": "user", "content": display_user},
            {"role": "assistant", "content": reply}
        ]

        return "", None, chat_history, f"Active mode: {actual_mode.upper()}", "Messages: " + str(len(chat_history)), audio_path

    except Exception as e:
        error_msg = f"🚨 Oops! I tripped: {str(e)}"
        print("=" * 50)
        print("RUPSHA ERROR:")
        traceback.print_exc()
        print("=" * 50)
        chat_history = chat_history + [
            {"role": "user", "content": user_message if has_text else "📎 [File]"},
            {"role": "assistant", "content": error_msg}
        ]
        return "", None, chat_history, "Active mode: ERROR", "Messages: " + str(len(chat_history)), None


def voice_respond(audio_file, chat_history, mode_choice):
    print(f"\n{'='*50}")
    print("DEBUG VOICE: Button clicked!")
    print(f"DEBUG VOICE: audio_file = {audio_file}")
    print(f"DEBUG VOICE: type = {type(audio_file)}")
    print(f"{'='*50}\n")

    if audio_file is None:
        print("DEBUG VOICE: audio_file is None — mic didn't return anything")
        return None, chat_history, "Active mode: —", "Messages: " + str(len(chat_history)), None

    if isinstance(audio_file, str):
        if not os.path.exists(audio_file):
            print(f"DEBUG VOICE: File does not exist: {audio_file}")
            return None, chat_history, "Active mode: ERROR", "Messages: " + str(len(chat_history)), None
        print(f"DEBUG VOICE: File exists, size = {os.path.getsize(audio_file)} bytes")

    mode_map = {"Auto": "auto", "Companion": "companion", "Work": "work"}

    try:
        brain = get_brain()
        print("DEBUG VOICE: Brain loaded")

        print("DEBUG VOICE: Starting STT...")
        user_text, reply, audio_path = brain.chat_with_voice(audio_file)
        print(f"DEBUG VOICE: STT result = '{user_text}'")
        print(f"DEBUG VOICE: Reply = '{reply[:50]}...'")
        print(f"DEBUG VOICE: TTS path = {audio_path}")

        if mode_choice != "Auto":
            actual_mode = mode_map.get(mode_choice, "auto")
        else:
            from personality import detect_mode
            actual_mode = detect_mode(user_text)

        chat_history = chat_history + [
            {"role": "user", "content": f"🎙️ {user_text}"},
            {"role": "assistant", "content": reply}
        ]

        return None, chat_history, f"Active mode: {actual_mode.upper()}", "Messages: " + str(len(chat_history)), audio_path

    except Exception as e:
        error_msg = f"🚨 Voice error: {str(e)}"
        print("=" * 50)
        print("RUPSHA VOICE ERROR:")
        traceback.print_exc()
        print("=" * 50)
        chat_history = chat_history + [
            {"role": "user", "content": "🎙️ [voice message]"},
            {"role": "assistant", "content": error_msg}
        ]
        return None, chat_history, "Active mode: ERROR", "Messages: " + str(len(chat_history)), None


def test_voice(text_to_speak):
    try:
        brain = get_brain()
        if brain.voice is None:
            return None, "Voice module not loaded!"
        path = brain.voice.speak(text_to_speak)
        return path, f"✅ Generated: {path}"
    except Exception as e:
        return None, f"❌ Error: {str(e)}"


demo = gr.Blocks(title="RUPSHA 🌸")

with demo:
    gr.Markdown("# 🌸 RUPSHA — Your Playful AI Companion")
    gr.Markdown("_Brain + Personality + Memory + Tools + Chat + Voice + Files_")

    with gr.Row():
        mode_selector = gr.Radio(
            choices=["Auto", "Companion", "Work"],
            value="Auto",
            label="Mode"
        )
        mode_display = gr.Textbox(
            value="Active mode: Auto-detect",
            label="Status",
            interactive=False
        )

    chatbot = gr.Chatbot(
        value=[],
        height=400
    )

    audio_output = gr.Audio(
        label="🔊 RUPSHA's Voice",
        autoplay=False,
        type="filepath"
    )

    file_input = gr.File(
        type="filepath",
        label="📎 Attach File (.jpg, .png, .py, .pdf, .txt, ...)",
        height=100
    )

    with gr.Row():
        msg_input = gr.Textbox(
            placeholder="Say something to RUPSHA...",
            container=False,
            scale=8
        )
        send_btn = gr.Button("Send 💌", variant="primary", scale=1)
        reset_btn = gr.Button("Reset 🔄", variant="secondary", scale=1)

    with gr.Row():
        mic = gr.Audio(
            sources=["microphone"],
            type="filepath",
            label="🎙️ Hold to Record",
            format="wav"
        )
        voice_send_btn = gr.Button("🎙️ Send Voice", variant="primary")

    memory_stats = gr.Textbox(
        value="Messages: 0",
        label="Memory Stats",
        interactive=False
    )

    with gr.Accordion("🔧 Test Voice (TTS only)", open=False):
        test_text = gr.Textbox(
            placeholder="Type something for RUPSHA to speak...",
            label="Test Text"
        )
        test_btn = gr.Button("Test TTS 🔊")
        test_audio = gr.Audio(label="Test Output", autoplay=False)
        test_status = gr.Textbox(label="Status", interactive=False)

    send_btn.click(
        fn=respond,
        inputs=[msg_input, file_input, chatbot, mode_selector],
        outputs=[msg_input, file_input, chatbot, mode_display, memory_stats, audio_output]
    )
    msg_input.submit(
        fn=respond,
        inputs=[msg_input, file_input, chatbot, mode_selector],
        outputs=[msg_input, file_input, chatbot, mode_display, memory_stats, audio_output]
    )
    reset_btn.click(
        fn=reset_chat,
        outputs=[chatbot, mode_display, memory_stats, audio_output, file_input]
    )
    voice_send_btn.click(
        fn=voice_respond,
        inputs=[mic, chatbot, mode_selector],
        outputs=[mic, chatbot, mode_display, memory_stats, audio_output]
    )

    test_btn.click(
        fn=test_voice,
        inputs=[test_text],
        outputs=[test_audio, test_status]
    )

    gr.Markdown("---")
    gr.Markdown("_RUPSHA | Groq API + Tools + Voice + Files | Built with 💖_")


def launch():
    print("🚀 Launching RUPSHA...")
    demo.launch(
        share=True,           # ← Creates public Colab link
        inbrowser=False,      # ← Don't try to open local browser
        show_error=True,      # ← Show actual errors (helps debugging)
        quiet=True            # ← Less console spam
    )

if __name__ == "__main__":
    launch()
