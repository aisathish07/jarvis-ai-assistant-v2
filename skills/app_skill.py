from jarvis_skills import BaseSkill
import asyncio

class Skill(BaseSkill):
    name = "app"
    keywords = ["open", "launch", "play", "close"]

    async def handle(self, text, jarvis):
        """Use the integrated AppControl to open or control apps."""
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, jarvis.app_control.parse_command, text)
            return result or "Could not perform app action."
        except Exception as e:
            return f"App skill error: {e}"
