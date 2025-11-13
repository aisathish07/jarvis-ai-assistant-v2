# skills/app_integration_skill.py - Deep app integration skill (async-safe)
import asyncio
import logging
import re
import sys
import time  # used only in thread-executed functions if needed
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.append(str(Path(__file__).parent.parent))
from jarvis_skills import BaseSkill
from jarvis_app_controller import AppController

logger = logging.getLogger("AI_Assistant.AppIntegrationSkill")


class Skill(BaseSkill):
    """
    Skill for opening apps and executing commands within them.
    """

    name = "app_integration"
    keywords = [
        "open", "spotify", "chrome", "discord", "whatsapp", "notepad", "vscode",
        "play", "search", "send", "type", "save", "google", "browse", "look up",
        "message", "mute", "pause", "next", "skip", "previous", "back", "volume"
    ]

    def __init__(self):
        super().__init__()
        self.controller = None
        self._controller_loaded = False
        self.assistant = None

    async def handle(self, text: str, jarvis: Any) -> Optional[str]:
        """
        Standard skill entry point.
        """
        # The original skill expected an 'assistant' object with callbacks.
        # We can mimic this by attaching the main jarvis instance.
        self.assistant = jarvis
        
        # The original skill had a complex command parser in `on_command`.
        # We'll call that method to reuse the existing logic.
        # The `context` dictionary is not fully used here, so we pass a simple one.
        context = {'source': 'jarvis_core'}
        return self.on_command(text, context)

    # -------------------- Async helpers --------------------
    async def _open_and_execute(self, app_name: str, action: str, context: Dict[str, Any]) -> str:
        """
        Open application (via assistant's open_app) and then execute action via controller.
        Both operations are executed in threads if blocking.
        """
        try:
            # call assistant-provided open_app (if available) in thread
            open_fn = None
            try:
                open_fn = getattr(self, "assistant", {}).get("open_app")  # type: ignore
            except Exception:
                open_fn = None

            if callable(open_fn):
                await asyncio.to_thread(open_fn, app_name)
                # allow app to initialize
                await asyncio.sleep(1.8)

            controller = self._get_controller()
            if not controller:
                return "App controller unavailable."

            # execute controller command in thread (controller is synchronous)
            return await asyncio.to_thread(self._execute_action, app_name, action, controller)

        except Exception as e:
            logger.exception("Error in _open_and_execute: %s", e)
            return f"Failed to execute '{action}' in {app_name}: {e}"

    def _execute_action(self, app_name: str, action: str, controller) -> str:
        """Synchronous executor used inside thread (keeps parsing and controller calls together)."""
        try:
            action = action.lower()

            # Spotify
            if "spotify" in app_name.lower():
                if "play" in action:
                    m = re.search(r"(?:play|search)\s+(?:for\s+)?(.+)", action)
                    if m:
                        query = m.group(1).strip()
                        return controller.execute_command("spotify", "search", query=query)
                    return controller.execute_command("spotify", "play")
                if "pause" in action:
                    return controller.execute_command("spotify", "pause")
                if "next" in action or "skip" in action:
                    return controller.execute_command("spotify", "next")
                if "previous" in action or "back" in action:
                    return controller.execute_command("spotify", "previous")
                if "volume up" in action or "louder" in action:
                    return controller.execute_command("spotify", "volume_up")
                if "volume down" in action or "quieter" in action:
                    return controller.execute_command("spotify", "volume_down")

            # Chrome / Browser
            if "chrome" in app_name.lower() or "browser" in app_name.lower():
                if "search" in action or "google" in action:
                    m = re.search(r"(?:search|google)\s+(?:for\s+)?(.+)", action)
                    if m:
                        query = m.group(1).strip()
                        return controller.execute_command("chrome", "search", query=query)
                if "go to" in action or "open" in action:
                    m = re.search(r"(?:go to|open)\s+(.+)", action)
                    if m:
                        url = m.group(1).strip()
                        return controller.execute_command("chrome", "go_to", url=url)
                if "new tab" in action:
                    return controller.execute_command("chrome", "new_tab")
                if "close tab" in action:
                    return controller.execute_command("chrome", "close_tab")

            # Notepad
            if "notepad" in app_name.lower():
                if "type" in action or "write" in action:
                    m = re.search(r"(?:type|write)\s+(.+)", action)
                    if m:
                        text = m.group(1).strip()
                        return controller.execute_command("notepad", "type", text=text)
                if "save" in action:
                    m = re.search(r"save\s+(?:as\s+)?(.+)", action)
                    filename = m.group(1).strip() if m else "document.txt"
                    return controller.execute_command("notepad", "save", filename=filename)

            # VS Code
            if "vscode" in app_name.lower() or "visual studio" in app_name.lower():
                if "new file" in action:
                    return controller.execute_command("vscode", "new_file")
                if "save" in action:
                    return controller.execute_command("vscode", "save")
                if "run" in action:
                    return controller.execute_command("vscode", "run")

            # Discord
            if "discord" in app_name.lower():
                if "send" in action or "message" in action:
                    m = re.search(r"(?:send|message)\s+(.+)", action)
                    if m:
                        message = m.group(1).strip()
                        return controller.execute_command(
                            "discord", "send_message", message=message
                        )
                if "mute" in action:
                    return controller.execute_command("discord", "mute")

            # WhatsApp
            if "whatsapp" in app_name.lower():
                if "send" in action or "message" in action:
                    m = re.search(r"(?:send|message)\s+(.+?)(?:\s+to\s+(.+))?$", action)
                    if m:
                        message = m.group(1).strip()
                        contact = m.group(2).strip() if m.group(2) else None
                        if contact:
                            controller.execute_command(
                                "whatsapp", "search_contact", contact=contact
                            )
                            time.sleep(0.8)
                        return controller.execute_command(
                            "whatsapp", "send_message", message=message
                        )

            return f"I don't know how to '{action}' in {app_name}"
        except Exception as e:
            logger.exception("Error executing action: %s", e)
            return f"Failed to run action: {e}"

    # -------------------- Async wrappers for direct handlers --------------------
    async def _handle_spotify_async(self, cmd: str) -> str:
        ctr = self._get_controller()
        if not ctr:
            return "App controller unavailable."
        # ensure spotify running via assistant open_app if available
        open_fn = getattr(self, "assistant", {}).get("open_app")
        if callable(open_fn) and not await asyncio.to_thread(ctr.is_app_running, "spotify"):
            await asyncio.to_thread(open_fn, "spotify")
            await asyncio.sleep(1.6)
        # run in thread
        return await asyncio.to_thread(lambda: self._handle_spotify_sync(cmd, ctr))

    def _handle_spotify_sync(self, cmd: str, controller) -> str:
        # reuse logic from earlier (synchronous)
        try:
            if "play" in cmd:
                m = re.search(
                    r"play\s+(?:music\s+)?(?:search\s+)?(?:for\s+)?(.+?)(?:\s+on spotify)?$",
                    cmd,
                    re.I,
                )
                if m:
                    query = m.group(1).strip()
                    return controller.execute_command("spotify", "search", query=query)
                return controller.execute_command("spotify", "play")
            if "pause" in cmd:
                return controller.execute_command("spotify", "pause")
            if "next" in cmd or "skip" in cmd:
                return controller.execute_command("spotify", "next")
            if "previous" in cmd or "back" in cmd:
                return controller.execute_command("spotify", "previous")
            if "volume up" in cmd or "louder" in cmd:
                return controller.execute_command("spotify", "volume_up")
            if "volume down" in cmd or "quieter" in cmd:
                return controller.execute_command("spotify", "volume_down")
        except Exception as e:
            logger.exception("Spotify handler failed: %s", e)
            return "Spotify action failed."
        return "I couldn't interpret that Spotify command."

    async def _handle_chrome_async(self, cmd: str) -> str:
        ctr = self._get_controller()
        if not ctr:
            return "App controller unavailable."
        if not await asyncio.to_thread(ctr.is_app_running, "chrome"):
            open_fn = getattr(self, "assistant", {}).get("open_app")
            if callable(open_fn):
                await asyncio.to_thread(open_fn, "chrome")
                await asyncio.sleep(1.6)
        return await asyncio.to_thread(lambda: self._handle_chrome_sync(cmd, ctr))

    def _handle_chrome_sync(self, cmd: str, controller) -> str:
        try:
            if "search" in cmd or "google" in cmd:
                m = re.search(r"(?:search|google)\s+(?:for\s+)?(.+)", cmd, re.I)
                if m:
                    query = m.group(1).strip()
                    return controller.execute_command("chrome", "search", query=query)
            if "new tab" in cmd:
                return controller.execute_command("chrome", "new_tab")
            if "close tab" in cmd:
                return controller.execute_command("chrome", "close_tab")
        except Exception as e:
            logger.exception("Chrome handler failed: %s", e)
            return "Chrome action failed."
        return "I couldn't interpret that Chrome command."

    async def _handle_discord_async(self, cmd: str) -> str:
        ctr = self._get_controller()
        if not ctr:
            return "App controller unavailable."
        if not await asyncio.to_thread(ctr.is_app_running, "discord"):
            open_fn = getattr(self, "assistant", {}).get("open_app")
            if callable(open_fn):
                await asyncio.to_thread(open_fn, "discord")
                await asyncio.sleep(1.6)
        return await asyncio.to_thread(lambda: self._handle_discord_sync(cmd, ctr))

    def _handle_discord_sync(self, cmd: str, controller) -> str:
        try:
            if "mute" in cmd:
                return controller.execute_command("discord", "mute")
            if "send" in cmd or "message" in cmd:
                m = re.search(r"(?:send|message)\s+(.+?)(?:\s+on discord)?$", cmd, re.I)
                if m:
                    message = m.group(1).strip()
                    return controller.execute_command("discord", "send_message", message=message)
        except Exception as e:
            logger.exception("Discord handler failed: %s", e)
            return "Discord action failed."
        return "I couldn't interpret that Discord command."

    async def _handle_whatsapp_async(self, cmd: str) -> str:
        ctr = self._get_controller()
        if not ctr:
            return "App controller unavailable."
        if not await asyncio.to_thread(ctr.is_app_running, "whatsapp"):
            open_fn = getattr(self, "assistant", {}).get("open_app")
            if callable(open_fn):
                await asyncio.to_thread(open_fn, "whatsapp")
                await asyncio.sleep(2.4)
        return await asyncio.to_thread(lambda: self._handle_whatsapp_sync(cmd, ctr))

    def _handle_whatsapp_sync(self, cmd: str, controller) -> str:
        try:
            if "send" in cmd or "message" in cmd:
                m = re.search(
                    r"(?:send|message)\s+(.+?)(?:\s+to\s+(.+?))?(?:\s+on whatsapp)?$", cmd, re.I
                )
                if m:
                    message = m.group(1).strip()
                    contact = m.group(2).strip() if m.group(2) else None
                    if contact:
                        controller.execute_command("whatsapp", "search_contact", contact=contact)
                        time.sleep(0.8)
                    return controller.execute_command("whatsapp", "send_message", message=message)
        except Exception as e:
            logger.exception("WhatsApp handler failed: %s", e)
            return "WhatsApp action failed."
        return "I couldn't interpret that WhatsApp command."

    # Utilities used by plugin system to describe the skill
    def help(self) -> str:
        return """
App Integration Skill - Natural Commands:
• "open spotify and play [song]"
• "play [song] on spotify"
• "search google for [query]"
• "send [message] on discord"
• "send [message] to [contact] on whatsapp"
"""
