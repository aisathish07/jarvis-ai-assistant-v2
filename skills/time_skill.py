import re, datetime
from skill_bus import BaseSkill

class TimeSkill(BaseSkill):
    intent_regex = re.compile(r"\btime\b", re.I)
    def handle(self, match):
        return datetime.datetime.now().strftime("%H:%M")