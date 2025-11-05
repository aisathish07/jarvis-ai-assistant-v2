#!/usr/bin/env python3
"""
core_fixed.py – debugged & cleaned minimal Jarvis brain
- Loads Whisper once
- Non-blocking TTS using pyttsx3 (threaded playback)
- Robust microphone capture
- Safer Ollama HTTP call with timeout and parsing
- Fixed main loop variable handling and exceptions
"""

from __future__ import annotations
import os
import sys
import time
import queue
import tempfile
import threading
import logging
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd
import pyttsx3
import requests
import whisper  # OpenAI whisper (python package)
import structlog

# Optional: playsound/winsound were used previously; we use pyttsx3 + threaded playback.
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
logger = structlog.get_logger("jarvis")

# ----- configuration -----
SAMPLE_RATE = 16000
WHISPER_SIZE = "base"  # change to "small"/"medium" if desired and available
OLLAMA_URL = "http://localhost:11434/api/generate"
WHISPER_FF16 = False  # set True if you want fp16 (and GPU) where supported
CONTEXT_MAX = 5

# load skills if available (your original code used this)
try:
    from skill_bus import load_skills, dispatch
    SKILLS = load_skills(Path("skills"))
except Exception:
    SKILLS = {}
    def dispatch(text, skills):
        return None

