# system_tray.py – Windows-console-safe logging + correct signature
import logging
import threading
from typing import Callable, Optional

import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger("AI_Assistant.SystemTray")


class SystemTray:
    """
    System-tray icon for Jarvis assistant.
    Provides quick access and minimization option.
    """

    def __init__(
        self,
        on_show: Callable,
        on_hide: Callable,
        on_voice: Callable,
        on_settings: Callable,
        on_exit: Callable,
    ):
        self.on_show = on_show
        self.on_hide = on_hide
        self.on_voice = on_voice
        self.on_settings = on_settings
        self.on_exit = on_exit

        self.icon: Optional[pystray.Icon] = None
        self.is_visible = True
        self.thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    #  Icon generator (colour changes with state)
    # ------------------------------------------------------------------
    def create_icon_image(self, state: str = "idle") -> Image.Image:
        img = Image.new("RGB", (64, 64), color="black")
        draw = ImageDraw.Draw(img)
        colours = {
            "idle": "#00ffbf",
            "listening": "#00bfff",
            "speaking": "#00ff88",
            "thinking": "#ffbf00",
            "error": "#ff0000",
        }
        colour = colours.get(state, "#00ffbf")
        draw.ellipse([8, 8, 56, 56], fill=colour, outline=colour)
        draw.ellipse([16, 16, 48, 48], fill="#1a1a2e", outline=colour)
        draw.ellipse([28, 28, 36, 36], fill=colour)
        return img

    def update_icon(self, state: str) -> None:
        if self.icon:
            try:
                self.icon.icon = self.create_icon_image(state)
            except Exception as e:
                logger.error("Error updating icon: %s", e)

    # ------------------------------------------------------------------
    #  Menu callbacks
    # ------------------------------------------------------------------
    def toggle_visibility(self, icon, item):
        if self.is_visible:
            self.on_hide()
            self.is_visible = False
            item.text = "Show Widget"
        else:
            self.on_show()
            self.is_visible = True
            item.text = "Hide Widget"

    def trigger_voice(self, icon, item):
        self.on_voice()

    def open_settings(self, icon, item):
        self.on_settings()

    def exit_app(self, icon, item):
        logger.info("Exit requested from system tray")
        if self.icon:
            self.icon.stop()
        self.on_exit()

    # ------------------------------------------------------------------
    #  Menu definition  (emojis safe here – PIL draws them, no console)
    # ------------------------------------------------------------------
    def create_menu(self):
        return pystray.Menu(
            pystray.MenuItem("🎤 Voice Command", self.trigger_voice, default=True),
            pystray.MenuItem(
                "Hide Widget" if self.is_visible else "Show Widget", self.toggle_visibility
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙️ Settings", self.open_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Exit", self.exit_app),
        )

    # ------------------------------------------------------------------
    #  Life-cycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            logger.warning("System tray already running")
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("System tray started")

    def _run(self) -> None:
        try:
            self.icon = pystray.Icon(
                "Jarvis",
                self.create_icon_image("idle"),
                "Jarvis Assistant",
                self.create_menu(),
            )
            self.icon.run()
        except Exception as e:
            logger.error("System tray error: %s", e, exc_info=True)

    def stop(self) -> None:
        if self.icon:
            try:
                self.icon.stop()
            except Exception as e:
                logger.error("Error stopping tray: %s", e)
        self.icon = None
        logger.info("System tray stopped")

    def notify(self, title: str, message: str, duration: int = 3) -> None:
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception as e:
                logger.error("Notification error: %s", e)


# --------------------------------------------------------------------------
#  Quick self-test
# --------------------------------------------------------------------------
if __name__ == "__main__":

    def dummy():
        print("Callback triggered")

    tray = SystemTray(dummy, dummy, dummy, dummy, lambda: print("Exiting…"))
    tray.start()
    try:
        while True:
            import time

            time.sleep(1)
    except KeyboardInterrupt:
        tray.stop()
