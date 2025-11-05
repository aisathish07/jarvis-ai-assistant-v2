import re, os
from skill_bus import BaseSkill
from web_agent_lazy import WebAgentLazy

agent = WebAgentLazy()


class WebSkill(BaseSkill):
    intent_regex = re.compile(r"google\s+(.+)", re.I)
    def handle(self, match):
        if os.getenv("WEB_AGENT_ENABLED", "").lower() != "true":
            return "Web search is disabled (set WEB_AGENT_ENABLED=true)."
        query = match.group(1).strip()
        import asyncio
        results = asyncio.run(agent.search(query))   # was google_search
        if not results:
            return f"No results for '{query}'."
        titles = [r["title"] for r in results[:3]]
        return "Top: " + " | ".join(titles)