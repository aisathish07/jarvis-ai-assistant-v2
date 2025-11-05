import re, subprocess, shutil
from skill_bus import BaseSkill

class AppSkill(BaseSkill):
    intent_regex = re.compile(r"open\s+(.+)", re.I)
    def handle(self, match):
        app = match.group(1).strip()
        if shutil.which(app):
            subprocess.Popen([app], shell=True)
            return f"Opening {app}"
        return f"Sorry, {app} not found"