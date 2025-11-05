import os, importlib, logging, pathlib, typing as t
logger = logging.getLogger("jarvis.web")
logging.basicConfig(level=logging.DEBUG)
import pathlib, importlib.util, os, logging
logger = logging.getLogger("jarvis.web")

def _load(self):
    if self._real is None and os.getenv("WEB_AGENT_ENABLED", "").lower() == "true":
        try:
            web_path = pathlib.Path(__file__).with_name("../attic/web_agent.py").resolve()
            spec = importlib.util.spec_from_file_location("web_agent", web_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self._real = mod.WebAgent()
            logger.info("Web agent lazy-loaded")
        except Exception as e:
            logger.exception("Web agent disabled")   # full traceback
    return self._real

class WebAgentLazy:
    """Loads real WebAgent only when first used."""
    def __init__(self) -> None:
        self._real = None

    def _load(self):
        if self._real is None and os.getenv("WEB_AGENT_ENABLED", "").lower() == "true":
            try:
                spec = importlib.util.spec_from_file_location("web_agent", pathlib.Path("attic/web_agent.py"))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                self._real = mod.WebAgent()
                logger.info("Web agent lazy-loaded")
            except Exception as e:
                logger.warning("Web agent disabled: %s", e)
        return self._real
    async def search(self, query: str, num: int = 5) -> list[dict]:
        """Default to DuckDuckGo."""
        agent = self._load()
        return await agent.search(query, num) if agent else []
    async def google_search(self, query: str, num: int = 3) -> list[dict]:
        agent = self._load()
        return await agent.google_search(query, num) if agent else []

    async def take_screenshot(self, url: str) -> str | None:
        agent = self._load()
        return await agent.take_screenshot(url) if agent else None
    async def close(self):
        """Pass-through to real agent if it exists."""
        if self._real:
            await self._real.close()