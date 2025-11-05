#!/usr/bin/env python3
"""
Jarvis – uncensored local edition.
Old GUI mode, no wizard, no cloud.
"""

import logging
import queue

from app_scanner import AppManager
from attic.predictive_model import PredictiveModel
from attic.system_tray import SystemTray
from command_processor import CommandProcessor
from config import Config
from gui import AssistantGUI
from memory_manager import MemoryManager
from tts import TextToSpeech
from wake_word import WakeWordDetector

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AI_Assistant.OldGUI")


# -------------------------------------------------
# 1.  Start components (same as standalone)
# -------------------------------------------------
def start_components():
    Config.setup_directories()
    Config.validate_configuration()
    Config.optimize_for_system()

    memory = MemoryManager(predictor=PredictiveModel())
    apps = AppManager(memory)
    tts = TextToSpeech()
    return memory, apps, tts


# -------------------------------------------------
# 2.  Main thread – old GUI mode
# -------------------------------------------------
async def main():
    logger.info("Starting Jarvis – uncensored local edition (old GUI mode)")
    memory, apps, tts = start_components()

    # create GUI (blocking)
    gui = AssistantGUI(input_queue=queue.Queue())
    processor = CommandProcessor(
        gui=gui,
        app_manager=apps,
        memory_manager=memory,
        tts_engine=tts,
        predictor=PredictiveModel(),
    )
    processor.set_event_loop(asyncio.new_event_loop())

    # start wake-word detector
    detector = WakeWordDetector(input_queue=gui.input_queue, tts_engine=tts)
    detector.start()

    # system tray
    tray = SystemTray(
        on_show=lambda: None,
        on_hide=lambda: None,
        on_voice=lambda: gui.input_queue.put(("WAKE_WORD_DETECTED", "manual")),
        on_settings=lambda: None,
        on_exit=lambda: gui.on_close(),
    )
    tray.start()

    # block on GUI mainloop
    gui.run()


if __name__ == "__main__":
    main()
