# app_controller.py - Deep integration with applications (hardening + retries)
from __future__ import annotations

import logging
import platform
import time
from typing import List, Optional

import pyautogui
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Windows-specific imports guarded
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    try:
        import psutil
        import win32con
        import win32gui
        import win32process
    except Exception:
        # fall back gracefully if pywin32 not available
        win32gui = win32con = win32process = None
        import psutil  # psutil usually available or will raise

logger = logging.getLogger("AI_Assistant.AppController")

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.4


class AppController:
    """
    Controls applications after opening them.
    Supports keyboard shortcuts, mouse clicks, and window management.
    """

    def __init__(self):
        self.system = platform.system()
        self.active_app: Optional[str] = None
        self.active_window_handle: Optional[int] = None
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = interface.QueryInterface(IAudioEndpointVolume)
        except Exception:
            self.volume = None

        self.app_commands = {
            "spotify": {
                "play": self._spotify_play,
                "pause": self._spotify_pause,
                "next": self._spotify_next,
                "previous": self._spotify_previous,
                "search": self._spotify_search,
                "volume_up": self._spotify_volume_up,
                "volume_down": self._spotify_volume_down,
            },
            "chrome": {
                "new_tab": self._chrome_new_tab,
                "close_tab": self._chrome_close_tab,
                "search": self._chrome_search,
                "go_to": self._chrome_goto,
            },
            "notepad": {
                "type": self._notepad_type,
                "save": self._notepad_save,
            },
            "vscode": {
                "new_file": self._vscode_new_file,
                "save": self._vscode_save,
                "run": self._vscode_run,
            },
            "discord": {
                "send_message": self._discord_send_message,
                "mute": self._discord_mute,
            },
            "whatsapp": {
                "send_message": self._whatsapp_send_message,
                "search_contact": self._whatsapp_search_contact,
            },
        }

    def set_volume(self, lvl: int) -> str:
        if self.volume:
            self.volume.SetMasterVolumeLevelScalar(max(0.0, min(1.0, lvl / 100.0)), None)
            return f"Volume set to {lvl}%"
        return "Volume control unavailable"

    def change_volume(self, delta: int) -> str:
        if not self.volume:
            return "Volume control unavailable"
        current = int(self.volume.GetMasterVolumeLevelScalar() * 100)
        new = max(0, min(100, current + delta))
        self.set_volume(new)
        return f"Volume {new}%"

    def _ensure_windows(self) -> bool:
        if not IS_WINDOWS:
            logger.warning("AppController feature is Windows-only on this build.")
            return False
        if win32gui is None:
            logger.warning("pywin32 not available; limited window operations.")
            return False
        return True

    def find_window_by_title(
        self, title_contains: str, retries: int = 3, delay: float = 0.6
    ) -> Optional[int]:
        """Find window handle by partial title match (Windows). Retries once to allow apps to start."""
        if not self._ensure_windows():
            return None

        title_contains = title_contains.lower()
        for attempt in range(retries):
            found_handle = None

            def callback(hwnd, _):
                nonlocal found_handle
                try:
                    if win32gui.IsWindowVisible(hwnd):
                        window_title = win32gui.GetWindowText(hwnd) or ""
                        if title_contains in window_title.lower():
                            found_handle = hwnd
                            return False  # stop enumeration
                except Exception:
                    pass
                return True

            try:
                win32gui.EnumWindows(callback, None)
                if found_handle:
                    return found_handle
            except Exception:
                logger.exception("Window enumeration failed", exc_info=True)
            time.sleep(delay)
        return None

    def focus_window(self, handle: int, fallback_click: bool = False) -> bool:
        """Bring window to foreground. Returns True on success."""
        if not self._ensure_windows() or not handle:
            return False
        try:
            if win32gui.IsIconic(handle):
                win32gui.ShowWindow(handle, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(handle)
            time.sleep(0.25)
            return True
        except Exception:
            logger.exception("Failed to focus window")
            if fallback_click:
                try:
                    # best-effort fallback (dangerous on multi-screen setups)
                    pyautogui.click(100, 10)
                    time.sleep(0.25)
                    return True
                except Exception:
                    pass
            return False

    def is_app_running(self, app_name: str) -> bool:
        """Check if application is currently running."""
        try:
            app_name_lower = app_name.lower()
            for proc in psutil.process_iter(["name"]):
                try:
                    pname = (proc.info.get("name") or "").lower()
                    if app_name_lower in pname:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            logger.exception("is_app_running failed")
        return False

    def wait_for_app_start(self, app_name: str, timeout: int = 10) -> bool:
        """Wait for application start; returns True if detected."""
        start = time.time()
        while time.time() - start < timeout:
            if self.is_app_running(app_name):
                time.sleep(1.0)
                return True
            time.sleep(0.5)
        return False

    # ==================== Spotify Controls ====================
    def _spotify_play(self, **kwargs) -> str:
        try:
            pyautogui.press("playpause")
            return "Playing Spotify"
        except Exception:
            logger.exception("Spotify play failed")
            return "Failed to play Spotify"

    def _spotify_pause(self, **kwargs) -> str:
        try:
            pyautogui.press("playpause")
            return "Paused Spotify"
        except Exception:
            logger.exception("Spotify pause failed")
            return "Failed to pause Spotify"

    def _spotify_next(self, **kwargs) -> str:
        try:
            pyautogui.press("nexttrack")
            return "Playing next track"
        except Exception:
            logger.exception("Spotify next failed")
            return "Failed to skip track"

    def _spotify_previous(self, **kwargs) -> str:
        try:
            pyautogui.press("prevtrack")
            return "Playing previous track"
        except Exception:
            logger.exception("Spotify previous failed")
            return "Failed to go to previous track"

    def _spotify_search(self, query: str = "", **kwargs) -> str:
        try:
            if not self._ensure_windows():
                return "Spotify search available on Windows only"
            handle = self.find_window_by_title("spotify")
            if not handle:
                return "Spotify window not found"
            if not self.focus_window(handle):
                return "Couldn't focus Spotify window"
            time.sleep(0.4)
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.2)
            pyautogui.write(query, interval=0.03)
            time.sleep(0.15)
            pyautogui.press("enter")
            return f"Searching Spotify for '{query}'"
        except Exception:
            logger.exception("Spotify search failed")
            return "Spotify search failed"

    def _spotify_volume_up(self, **kwargs) -> str:
        try:
            pyautogui.press("volumeup")
            return "Volume increased"
        except Exception:
            logger.exception("Volume up failed")
            return "Failed to change volume"

    def _spotify_volume_down(self, **kwargs) -> str:
        try:
            pyautogui.press("volumedown")
            return "Volume decreased"
        except Exception:
            logger.exception("Volume down failed")
            return "Failed to change volume"

    # ==================== Chrome Controls ====================
    def _chrome_new_tab(self, **kwargs) -> str:
        try:
            if not self._ensure_windows():
                return "Chrome operations are Windows-only in this build"
            handle = self.find_window_by_title("chrome")
            if handle:
                self.focus_window(handle)
                pyautogui.hotkey("ctrl", "t")
                return "Opened new tab"
            return "Chrome window not found"
        except Exception:
            logger.exception("Chrome new tab failed")
            return "Failed to open new tab"

    def _chrome_close_tab(self, **kwargs) -> str:
        try:
            if not self._ensure_windows():
                return "Chrome operations are Windows-only"
            handle = self.find_window_by_title("chrome")
            if handle:
                self.focus_window(handle)
                pyautogui.hotkey("ctrl", "w")
                return "Closed tab"
            return "Chrome window not found"
        except Exception:
            logger.exception("Chrome close tab failed")
            return "Failed to close tab"

    def _chrome_search(self, query: str = "", **kwargs) -> str:
        try:
            if not self._ensure_windows():
                return "Chrome operations are Windows-only"
            handle = self.find_window_by_title("chrome")
            if not handle:
                return "Chrome window not found"
            self.focus_window(handle)
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.15)
            pyautogui.write(query, interval=0.03)
            pyautogui.press("enter")
            return f"Searching for '{query}'"
        except Exception:
            logger.exception("Chrome search failed")
            return "Failed to search in Chrome"

    def _chrome_goto(self, url: str = "", **kwargs) -> str:
        return self._chrome_search(query=url)

    # ==================== Notepad Controls ====================
    def _notepad_type(self, text: str = "", **kwargs) -> str:
        try:
            if not self._ensure_windows():
                return "Notepad is Windows-only"
            handle = self.find_window_by_title("notepad")
            if not handle:
                return "Notepad window not found"
            self.focus_window(handle)
            pyautogui.write(text, interval=0.02)
            return "Typed text"
        except Exception:
            logger.exception("Notepad type failed")
            return "Failed to type in Notepad"

    def _notepad_save(self, filename: str = "document.txt", **kwargs) -> str:
        try:
            if not self._ensure_windows():
                return "Notepad save is Windows-only"
            handle = self.find_window_by_title("notepad")
            if not handle:
                return "Notepad window not found"
            self.focus_window(handle)
            pyautogui.hotkey("ctrl", "s")
            time.sleep(0.5)
            pyautogui.write(filename, interval=0.04)
            pyautogui.press("enter")
            return f"Saved as {filename}"
        except Exception:
            logger.exception("Notepad save failed")
            return "Failed to save Notepad file"

    # ==================== VS Code ====================
    def _vscode_new_file(self, **kwargs) -> str:
        try:
            handle = self.find_window_by_title("visual studio code")
            if handle:
                self.focus_window(handle)
                pyautogui.hotkey("ctrl", "n")
                return "Created new file"
            return "VS Code not found"
        except Exception:
            logger.exception("VS Code new file failed")
            return "Failed to create file"

    def _vscode_save(self, **kwargs) -> str:
        try:
            handle = self.find_window_by_title("visual studio code")
            if handle:
                self.focus_window(handle)
                pyautogui.hotkey("ctrl", "s")
                return "File saved"
            return "VS Code not found"
        except Exception:
            logger.exception("VS Code save failed")
            return "Failed to save file"

    def _vscode_run(self, **kwargs) -> str:
        try:
            handle = self.find_window_by_title("visual studio code")
            if handle:
                self.focus_window(handle)
                pyautogui.press("f5")
                return "Running code"
            return "VS Code not found"
        except Exception:
            logger.exception("VS Code run failed")
            return "Failed to run code"

    # ==================== Discord ====================
    def _discord_send_message(self, message: str = "", **kwargs) -> str:
        try:
            handle = self.find_window_by_title("discord")
            if not handle:
                return "Discord not found"
            self.focus_window(handle)
            time.sleep(0.2)
            pyautogui.write(message, interval=0.02)
            pyautogui.press("enter")
            return "Sent message"
        except Exception:
            logger.exception("Discord send failed")
            return "Failed to send Discord message"

    def _discord_mute(self, **kwargs) -> str:
        try:
            handle = self.find_window_by_title("discord")
            if handle:
                self.focus_window(handle)
                pyautogui.hotkey("ctrl", "shift", "m")
                return "Toggled mute"
            return "Discord not found"
        except Exception:
            logger.exception("Discord mute failed")
            return "Failed to toggle mute"

    # ==================== WhatsApp ====================
    def _whatsapp_send_message(self, message: str = "", **kwargs) -> str:
        try:
            handle = self.find_window_by_title("whatsapp")
            if not handle:
                return "WhatsApp not found"
            self.focus_window(handle)
            time.sleep(0.25)
            pyautogui.write(message, interval=0.02)
            pyautogui.press("enter")
            return "Sent WhatsApp message"
        except Exception:
            logger.exception("WhatsApp send failed")
            return "Failed to send WhatsApp message"

    def _whatsapp_search_contact(self, contact: str = "", **kwargs) -> str:
        try:
            handle = self.find_window_by_title("whatsapp")
            if not handle:
                return "WhatsApp not found"
            self.focus_window(handle)
            pyautogui.hotkey("ctrl", "f")
            time.sleep(0.2)
            pyautogui.write(contact, interval=0.03)
            time.sleep(0.35)
            pyautogui.press("enter")
            return f"Opened chat with {contact}"
        except Exception:
            logger.exception("WhatsApp contact search failed")
            return "Failed to search contact"

    # ==================== PUBLIC API ====================
    def execute_command(self, app_name: str, command: str, **params) -> str:
        app_name = app_name.lower()
        command = command.lower()

        if app_name not in self.app_commands:
            return f"App '{app_name}' not supported yet"

        if command not in self.app_commands[app_name]:
            available = ", ".join(self.app_commands[app_name].keys())
            return f"Command '{command}' not available. Available: {available}"

        try:
            func = self.app_commands[app_name][command]
            return func(**params)
        except Exception as e:
            logger.exception("Command execution failed: %s", e)
            return f"Error executing command: {e}"

    def list_supported_apps(self) -> List[str]:
        return list(self.app_commands.keys())

    def list_app_commands(self, app_name: str) -> List[str]:
        app_name = app_name.lower()
        if app_name in self.app_commands:
            return list(self.app_commands[app_name].keys())
        return []
