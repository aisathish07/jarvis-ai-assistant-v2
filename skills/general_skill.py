import logging
from jarvis_skills import BaseSkill
from typing import Any, Optional

logger = logging.getLogger("Jarvis.GeneralSkill")

class GeneralSkill(BaseSkill):
    name = "general"
    keywords = ["tell me about", "what is", "who is", "where is", "when is", "how is"]

    async def handle(self, text: str, jarvis: Any) -> Optional[str]:
        logger.info(f"Handling general query: {text}")
        # Use the core AI to answer general questions
        response = await jarvis.process_query(text, speak=False, stream=False)
        return response
