"""
═══════════════════════════════════════════════════════════════════════════════
FILE: jarvis_app_control.py
DESCRIPTION: Unified Windows App Control System for Jarvis
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from jarvis_core_optimized import JarvisIntegrated
import psutil
import pyautogui
import pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

# Optional Windows-only imports
try:
    import win32gui
    import win32con
    import win32process
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    IS_WINDOWS = True
except Exception:
    IS_WINDOWS = False

logger = logging.getLogger("Jarvis.AppControl")
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.4


# ════════════════════════════════════════════════════════════════════════════
# BASIC WINDOWS APP CONTROLLER
# ════════════════════════════════════════════════════════════════════════════

class WindowsAppController:
    """Lightweight app launcher and closer (base class)."""

    APP_PATHS = {
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "notepad": "notepad.exe",
        "vscode": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "spotify": r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
        "discord": r"C:\Users\{user}\AppData\Local\Discord\Update.exe",
        "whatsapp": r"C:\Users\{user}\AppData\Local\WhatsApp\WhatsApp.exe",
    }

    def __init__(self):
        self.username = os.getlogin()
        for k, v in self.APP_PATHS.items():
            self.APP_PATHS[k] = v.replace("{user}", self.username)

    def open_app(self, app_name: str) -> bool:
        """Open application by name."""
        try:
            app = app_name.lower()
            if app in self.APP_PATHS:
                subprocess.Popen([self.APP_PATHS[app]])
                logger.info(f"Opened {app_name}")
                return True
            subprocess.Popen(app_name, shell=True)
            logger.info(f"Executed: {app_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to open {app_name}: {e}")
            return False

    def close_app(self, app_name: str) -> bool:
        """Close app by process name."""
        closed = False
        for proc in psutil.process_iter(["name"]):
            try:
                if app_name.lower() in proc.info["name"].lower():
                    proc.terminate()
                    closed = True
                    logger.info(f"Closed {proc.info['name']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return closed

    def is_running(self, app_name: str) -> bool:
        for proc in psutil.process_iter(["name"]):
            try:
                if app_name.lower() in (proc.info["name"] or "").lower():
                    return True
            except Exception:
                pass
        return False


# ════════════════════════════════════════════════════════════════════════════
# DEEP APP CONTROLLER (AUTOMATION)
# ════════════════════════════════════════════════════════════════════════════

class DeepAppController:
    """Advanced app control (keyboard, search, typing, volume, etc.)."""

    def __init__(self):
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = interface.QueryInterface(IAudioEndpointVolume)
        except Exception:
            self.volume = None

    # ─── Utility Methods ──────────────────────────────────────────────────────

    def _focus_window(self, keyword: str) -> bool:
        if not IS_WINDOWS:
            return False
        hwnd = None

        def callback(h, _):
            nonlocal hwnd
            try:
                title = win32gui.GetWindowText(h)
                if keyword.lower() in title.lower():
                    hwnd = h
                    return False
            except Exception:
                pass
            return True

        win32gui.EnumWindows(callback, None)
        if hwnd:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.3)
                return True
            except Exception:
                pass
        return False

    # ─── Spotify ─────────────────────────────────────────────────────────────
    def spotify_play(self, query: Optional[str] = None) -> str:
        if not self._focus_window("spotify"):
            return "Spotify not found."
        pyautogui.hotkey("ctrl", "l")
        if query:
            pyautogui.write(query, interval=0.03)
        pyautogui.press("enter")
        return f"Playing '{query}' on Spotify" if query else "Resumed Spotify"

    def spotify_pause(self) -> str:
        pyautogui.press("playpause")
        return "Paused Spotify"

    # ─── Chrome ──────────────────────────────────────────────────────────────
    def chrome_search(self, query: str) -> str:
        if not self._focus_window("chrome"):
            return "Chrome not found."
        pyautogui.hotkey("ctrl", "l")
        pyautogui.write(query, interval=0.03)
        pyautogui.press("enter")
        return f"Searching Chrome for '{query}'"

    # ─── Notepad ─────────────────────────────────────────────────────────────
    def notepad_type(self, text: str) -> str:
        if not self._focus_window("notepad"):
            return "Notepad not found."
        pyautogui.write(text, interval=0.03)
        return "Typed text in Notepad."

    def notepad_save(self, filename: str = "document.txt") -> str:
        if not self._focus_window("notepad"):
            return "Notepad not found."
        pyautogui.hotkey("ctrl", "s")
        pyautogui.write(filename, interval=0.04)
        pyautogui.press("enter")
        return f"Saved file as {filename}"

    # ─── Discord / WhatsApp ──────────────────────────────────────────────────
    def discord_send_message(self, message: str) -> str:
        if not self._focus_window("discord"):
            return "Discord not found."
        pyautogui.write(message, interval=0.02)
        pyautogui.press("enter")
        return "Sent message on Discord."

    def whatsapp_send_message(self, message: str, contact: Optional[str] = None) -> str:
        if not self._focus_window("whatsapp"):
            return "WhatsApp not found."
        if contact:
            pyautogui.hotkey("ctrl", "f")
            time.sleep(0.2)
            pyautogui.write(contact, interval=0.03)
            time.sleep(0.4)
            pyautogui.press("enter")
        pyautogui.write(message, interval=0.03)
        pyautogui.press("enter")
        return f"Sent '{message}'{' to ' + contact if contact else ''} on WhatsApp."

    # ─── Volume ──────────────────────────────────────────────────────────────
    def volume_up(self):
        pyautogui.press("volumeup")
        return "Volume increased"

    def volume_down(self):
        pyautogui.press("volumedown")
        return "Volume decreased"


# ════════════════════════════════════════════════════════════════════════════
# APP SCANNER (FUZZY DETECTION)
# ════════════════════════════════════════════════════════════════════════════

class AppScanner:
    """Finds best app match using fuzzy search."""
    def __init__(self):
        self.known_apps = list(WindowsAppController.APP_PATHS.keys())

    def find_best_match(self, query: str) -> Optional[str]:
        query = query.lower()
        matches = [app for app in self.known_apps if query in app]
        return matches[0] if matches else None


# ════════════════════════════════════════════════════════════════════════════
# MAIN UNIFIED CONTROL LAYER
# ════════════════════════════════════════════════════════════════════════════

class JarvisAppControl:
    """Main orchestrator combining all app control features."""

    def __init__(self):
        self.basic = WindowsAppController()
        self.deep = DeepAppController()
        self.scanner = AppScanner()

    async def handle_command(self, text: str) -> Optional[str]:
        text = text.lower().strip()
        logger.info(f"[AppControl] Received: {text}")

        # --- detect app ---
        app = self.scanner.find_best_match(text)
        if not app:
            return None

        # --- open app if needed ---
        if not self.basic.is_running(app):
            self.basic.open_app(app)
            await asyncio.sleep(2)

        # --- route to action handlers ---
        if "spotify" in app:
            if "pause" in text:
                return self.deep.spotify_pause()
            if "play" in text or "search" in text:
                m = re.search(r"(?:play|search)\s+(?:for\s+)?(.+)", text)
                query = m.group(1).strip() if m else None
                return self.deep.spotify_play(query)

        if "chrome" in app:
            m = re.search(r"(?:search|google)\s+(?:for\s+)?(.+)", text)
            if m:
                return self.deep.chrome_search(m.group(1))

        if "notepad" in app:
            if "type" in text:
                m = re.search(r'(?:type|write)\s+"(.+)"', text)
                if m:
                    return self.deep.notepad_type(m.group(1))
            if "save" in text:
                return self.deep.notepad_save()

        if "discord" in app and "send" in text:
            m = re.search(r'(?:send|message)\s+"(.+)"', text)
            if m:
                return self.deep.discord_send_message(m.group(1))

        if "whatsapp" in app and "send" in text:
            m = re.search(r'(?:send|message)\s+"(.+?)"(?:\s+to\s+(\w+))?', text)
            if m:
                msg = m.group(1)
                contact = m.group(2)
                return self.deep.whatsapp_send_message(msg, contact)

        if "volume up" in text:
            return self.deep.volume_up()
        if "volume down" in text:
            return self.deep.volume_down()

        if "close" in text or "quit" in text:
            self.basic.close_app(app)
            return f"Closed {app}"

        # Default open
        if "open" in text:
            return f"Opened {app}"

        return None


# ════════════════════════════════════════════════════════════════════════════
# APP CONTROL INTEGRATION (CALLED BY jarvis_complete)
# ════════════════════════════════════════════════════════════════════════════

class AppControlIntegration:
    """Interface used by JarvisIntegrated to handle natural language."""

    def __init__(self):
        self.controller = JarvisAppControl()

    def parse_command(self, text: str) -> Optional[str]:
        """Blocking wrapper for async handler."""
        try:
            return asyncio.run(self.controller.handle_command(text))
        except RuntimeError:
            # If event loop is already running (e.g., in async Jarvis)
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.controller.handle_command(text))
        except Exception as e:
            logger.error(f"App control error: {e}")
            return f"Error handling command: {e}"


# ════════════════════════════════════════════════════════════════════════════
# TEST ENTRY
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    integ = AppControlIntegration()
    while True:
        cmd = input("Command> ")
        if cmd.lower() in ("exit", "quit"):
            break
        print(integ.parse_command(cmd))
