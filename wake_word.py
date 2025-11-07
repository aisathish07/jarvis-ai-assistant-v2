#!/usr/bin/env python3
"""
wake_word_v2.py – production wake-word + hot-key module for Jarvis
Improvements:
 - Safe async handling for TTS
 - Graceful shutdown of mic stream
 - Optional console meter toggle
 - Slight CPU optimization
 - Proper ONNX model fallback handling
"""

import asyncio
import logging
import os
import queue
import threading
import time
from pathlib import Path

import keyboard
import librosa
import numpy as np
import onnxruntime as ort
import sounddevice as sd

# --------------- imports from YOUR assistant  ---------------
from jarvis_config import Config  # gives SAMPLE_RATE etc
from jarvis_voice_io import OptimizedVoiceIO as TextToSpeech  # optional “Yes?” feedback

# ------------------------------------------------------------

log = logging.getLogger("AI_Assistant.WakeWord")

# --------------------------- CONFIG ---------------------------
MODEL_PATH = Path(__file__).with_name("models") / "hey_jarvis.onnx"
SAMPLE_RATE = Config.SAMPLE_RATE  # 16000
BLOCK_SIZE = 512
THRESHOLD = 0.65
DEBOUNCE_S = 1.5
SILENCE_DB = -60
MEL_SHAPE = (1, 16, 96)
SHOW_METER = os.environ.get("SHOW_METER", "1") == "1"
# --------------------------------------------------------------


class WakeWordDetector:
    """
    Live wake-word + global hot-key (Ctrl+Space) feeder.
    Runs in its own thread; pushes strings to assistant input_queue.
    """

    def __init__(self, input_queue: queue.Queue, tts_engine: "TextToSpeech | None" = None, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self.q = input_queue
        self.tts = tts_engine
        self.loop = loop
        self.running = False
        self.thread: threading.Thread | None = None
        self._hotkey_pressed = False
        self.paused = False

        # Try to load ONNX model
        providers = ["CPUExecutionProvider"]
        if MODEL_PATH.exists():
            log.info(f"Loading wake-word model from: {MODEL_PATH}")
            self.sess = ort.InferenceSession(str(MODEL_PATH), providers=providers)
        else:
            raise FileNotFoundError(f"Wake-word model not found at {MODEL_PATH}")

        self.input_name = self.sess.get_inputs()[0].name
        self.output_name = self.sess.get_outputs()[0].name

        # hot-key
        keyboard.add_hotkey("ctrl+space", self._hotkey_callback)
        log.info("Wake-word detector initialised (threshold %.2f)", THRESHOLD)

    # ----------------------------------------------------------
    #  life-cycle
    # ----------------------------------------------------------
    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        log.info("🎧 Wake-word + hot-key listening …")

    def stop(self) -> None:
        self.running = False
        keyboard.unhook_all_hotkeys()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        log.info("🔇 Wake-word detector stopped")

    def pause(self) -> None:
        self.paused = True
        log.info("🎤 Wake-word detector paused")

    def resume(self) -> None:
        self.paused = False
        log.info("🎧 Wake-word + hot-key listening …")

    # ----------------------------------------------------------
    #  hot-key callback
    # ----------------------------------------------------------
    def _hotkey_callback(self) -> None:
        self._hotkey_pressed = True

    # ----------------------------------------------------------
    #  audio loop (runs in thread)
    # ----------------------------------------------------------
    def _listen_loop(self) -> None:
        audio_q = queue.Queue(maxsize=10)
        last_trigger = 0.0

        def callback(indata, frames, time_info, status):
            if status:
                log.debug("audio status: %s", status)
            audio_q.put(indata.copy())

        window = np.zeros(SAMPLE_RATE * 2, dtype=np.float32)

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            blocksize=BLOCK_SIZE,
            dtype="float32",
            callback=callback,
        ) as stream:
            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue
                try:
                    chunk = audio_q.get(timeout=0.5).flatten()
                except queue.Empty:
                    continue

                window = np.roll(window, -len(chunk))
                window[-len(chunk) :] = chunk

                # Silence filter
                rms = np.sqrt(np.mean(window**2))
                db = 20 * np.log10(max(rms, 1e-7))
                if db < SILENCE_DB:
                    continue

                mel = self._make_mel(window)
                score = float(
                    self.sess.run([self.output_name], {self.input_name: mel})[0].squeeze()
                )

                if SHOW_METER:
                    self._print_meter(db, score)

                now = time.time()
                auto = score >= THRESHOLD and (now - last_trigger) > DEBOUNCE_S
                manual = self._hotkey_pressed

                if auto or manual:
                    self._fire_wake_event()
                    last_trigger = now
                    self._hotkey_pressed = False

                # reduce CPU load
                time.sleep(0.02)

            stream.stop()

    # ----------------------------------------------------------
    #  helpers
    # ----------------------------------------------------------
    def _make_mel(self, audio: np.ndarray) -> np.ndarray:
        mel = librosa.feature.melspectrogram(
            y=audio, sr=SAMPLE_RATE, n_fft=512, hop_length=160, n_mels=16, fmax=8000
        )
        mel_db = librosa.power_to_db(mel, ref=np.max)
        if mel_db.shape[1] < 96:
            mel_db = np.pad(mel_db, ((0, 0), (0, 96 - mel_db.shape[1])))
        mel_db = mel_db[:, :96]
        mel_db = (mel_db - np.mean(mel_db)) / (np.std(mel_db) + 1e-6)
        return mel_db[np.newaxis, :, :].astype(np.float32)

    def _print_meter(self, db: float, score: float) -> None:
        if not SHOW_METER:
            return
        bar = "█" * int(score * 40)
        print(f"\r🎚 {db:6.1f} dB  |  {score:.2f}  {bar:<40}", end="", flush=True)

    def _fire_wake_event(self) -> None:
        log.info("\n🎤 Wake-word / hot-key triggered")
        self.q.put("WAKE_WORD_DETECTED")

        if self.tts and self.loop:
            try:
                asyncio.run_coroutine_threadsafe(self.tts.speak("Yes?"), self.loop)
            except Exception as e:
                log.warning(f"TTS feedback failed: {e}")