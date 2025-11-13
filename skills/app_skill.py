import asyncio
import subprocess
import shutil
from jarvis_skills import BaseSkill
from typing import Any, Optional

class Skill(BaseSkill):
    name = "app"
    keywords = ["open", "launch", "start"]

    async def handle(self, text: str, jarvis: Any) -> Optional[str]:
        # Extract app name, e.g., "open notepad" -> "notepad"
        app_name = ""
        text_lower = text.lower()
        for kw in self.keywords:
            if text_lower.startswith(kw):
                app_name = text[len(kw):].strip()
                break
        
        if not app_name:
            return None # Not a command for this skill

        if shutil.which(app_name):
            try:
                # Run the app in a separate process without blocking
                await asyncio.to_thread(subprocess.Popen, [app_name], shell=True)
                return f"Opening {app_name}."
            except Exception as e:
                return f"Sorry, I failed to open {app_name}: {e}"
        else:
            return f"Sorry, I can't find the application '{app_name}'."