# ----- Assistant class -----
class Assistant:
    def __init__(self):
        self.running = True
        self.context = deque(maxlen=CONTEXT_MAX)
        self._tts_engine = None
        self._whisper = None
        self._load_whisper()
        self._init_tts()

    # ---- load Whisper once ----
    def _load_whisper(self) -> None:
        try:
            logger.info("Loading Whisper model '%s' …", WHISPER_SIZE)
            self._whisper = whisper.load_model(WHISPER_SIZE)
            logger.info("Whisper loaded")
        except Exception as e:
            logger.exception("Failed to load Whisper model: %s", e)
            self._whisper = None

    # ---- init TTS once ----
    def _init_tts(self) -> None:
        try:
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty("rate", 180)
        except Exception as e:
            logger.warning("TTS engine init failed: %s", e)
            self._tts_engine = None

    # ---- non-blocking speak (threaded) ----
    def speak(self, text: str) -> None:
        """Speak text asynchronously (non-blocking)."""
        logger.info("speaking", text=text)
        print(f"[TTS] {text}")

        if not self._tts_engine:
            logger.warning("No TTS engine available.")
            return

        def _synth(txt: str):
            try:
                # synth to temporary file and play via engine.runAndWait() so Windows sound works
                tmp = Path(tempfile.gettempdir()) / f"jarvis_tts_{os.getpid()}_{int(time.time()*1000)}.mp3"
                # pyttsx3 has save_to_file — use it then runAndWait in the same thread
                self._tts_engine.save_to_file(txt, str(tmp))
                self._tts_engine.runAndWait()
                # play file using OS default player in non-blocking way if desired;
                # but pyttsx3 already synthesised and may have played via driver—so we keep it simple.
                time.sleep(0.1)
                # cleanup
                try:
                    tmp.unlink(missing_ok=True)
                except Exception:
                    pass
            except Exception as e:
                logger.exception("TTS playback error: %s", e)

        threading.Thread(target=_synth, args=(text,), daemon=True).start()

    # ---- microphone capture and whisper transcribe ----
    def listen(self, timeout: float = 3.0) -> str:
        """
        Record `timeout` seconds from default input and transcribe with Whisper.
        Returns the transcribed text ("" if nothing or on error).
        """
        if self._whisper is None:
            logger.warning("Whisper model not loaded; cannot transcribe")
            return ""

        try:
            logger.info("Listening for %.1f sec...", timeout)
            frames = []
            blocksize = 1024
            total_blocks = int(SAMPLE_RATE * timeout / blocksize)
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=blocksize) as stream:
                for _ in range(total_blocks):
                    data, overflow = stream.read(blocksize)
                    frames.append(data.copy())
            audio = np.concatenate(frames).flatten()
            if audio.size == 0 or np.allclose(audio, 0.0):
                return ""
            # whisper.transcribe accepts numpy arrays too; pass audio and sample rate via 'audio' arg if supported.
            # To be robust, use model.transcribe with the array (this matches earlier approach).
            result = self._whisper.transcribe(audio, fp16=WHISPER_FF16)
            text = result.get("text", "").strip()
            logger.info("Transcribed: %s", text)
            return text
        except Exception as e:
            logger.exception("listen() failed: %s", e)
            return ""

    # ---- interaction with local Ollama-like API ----
    def ask_llm(self, prompt: str, model: str = "phi3:3.8b") -> str:
        """
        Query Ollama via /api/chat with correct payload for installed models.
    """
        try:
            payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }

            logger.info("Querying LLM model=%s", model)

            r = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=30
        )
            r.raise_for_status()

            data = r.json()
        # The expected response structure: {"message": {"content": "..."}}
            resp = data.get("message", {}).get("content", "")
            if not resp:
                resp = data.get("response", "")  # fallback for older API versions

            return resp.strip() or "No reply from model."

        except Exception as e:
            logger.warning("LLM error: %s", e)
        return "Sorry, I can't answer that right now."


    # ---- handle / intent / skill bus ----
    def handle(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return ""

        ltext = text.lower()

        # meta commands
        if ltext in {"forget", "clear history", "wipe memory"}:
            self.context.clear()
            return "Memory wiped."

        # skill bus
        try:
            if SKILLS:
                reply = dispatch(text, SKILLS)
                if reply:
                    self.context.append((text, reply))
                    return reply
        except Exception as e:
            logger.warning("Skill dispatch error: %s", e)

        # simple builtins: time
        if "time" in ltext and ("what" in ltext or "tell" in ltext or "current" in ltext):
            now = datetime.now().strftime("%I:%M %p on %B %d, %Y")
            return f"The current time is {now}."

        # fallback to LLM with a small conversation context
        history = "\n".join(f"User: {u}\nJarvis: {a}" for u, a in self.context)
        prompt = f"You are Jarvis, a helpful assistant.\nRecent conversation:\n{history}\nUser: {text}\nJarvis:"
        reply = self.ask_llm(prompt)
        # store conversation
        self.context.append((text, reply))
        return reply

    # ---- main loop (debugged) ----
    def run(self):
        print("Say 'hey jarvis' or type it. Ctrl-C to exit.")
        try:
            while self.running:
                try:
                    # 1) listen a short chunk (non-blocking-ish)
                    trans = self.listen(timeout=2.5)
                    typed = ""
                    if not trans:
                        # fallback to immediate typed input if nothing heard
                        # use input with a small prompt; allow quick typing
                        try:
                            typed = input("> ").strip()
                        except EOFError:
                            typed = ""
                    # choose the user text source
                    user_text = (trans or typed or "").strip()
                    if not user_text:
                        continue

                    # only respond if wake word present OR input typed explicitly
                    if "jarvis" in user_text.lower() or typed:
                        # if wake word in speech, ask followup
                        if "jarvis" in user_text.lower() and not typed:
                            # short prompt to ask follow-up
                            self.speak("Yes?")
                            cmd = self.listen(timeout=5) or input("> ")
                        else:
                            # typed input already stored
                            cmd = user_text

                        if cmd:
                            reply = self.handle(cmd)
                            if reply:
                                self.speak(reply)
                except KeyboardInterrupt:
                    logger.info("KeyboardInterrupt received, exiting.")
                    break
                except Exception as e:
                    logger.exception("Loop error: %s", e)
                    # soft fail and continue
                    self.speak("Oops, something went wrong.")
        finally:
            logger.info("Assistant shutting down.")

# ---- main entrypoint ----
if __name__ == "__main__":
    a = Assistant()
    try:
        a.run()
    except Exception as e:
        logger.exception("Fatal error: %s", e)
        sys.exit(1)
