"""
skills/media_skill.py
──────────────────────────────────────────────
Media Control Skill for Jarvis
Controls Spotify, YouTube (browser), and local media playback.
Uses app control integration and system media keys.
"""

from jarvis_skills import BaseSkill
import asyncio
import pyautogui
import re

class Skill(BaseSkill):
    name = "media"
    keywords = [
        "music", "song", "spotify", "play", "pause", "resume",
        "stop", "next", "previous", "volume", "youtube", "sound"
    ]

    async def handle(self, text, jarvis):
        text = text.lower().strip()

        # Route to Spotify if mentioned
        if "spotify" in text:
            return await self._spotify_control(text, jarvis)

        # YouTube control
        if "youtube" in text:
            return await self._youtube_control(text, jarvis)

        # General media keys
        if any(k in text for k in ["play", "pause", "resume", "stop", "next", "previous", "volume"]):
            return await self._system_media_control(text)

        return "I couldn’t determine which media action to perform."

    # ───────────────────────────────────────────────
    # Spotify Control
    # ───────────────────────────────────────────────
    async def _spotify_control(self, text: str, jarvis) -> str:
        """Controls Spotify app via AppControlIntegration."""
        try:
            loop = asyncio.get_running_loop()
            # Use the app controller if integrated
            response = await loop.run_in_executor(None, jarvis.app_control.parse_command, text)
            if response:
                return response

            # fallback: system keys
            if "play" in text or "resume" in text:
                pyautogui.press("playpause")
                return "Resumed Spotify playback."
            if "pause" in text:
                pyautogui.press("playpause")
                return "Paused Spotify."
            if "next" in text:
                pyautogui.press("nexttrack")
                return "Skipped to next song."
            if "previous" in text:
                pyautogui.press("prevtrack")
                return "Playing previous song."
            if "volume up" in text:
                pyautogui.press("volumeup")
                return "Increased volume."
            if "volume down" in text:
                pyautogui.press("volumedown")
                return "Decreased volume."

            # Play specific track
            match = re.search(r"(?:play|listen to)\s+(.*)", text)
            if match:
                query = match.group(1)
                cmd = f"spotify play {query}"
                _ = await loop.run_in_executor(None, jarvis.app_control.parse_command, cmd)
                return f"Playing {query} on Spotify."
        except Exception as e:
            return f"Spotify control failed: {e}"

    # ───────────────────────────────────────────────
    # YouTube Control (via Chrome)
    # ───────────────────────────────────────────────
    async def _youtube_control(self, text: str, jarvis) -> str:
        """Opens or plays YouTube videos."""
        try:
            loop = asyncio.get_running_loop()
            # Parse search query
            match = re.search(r"(?:play|search)\s+(?:on\s+)?youtube\s+(?:for\s+)?(.+)", text)
            if match:
                query = match.group(1)
                url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                cmd = f"open chrome and search {query} site:youtube.com"
                await loop.run_in_executor(None, jarvis.app_control.parse_command, cmd)
                return f"Searching YouTube for {query}."
            elif "pause" in text:
                pyautogui.press("k")  # YouTube shortcut
                return "Paused YouTube playback."
            elif "resume" in text or "play" in text:
                pyautogui.press("k")
                return "Resumed YouTube playback."
            elif "mute" in text:
                pyautogui.press("m")
                return "Muted YouTube."
            elif "volume up" in text:
                pyautogui.press("up")
                return "Turned volume up on YouTube."
            elif "volume down" in text:
                pyautogui.press("down")
                return "Turned volume down on YouTube."

            return "Specify what to play or control on YouTube."
        except Exception as e:
            return f"YouTube control failed: {e}"

    # ───────────────────────────────────────────────
    # System Media Control (generic)
    # ───────────────────────────────────────────────
    async def _system_media_control(self, text: str) -> str:
        """Uses global media keys for system-level control."""
        try:
            if "play" in text or "resume" in text:
                pyautogui.press("playpause")
                return "Resumed media playback."
            if "pause" in text or "stop" in text:
                pyautogui.press("playpause")
                return "Paused media."
            if "next" in text:
                pyautogui.press("nexttrack")
                return "Skipped to next track."
            if "previous" in text:
                pyautogui.press("prevtrack")
                return "Went back to previous track."
            if "volume up" in text:
                pyautogui.press("volumeup")
                return "Increased system volume."
            if "volume down" in text:
                pyautogui.press("volumedown")
                return "Decreased system volume."
            if "mute" in text:
                pyautogui.press("volumemute")
                return "Muted system volume."

            return "Media action not recognized."
        except Exception as e:
            return f"Media control failed: {e}"
