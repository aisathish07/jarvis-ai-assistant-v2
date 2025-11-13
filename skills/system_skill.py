import logging
from jarvis_skills import BaseSkill
from jarvis_config import Config
from typing import Any, Optional

logger = logging.getLogger("Jarvis.SystemSkill")

class SystemSkill(BaseSkill):
    name = "system"
    keywords = [
        "enable gaming mode", 
        "disable gaming mode", 
        "turn on gaming mode", 
        "turn off gaming mode"
    ]

    async def handle(self, text: str, jarvis: Any) -> Optional[str]:
        """Handles enabling and disabling of system modes like Gaming Mode."""
        text_lower = text.lower()
        
        if "enable" in text_lower or "on" in text_lower:
            if Config.GAMING_MODE:
                return "Gaming mode is already enabled."
            
            logger.info("Enabling Gaming Mode.")
            Config.GAMING_MODE = True
            if jarvis.turbo:
                await jarvis.turbo.unload_all_models()
            return "Gaming mode has been enabled. All local models are unloaded, and I will now use the Gemini API. Enjoy your game!"

        elif "disable" in text_lower or "off" in text_lower:
            if not Config.GAMING_MODE:
                return "Gaming mode is already disabled."

            logger.info("Disabling Gaming Mode.")
            Config.GAMING_MODE = False
            return "Gaming mode has been disabled. Local models will be loaded on the next query."
            
        return None