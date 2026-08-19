import os
import re
import queue
import shutil
import string
import subprocess
import threading
import tkinter as tk

try:
    from google import genai
except Exception:  # pragma: no cover
    genai = None

# Optional voice dependencies
# If not installed, the bot will still work in "type" mode.
try:
    import speech_recognition as sr
except Exception:  # pragma: no cover
    sr = None

try:
    import pyttsx3
except Exception:  # pragma: no cover
    pyttsx3 = None


class Jarvis:
    def __init__(self):
        self.name = "Jarvis"
        self.creator = "Nilanjan Das"

        # Keep credentials outside source control. Set GEMINI_API_KEY before
        # starting the application (see README).
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model = None
        self.client = None
        self.chat = None
        self.api_available = genai is not None and bool(self.gemini_key)
        if self.api_available:
            # Keep the client alive for the lifetime of the chat session.
            self.client = genai.Client(api_key=self.gemini_key)
            self.chat = self.client.chats.create(model="gemini-2.5-flash")

        self.conversation_history = []

        self.local_tech = {
            "python": "Python: Beginner-friendly for AI/web. print('Hello FRIDAY!') to start.",
            "js": "JavaScript: Web king. React for UI.",
            "git": "Git: git add .; git commit -m 'feat'; git push",
            "who made you": f"I'm {self.name}, created by {self.creator}. Powered by Google Gemini!",
            "who is karlos": f"Karlos is the mentor of {self.creator}",
            "when you made": "I was created in 2026, sir!",
        }

    def preprocess(self, text: str):
        text = text.lower().translate(str.maketrans("", "", string.punctuation))
        return re.findall(r"\b\w+\b", text)

    def get_response(self, user_input: str) -> str:
        tokens = self.preprocess(user_input)
        self.conversation_history.append(f"User: {' '.join(tokens)}")
        input_text = " ".join(tokens)

        # Local priorities
        for key, resp in self.local_tech.items():
            if key in input_text:
                return resp

        # Creator questions (keep narrow)
        if (
            re.search(r"^who\s+made\s+you\b", input_text)
            or re.search(r"^who\s+is\s+your\s+creator\b", input_text)
        ):
            return f"My creator is {self.creator}."

        if re.search(r"(hello|hi)", input_text):
            return "Yes sir! How can I help?"

        if re.search(r"(help)", input_text):
            return "Say something like: 'python tips', 'who made you', 'who is karlos', or 'quit'."

        if re.search(r"(quit|bye|close|exit)", input_text):
            return "Offline, sir!"

        # Gemini API
        if self.chat is None:
            if genai is None:
                return "Gemini SDK is missing. Run: python -m pip install -r requirements.txt"
            return "Gemini is not configured. Set GEMINI_API_KEY, then restart the app."

        try:
            response = self.chat.send_message(user_input)
            text = response.text.strip()
            self.conversation_history.append(f"{self.name}: {text}")
            return text
        except Exception as exc:
            return f"Gemini error: {str(exc)[:80]}"


