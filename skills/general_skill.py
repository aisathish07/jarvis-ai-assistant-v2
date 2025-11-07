import logging
from jarvis_skills import BaseSkill
from typing import Any, Optional

logger = logging.getLogger("Jarvis.GeneralSkill")

class GeneralSkill(BaseSkill):
    name = "general"
    keywords = ["tell me about", "what is", "who is", "where is", "when is", "how is"]

    async def handle(self, text: str, jarvis: Any) -> Optional[str]:
        logger.info(f"Handling general query: {text}")
        full_response = ""
        async for chunk in jarvis.turbo.query_with_turbo(prompt=text, system=jarvis.personality.get_system_prompt(), stream=True):
            full_response += chunk.get('message', {}).get('content', '')
        return full_response
