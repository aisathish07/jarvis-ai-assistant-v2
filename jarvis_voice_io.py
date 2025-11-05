"""
jarvis_voice_io.py
A basic implementation of voice output using pyttsx3.
"""

import pyttsx3
import logging

logger = logging.getLogger("Jarvis.VoiceIO")

class OptimizedVoiceIO:
    def __init__(self, enabled=True):
        self.enabled = enabled
        if self.enabled:
            try:
                self.engine = pyttsx3.init()
                logger.info("Voice IO initialized (pyttsx3).")
            except Exception as e:
                logger.error(f"Failed to initialize pyttsx3: {e}")
                self.enabled = False
        else:
            logger.info("Voice IO is disabled.")

    async def speak(self, text: str):
        if not self.enabled or not text:
            return

        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error in pyttsx3 speech: {e}")
