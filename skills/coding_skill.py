import logging
from jarvis_skills import BaseSkill
from typing import Any, Optional

logger = logging.getLogger("Jarvis.CodingSkill")

class CodingSkill(BaseSkill):
    name = "coding"
    keywords = ["code", "python", "java", "javascript", "c++", "c#", "php", "ruby", "go", "rust", "swift", "kotlin", "sql", "html", "css", "bash", "shell", "algorithm", "function", "class", "variable", "loop", "debug", "error", "programming"]

    async def handle(self, text: str, jarvis: Any) -> Optional[str]:
        logger.info(f"Handling coding query: {text}")
        full_response = ""
        async for chunk in jarvis.turbo.query_with_turbo(prompt=text, system="You are a coding assistant. Provide code snippets and explanations.", stream=True):
            full_response += chunk.get('message', {}).get('content', '')
        return full_response
