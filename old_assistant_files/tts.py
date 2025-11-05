import asyncio
import logging
import os
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable, Optional

# ----------  add at top of tts.py (after imports)  ----------
from pynput import keyboard


class _HotkeyStop:
    """Global Ctrl+Space interrupt – lives inside TTS."""

    def __init__(self, tts_engine: "TextToSpeech"):
        self.tts_engine = tts_engine
        self.listener = None
        try:
            self.hotkey = keyboard.HotKey(
                keyboard.HotKey.parse("<ctrl>+<space>"), self._on_activate
            )
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
        except Exception as e:
            logging.getLogger("AI_Assistant.TTS").warning("Hotkey init failed: %s", e)

    def _run(self):
        self.listener = keyboard.Listener(
            on_press=self.hotkey.press, on_release=self.hotkey.release
        )
        self.listener.start()
        self.listener.join()

    def _on_activate(self):
        self.tts_engine.stop()

    def stop(self):
        if self.listener:
            self.listener.stop()


# ---------------------------------------------------

# ------------------------------------------------------------------
#  ElevenLabs SDK version detector
# ------------------------------------------------------------------
try:
    # SDK ≥ 1.0
    from elevenlabs import Voice, VoiceSettings, generate, save

    ELEVEN_SDK_NEW = True
except ImportError:
    try:
        # SDK 0.x
        from elevenlabs import generate, save

        ELEVEN_SDK_NEW = False
    except ImportError:
        # ElevenLabs not installed at all
        ELEVEN_SDK_NEW = None

from gtts import gTTS

from config import Config

logger = logging.getLogger("AI_Assistant.TTS")