class VoiceEngine:
    def __init__(self):
        self.recognizer = None
        self.microphone = None
        self._speech_queue = queue.Queue()
        self._speech_lock = threading.Lock()
        self._speech_generation = 0
        self._active_speech_process = None
        self._speech_failed = False
        self._powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        self._use_windows_speech = os.name == "nt" and self._powershell is not None

        if sr is not None:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
            except Exception:
                self.recognizer = None
                self.microphone = None

        self.tts_engine = None
        if self._use_windows_speech or pyttsx3 is not None:
            threading.Thread(target=self._speech_worker, daemon=True).start()

    def is_voice_available(self) -> bool:
        return (
            self.recognizer is not None
            and self.microphone is not None
            and self.is_speech_available()
        )

    def is_speech_available(self) -> bool:
        return (self._use_windows_speech or pyttsx3 is not None) and not self._speech_failed

    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 15) -> str:
        if self.recognizer is None or self.microphone is None:
            raise RuntimeError("Voice recognition dependencies not installed.")

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = self.recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )

        return self.recognizer.recognize_google(audio)

    def speak(self, text: str):
        if not self.is_speech_available():
            return
        speech_text = self._speech_text(text)
        if speech_text:
            with self._speech_lock:
                generation = self._speech_generation
            self._speech_queue.put((generation, speech_text))

    def stop_speaking(self):
        """Immediately stop the active reply and discard queued replies."""
        with self._speech_lock:
            self._speech_generation += 1
            process = self._active_speech_process

        # Windows SAPI runs in this child process, so ending it stops audio now.
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass

        if self.tts_engine is not None:
            try:
                self.tts_engine.stop()
            except Exception:
                pass

        while True:
            try:
                self._speech_queue.get_nowait()
                self._speech_queue.task_done()
            except queue.Empty:
                break

    def _speech_worker(self):
        if not self._use_windows_speech:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", 175)
            except Exception:
                self.tts_engine = None
                self._speech_failed = True
                return

        while True:
            generation, text = self._speech_queue.get()
            try:
                with self._speech_lock:
                    if generation != self._speech_generation:
                        continue
                if self._use_windows_speech:
                    self._speak_with_windows_sapi(text, generation)
                else:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
            except Exception:
                # Keep the speaker alive for the next reply if one utterance fails.
                if self.tts_engine is not None:
                    try:
                        self.tts_engine.stop()
                    except Exception:
                        pass
            finally:
                self._speech_queue.task_done()

    def _speak_with_windows_sapi(self, text: str, generation: int):
        command = (
            "$speaker = New-Object -ComObject SAPI.SpVoice; "
            "$speaker.Rate = 0; "
            "$speaker.Speak($env:JARVIS_SPEECH_TEXT) | Out-Null"
        )

        for chunk in self._speech_chunks(text):
            with self._speech_lock:
                if generation != self._speech_generation:
                    return
            env = os.environ.copy()
            env["JARVIS_SPEECH_TEXT"] = chunk
            process = subprocess.Popen(
                [self._powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            with self._speech_lock:
                self._active_speech_process = process
            process.wait()
            with self._speech_lock:
                if self._active_speech_process is process:
                    self._active_speech_process = None

    def _speech_chunks(self, text: str, chunk_size: int = 2800):
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    def _speech_text(self, text: str) -> str:
        text = re.sub(r"`{1,3}", "", text)
        text = re.sub(r"[*_#>\[\]()]", " ", text)
        text = re.sub(r"https?://\S+", " link ", text)
        return re.sub(r"\s+", " ", text).strip()


class VoiceBotGUI:
    """Voice-only GUI: no chat input, only mic + transcript log."""

    def _create_bg_logo(self):
        """Create the animated watermark behind the transcript text."""
        self.chat_log.delete("watermark")
        pad = 18
        s = self._logo_size - (pad * 2)
        cx, cy = self._visible_chat_center()
        x0 = cx - self._logo_size // 2
        y0 = cy - self._logo_size // 2

        self._blue_logo_arc_id = self.chat_log.create_arc(
            x0 + pad,
            y0 + pad,
            x0 + pad + s,
            y0 + pad + s,
            start=self._blue_logo_angle,
            extent=120,
            style="arc",
            outline=self.logo_color,
            width=4,
            tags=("watermark",),
        )
        self._green_logo_arc_id = self.chat_log.create_arc(
            x0 + pad + 32,
            y0 + pad + 32,
            x0 + pad + s - 32,
            y0 + pad + s - 32,
            start=self._green_logo_angle,
            extent=120,
            style="arc",
            outline=self.logo_green,
            width=3,
            tags=("watermark",),
        )
        self._logo_dot_id = self.chat_log.create_oval(
            cx - 7,
            cy - 7,
            cx + 7,
            cy + 7,
            outline=self.logo_color,
            width=1,
            tags=("watermark",),
        )
        self.chat_log.tag_lower("watermark")

    def _animate_bg_logo(self):
        """Animate the background logo arc angle."""
        if self._blue_logo_arc_id is not None:
            self._blue_logo_angle = (self._blue_logo_angle + 4) % 360
            self.chat_log.itemconfigure(
                self._blue_logo_arc_id, start=self._blue_logo_angle
            )

        if self._green_logo_arc_id is not None:
            self._green_logo_angle = (self._green_logo_angle - 4) % 360
            self.chat_log.itemconfigure(
                self._green_logo_arc_id, start=self._green_logo_angle
            )

        self._position_bg_logo()

        # Schedule next frame.
        self.root.after(50, self._animate_bg_logo)

    def _position_bg_logo(self, event=None):
        """Keep the watermark centered in the visible transcript viewport."""
        if self._blue_logo_arc_id is None or self._green_logo_arc_id is None:
            return

        cx, cy = self._visible_chat_center()
        pad = 18
        s = self._logo_size - (pad * 2)
        x0 = cx - self._logo_size // 2
        y0 = cy - self._logo_size // 2

        self.chat_log.coords(
            self._blue_logo_arc_id,
            x0 + pad,
            y0 + pad,
            x0 + pad + s,
            y0 + pad + s,
        )
        self.chat_log.coords(
            self._green_logo_arc_id,
            x0 + pad + 32,
            y0 + pad + 32,
            x0 + pad + s - 32,
            y0 + pad + s - 32,
        )
        self.chat_log.coords(self._logo_dot_id, cx - 7, cy - 7, cx + 7, cy + 7)
        self.chat_log.tag_lower("watermark")

    def _visible_chat_center(self):
        width = max(self.chat_log.winfo_width(), 1)
        height = max(self.chat_log.winfo_height(), 1)
        return self.chat_log.canvasx(width / 2), self.chat_log.canvasy(height / 2)

    def _redraw_messages(self, event=None):
        """Draw transcript messages above the watermark."""
        if not hasattr(self, "messages"):
            return

        self.chat_log.delete("message")
        text_width = max(self.chat_log.winfo_width() - 28, 100)
        y = 10

        for sender, message, tag in self.messages:
            item_id = self.chat_log.create_text(
                10,
                y,
                anchor="nw",
                fill=self.tag_colors.get(tag, self.fg),
                font=self.chat_font,
                text=f"{sender}: {message}",
                width=text_width,
                tags=("message",),
            )
            bbox = self.chat_log.bbox(item_id)
            y = (bbox[3] if bbox else y + 24) + 24

        self.chat_log.configure(scrollregion=(0, 0, text_width + 28, max(y, 1)))
        self.chat_log.tag_raise("message")
        self.chat_log.tag_lower("watermark")
        self._position_bg_logo()

    def _scroll_chat(self, *args):
        self.chat_log.yview(*args)
        self._position_bg_logo()

    def _on_mousewheel(self, event):
        self.chat_log.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self._position_bg_logo()

    def _on_chat_configure(self, event=None):
        if self._blue_logo_arc_id is None:
            self._create_bg_logo()
        self._redraw_messages()

    def __init__(self, root: tk.Tk):

        self.root = root
        self.root.title("Jarvis")
        self.root.geometry("900x600")

        # Theme
        self.bg = "#0f1115"
        self.fg = "#e6edf3"
        self.accent2 = "#0bfe64"
        # Color used for the animated background logo arc.
        # Keep it independent from text foreground color to avoid accidental theme changes.
        self.logo_color = "#00385f"
        self.logo_green = "#064a22"
        self.entry_bg = "#c8c8c9"
        self.root.configure(bg=self.bg)

        self._logo_size = 220
        self._logo_panel_width = 300
        self._blue_logo_angle = 0
        self._green_logo_angle = 210
        self._blue_logo_arc_id = None
        self._green_logo_arc_id = None
        self._logo_dot_id = None
        self.chat_font = ("Consolas", 13)
        self.messages = []
        self.tag_colors = {
            "user_tag": "#93c5fd",
            "bot_tag": "#a7f3d0",
        }

        self.bot = Jarvis()

        self.voice = VoiceEngine()


        # Chat log (transcript)
        self.chat_frame = tk.Frame(root, bg=self.bg)
        self.chat_frame.pack(padx=12, pady=(12, 8), fill=tk.BOTH, expand=True)

        self.chat_log = tk.Canvas(
            self.chat_frame,
            bg=self.bg,
            highlightthickness=1,
            highlightbackground="#30363d",
            bd=0,
        )
        self.chat_scrollbar = tk.Scrollbar(
            self.chat_frame,
            orient=tk.VERTICAL,
            command=self._scroll_chat,
        )
        self.chat_log.configure(yscrollcommand=self.chat_scrollbar.set)
        self.chat_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_log.bind("<Configure>", self._on_chat_configure)
        self.chat_log.bind("<MouseWheel>", self._on_mousewheel)
        self.chat_log.bind("<Button-4>", lambda event: self._scroll_chat("scroll", -1, "units"))
        self.chat_log.bind("<Button-5>", lambda event: self._scroll_chat("scroll", 1, "units"))

        self.root.after_idle(
            lambda: (
                self._create_bg_logo(),
                self._redraw_messages(),
                self._position_bg_logo(),
            )
        )

        # Start animation after UI is ready.
        self.root.after(100, self._animate_bg_logo)

        # Status line
        self.status_var = tk.StringVar(value=self._status_text())
        status = tk.Label(
            root,
            textvariable=self.status_var,
            bg=self.bg,
            fg=self.fg,
            anchor="w",
        )
        status.pack(fill=tk.X, padx=12, pady=(0, 6))

        # Controls
        controls = tk.Frame(root, bg=self.bg)
        controls.pack(fill=tk.X, padx=12, pady=(0, 12))

        controls.grid_columnconfigure(0, weight=2)
        controls.grid_columnconfigure(2, weight=2)

        self.mic_btn = tk.Button(
            controls,
            text="Speak",
            bg=self.accent2,
            fg="white",
            activebackground=self.accent2,
            activeforeground="white",
            disabledforeground="green",
            relief=tk.FLAT,
            padx=14,
            command=self.start_listening,
        )

        # Button colors
        self._idle_mic_bg = self.accent2
        self._listening_mic_bg = "#f97316"  # orange
        self._mic_fg = "white"

        self.mic_btn.grid(row=0, column=1, sticky="")
        self.root.bind("<Escape>", lambda event: self.stop_speaking())

        if not self.voice.is_voice_available():

            self.append_bot_message(
                self.bot.name,
                "Voice mode not available. Install speech_recognition + pyttsx3.",
            )
        else:
            self.append_bot_message(
                self.bot.name,
                "Online sir! Press Speak.",
            )

    def _status_text(self) -> str:
        if self.voice.is_voice_available():
            return "Voice input and answer voice are available."
        if self.voice.is_speech_available():
            return "Answer voice available. Microphone input is not available."
        return "Voice not available. Install speech_recognition + pyttsx3."

    def append_message(self, sender: str, message: str, tag: str):
        self.messages.append((sender, message, tag))
        self._redraw_messages()
        self.chat_log.yview_moveto(1.0)
        self._position_bg_logo()
        if tag == "bot_tag":
            self.speak_async(message)

    def append_bot_message(self, sender: str, message: str):
        self.append_message(sender, message, "bot_tag")

    def speak_async(self, message: str):
        if self.voice.is_speech_available():
            self.voice.speak(message)

    def stop_speaking(self):
        self.voice.stop_speaking()
        self.status_var.set("Speech stopped.")

    def start_listening(self):
        if not self.voice.is_voice_available():
            self.append_bot_message(
                self.bot.name,
                "Voice mode not available. Install speech_recognition + pyttsx3.",
            )
            return

        # Update button to indicate recording state.
        self.root.after(
            0,
            lambda: self.mic_btn.config(
                bg=self._listening_mic_bg,
                fg=self._mic_fg,
                activebackground=self._listening_mic_bg,
                activeforeground=self._mic_fg,
            ),
        )

        self.status_var.set("Listening...")
        self.mic_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._listen_and_handle, daemon=True).start()


    def _listen_and_handle(self):
        try:
            heard = self.voice.listen_once()
            self.root.after(0, self.append_message, "You", heard, "user_tag")
            self.root.after(0, self.status_var.set, self._status_text())

            response = self.bot.get_response(heard)
            self.root.after(0, self.append_bot_message, self.bot.name, response)

            if response.lower().strip().startswith("offline"):
                # Quitting time should be ~4 seconds.
                self.root.after(4000, self.root.destroy)

        except Exception as e:
            self.root.after(0, self.status_var.set, self._status_text())
            self.root.after(
                0,
                self.append_bot_message,
                self.bot.name,
                f"Could not hear/understand. ({str(e)[:60]})",
            )

        finally:
            # Restore mic button back to idle state (success or error).
            self.root.after(
                0,
                lambda: self.mic_btn.config(
                    state=tk.NORMAL,
                    bg=self.accent2,
                    fg="white",
                    activebackground=self.accent2,
                    activeforeground="white",
                ),
            )


def main():
    root = tk.Tk()
    app = VoiceBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

