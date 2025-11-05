import logging

import numpy as np
import speech_recognition as sr
import torch
import whisper

from gui import AssistantGUI

logger = logging.getLogger("AI_Assistant.STT")


class SpeechToText:
    def __init__(self, model_size: str, gui: AssistantGUI):
        self.gui = gui
        self.model_size = model_size
        self.model = None
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

    def load_model(self):
        if self.model is not None:
            return
        self.gui.gui_queue.put(("set_state", "thinking", "Loading speech model…"))
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Loading Whisper %s on %s", self.model_size, device)
        try:
            self.model = whisper.load_model(self.model_size, device=device)
        except Exception:
            logger.exception("Whisper load failed")
            self.gui.gui_queue.put(("set_state", "error", "Model load failed"))
        finally:
            self.gui.gui_queue.put(("set_state", "idle"))

    def listen_and_transcribe(self) -> str:
        if self.model is None:
            logger.error("Whisper not loaded")
            return ""
        self.gui.gui_queue.put(("set_state", "listening"))
        with sr.Microphone(sample_rate=16000) as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                return ""
        self.gui.gui_queue.put(("set_state", "thinking", "Transcribing…"))
        try:
            audio_np = (
                np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
            )
            result = self.model.transcribe(audio_np, fp16=False)
            return result.get("text", "").strip()
        except Exception:
            logger.exception("Transcription error")
            return ""
