# skills/test_skill.py
"""
Test skill to verify system connectivity
"""

from jarvis_skills import BaseSkill

class Skill(BaseSkill):
    name = "test"
    keywords = ["test", "ping", "status", "hello"]

    async def handle(self, text, jarvis):
        text = text.lower().strip()
        
        if "ping" in text:
            return "🏓 Pong! System is connected and working."
        
        if "status" in text:
            status = jarvis.get_status()
            return f"✅ System Status: {status['skills_loaded']} skills loaded, {status['total_queries']} queries processed"
        
        if "hello" in text or "test" in text:
            return "👋 Hello! The skill system is working perfectly. I can help you with apps, files, weather, and more!"
        
        return "Test skill activated. Use 'ping', 'status', or 'hello' to test."