class TextToSpeech:
    def __init__(self):
        # ----------  ElevenLabs  ----------
        self.elevenlabs_voice = os.getenv("ELEVENLABS_VOICE", "21m00Tcm4TlvDq8ikWAM")
        self.elevenlabs_model = os.getenv("ELEVENLABS_MODEL", "eleven_monolingual_v1")

        # ----------  gTTS  ----------
        self.gtts_lang = os.getenv("GTTS_LANG", "en")

        # ----------  Piper  ----------
        self.piper_exe = os.getenv("PIPER_EXECUTABLE_PATH")

        # ----------  playback (FIXED: no duplicate initialization)  ----------
        self.playback_queue: asyncio.Queue = asyncio.Queue()
        self._stop_event: Optional[asyncio.Event] = None
        self.playback_task: Optional[asyncio.Task] = None
        self._playback_worker_started = False
        self.interrupt = _HotkeyStop(self)  # ← new

    # ------------------------------------------------------------------
    #  Public API – always async
    # ------------------------------------------------------------------
    async def speak(
        self, text: str, status_callback: Optional[Callable[[str, Any], None]] = None
    ) -> None:
        """Generate and queue audio for playback."""
        if not text or not text.strip():
            return
        try:
            file_path = await self._generate_audio(text)
            if not file_path:
                logger.error("No audio generated.")
                return
            await self.playback_queue.put((file_path, status_callback))
        except Exception as e:
            logger.error("Error in speak(): %s", e, exc_info=True)

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """Call this once the event-loop is running (from assistant thread)."""
        if self.playback_task is None and not self._playback_worker_started:
            self._stop_event = asyncio.Event()
            self.playback_task = loop.create_task(self._playback_worker())
            self._playback_worker_started = True
            logger.info("TTS playback worker started.")

    def stop(self) -> None:
        """Stop playback and clear queue."""
        if self._stop_event:
            self._stop_event.set()

        # FIXED: Safe queue clearing with proper exception handling
        try:
            while not self.playback_queue.empty():
                try:
                    self.playback_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        except Exception as e:
            logger.warning("Error clearing playback queue: %s", e)

        if self.playback_task and not self.playback_task.done():
            self.playback_task.cancel()

    def close(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down TTS...")
        self.stop()
        try:
            self.playback_queue.put_nowait((None, None))
        except asyncio.QueueFull:
            pass

    # ------------------------------------------------------------------
    #  Audio generation – returns path to temp file
    # ------------------------------------------------------------------
    async def _generate_audio(self, text: str) -> Optional[str]:
        """Try TTS engines in priority order."""
        for engine in Config.TTS_PRIORITY:
            try:
                if (
                    engine == "elevenlabs"
                    and Config.ELEVENLABS_API_KEY
                    and ELEVEN_SDK_NEW is not None
                ):
                    path = await self._speak_elevenlabs(text)
                    if path:
                        return path
                elif engine == "gtts":
                    path = await self._speak_gtts(text)
                    if path:
                        return path
                elif engine == "piper" and self.piper_exe and os.path.isfile(self.piper_exe):
                    path = await self._speak_piper(text)
                    if path:
                        return path
            except Exception as e:
                logger.warning("%s TTS failed: %s", engine, e)
        return None

    # ------------------------------------------------------------------
    #  ElevenLabs  –  version-agnostic
    # ------------------------------------------------------------------
    async def _speak_elevenlabs(self, text: str) -> Optional[str]:
        if ELEVEN_SDK_NEW is None:
            logger.warning("ElevenLabs not installed – skipping.")
            return None
        try:
            if ELEVEN_SDK_NEW:  # ≥ 1.0
                audio = generate(
                    text=text,
                    voice=Voice(
                        voice_id=self.elevenlabs_voice,
                        settings=VoiceSettings(stability=0.45, similarity_boost=0.75),
                    ),
                    model=self.elevenlabs_model,
                )
            else:  # 0.x
                audio = generate(
                    text=text, voice=self.elevenlabs_voice, model=self.elevenlabs_model
                )

            file_path = Path(tempfile.gettempdir()) / f"elevenlabs_{os.urandom(4).hex()}.mp3"
            save(audio, file_path)
            return str(file_path)
        except Exception as e:
            logger.error("ElevenLabs TTS failed: %s", e)
            return None

    # ------------------------------------------------------------------
    #  gTTS  (sync, wrap in thread)
    # ------------------------------------------------------------------
    async def _speak_gtts(self, text: str) -> Optional[str]:
        """Generate audio using Google TTS."""

        def _gtts():
            try:
                tts = gTTS(text=text, lang=self.gtts_lang)
                file_path = Path(tempfile.gettempdir()) / f"gtts_{os.urandom(4).hex()}.mp3"
                tts.save(str(file_path))
                return str(file_path)
            except Exception as e:
                logger.error("gTTS generation failed: %s", e)
                return None

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _gtts)
        except Exception as e:
            logger.error("gTTS executor error: %s", e)
            return None

    # ------------------------------------------------------------------
    #  Piper  (sync CLI, wrap in thread)
    # ------------------------------------------------------------------
    async def _speak_piper(self, text: str) -> Optional[str]:
        """Generate audio using Piper (offline)."""
        if not self.piper_exe or not os.path.isfile(self.piper_exe):
            logger.warning("Piper executable not found: %s", self.piper_exe)
            return None

        def _piper():
            try:
                wav_path = Path(tempfile.gettempdir()) / f"piper_{os.urandom(4).hex()}.wav"
                mp3_path = wav_path.with_suffix(".mp3")

                proc = subprocess.Popen(
                    [
                        self.piper_exe,
                        "--model",
                        "en_US-amy-medium.onnx",
                        "--output_file",
                        str(wav_path),
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                out, err = proc.communicate(input=text.encode())
                if proc.returncode != 0:
                    logger.error("Piper process failed: %s", err.decode())
                    return None

                # Convert to mp3
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(wav_path), "-loglevel", "quiet", str(mp3_path)],
                    check=True,
                    capture_output=True,
                )
                wav_path.unlink(missing_ok=True)
                return str(mp3_path)
            except Exception as e:
                logger.error("Piper generation failed: %s", e)
                return None

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _piper)
        except Exception as e:
            logger.error("Piper executor error: %s", e)
            return None

    # ------------------------------------------------------------------
    #  Playback worker (async, uses ffplay)
    # ------------------------------------------------------------------
    async def _playback_worker(self) -> None:
        """Async worker that plays queued audio files."""
        if not self._stop_event:
            logger.error("Stop event not initialized")
            return

        while not self._stop_event.is_set():
            try:
                try:
                    item = await asyncio.wait_for(self.playback_queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue

                file_path, status_callback = item

                if file_path is None:  # Sentinel shutdown
                    break

                try:
                    if not os.path.isfile(file_path):
                        logger.warning("Audio file not found: %s", file_path)
                        continue

                    if status_callback:
                        status_callback("speaking_start")

                    proc = await asyncio.create_subprocess_exec(
                        "ffplay",
                        "-nodisp",
                        "-autoexit",
                        "-loglevel",
                        "quiet",
                        str(file_path),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    await proc.wait()
                except FileNotFoundError:
                    logger.error("ffplay not found – install ffmpeg.")
                except Exception as e:
                    logger.error("Playback error: %s", e)
                finally:
                    if status_callback:
                        status_callback("speaking_end")
                    try:
                        Path(file_path).unlink(missing_ok=True)
                    except Exception as e:
                        logger.warning("Failed to delete temp file: %s", e)
            except asyncio.CancelledError:
                logger.info("Playback worker cancelled.")
                break
            except Exception as e:
                logger.error("Playback worker error: %s", e, exc_info=True)
