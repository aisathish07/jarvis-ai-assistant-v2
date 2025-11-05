"""
skills/media_skill.py
──────────────────────────────────────────────
Media Control Skill for Jarvis
Controls Spotify via Web API, YouTube (browser), and local media playback.
"""

from jarvis_skills import BaseSkill
import asyncio
import pyautogui
import re
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# --- Helper function for Spotipy --- #

def get_spotify_client():
    """Authenticates and returns a Spotipy client."""
    scope = "user-read-playback-state,user-modify-playback-state"
    try:
        auth_manager = SpotifyOAuth(scope=scope,
                                    # The following are read from your environment variables
                                    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                                    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                                    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"))
        sp = spotipy.Spotify(auth_manager=auth_manager)
        # Test authentication
        sp.current_user()
        return sp
    except Exception as e:
        # This will catch missing credentials or failed authentication
        if "No client id" in str(e):
            raise Exception("Spotify credentials not found. Please set them as environment variables.")
        return None

class Skill(BaseSkill):
    name = "media"
    keywords = [
        "music", "song", "spotify", "play", "pause", "resume",
        "stop", "next", "previous", "volume", "youtube", "sound"
    ]

    def __init__(self):
        super().__init__()
        self.spotify_client = None

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
    # Spotify Control (New Spotipy Implementation)
    # ───────────────────────────────────────────────
    async def _spotify_control(self, text: str, jarvis) -> str:
        """Controls Spotify using the official Web API via Spotipy."""
        try:
            # Get authenticated client
            if not self.spotify_client:
                self.spotify_client = get_spotify_client()
            
            if not self.spotify_client:
                return "Spotify authentication failed. Please check your credentials and setup."

            sp = self.spotify_client

            # Play specific track
            match = re.search(r"play\s+(.+?)(?:\s+on\s+spotify)?$", text)
            if match:
                query = match.group(1).strip()
                results = sp.search(q=f"track:{query}", type="track", limit=1)
                tracks = results.get('tracks', {}).get('items', [])
                
                if not tracks:
                    return f"Sorry, I couldn't find the song '{query}' on Spotify."
                
                track = tracks[0]
                track_uri = track['uri']
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                
                sp.start_playback(uris=[track_uri])
                return f"Now playing '{track_name}' by {artist_name} on Spotify."

            # Other playback controls
            if "pause" in text:
                sp.pause_playback()
                return "Spotify paused."
            if "resume" in text or "play" in text:
                sp.start_playback()
                return "Resuming Spotify."
            if "next" in text:
                sp.next_track()
                return "Skipping to the next track."
            if "previous" in text:
                sp.previous_track()
                return "Playing the previous track."

            return "Please specify what to do with Spotify (e.g., 'play [song]', 'pause', 'next')."

        except Exception as e:
            return f"Spotify control failed: {e}"

    # ───────────────────────────────────────────────
    # YouTube Control (via Chrome) - Unchanged
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
    # System Media Control (generic) - Unchanged
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