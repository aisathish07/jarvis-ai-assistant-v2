# skills/web_automation_skill.py - Web automation skill for MY-Assistant (improved)
import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.append(str(Path(__file__).parent.parent))
from attic.plugin_system import BaseSkill

logger = logging.getLogger("AI_Assistant.WebAutomationSkill")


class WebAutomationSkill(BaseSkill):
    """
    Web automation skill using a lazy-loaded WebAgent.
    This version:
    - returns immediate placeholders for long tasks,
    - schedules coroutines on the assistant event loop,
    - calls self.assistant['on_async_result'] (if provided) when a task completes.
    - provides a shutdown hook to release resources.
    """

    name = "web_automation"

    def __init__(self):
        super().__init__()
        self.agent = None
        self._agent_initialized = False

    async def _get_agent(self):
        """Lazy load web agent only when needed."""
        if not self._agent_initialized:
            try:
                from attic.web_agent import WebAgent

                self.agent = WebAgent()
                self._agent_initialized = True
                logger.info("Web agent loaded successfully")
            except Exception as e:
                logger.exception("Failed to load web agent: %s", e)
                return None
        return self.agent

    def on_command(self, command_text: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Handle web automation commands. Long-running tasks are scheduled and return a placeholder.
        """
        cmd = command_text.lower()

        # Amazon search
        m = re.search(r"(?:search amazon for|find on amazon)\s+(.+)", cmd, re.I)
        if m:
            query = m.group(1).strip()
            return self._schedule_async(self._amazon_search(query))

        # Google search
        m = re.search(r"(?:google search|search google for|look up)\s+(.+)", cmd, re.I)
        if m:
            query = m.group(1).strip()
            return self._schedule_async(self._google_search(query))

        # Screenshot
        m = re.search(r"(?:screenshot of|capture webpage)\s+(.+)", cmd, re.I)
        if m:
            url = m.group(1).strip()
            if not url.startswith("http"):
                url = "https://" + url
            return self._schedule_async(self._take_screenshot(url))

        # Navigate
        m = re.search(r"(?:open website|go to|navigate to)\s+(.+)", cmd, re.I)
        if m:
            url = m.group(1).strip()
            if not url.startswith("http"):
                url = "https://" + url
            return self._schedule_async(self._navigate(url))

        # Stats
        if "web agent stats" in cmd or "browser stats" in cmd:
            return self._schedule_async(self._get_stats())

        # Mode switching
        if "web agent" in cmd and "mode" in cmd:
            if "lightweight" in cmd:
                return self._schedule_async(self._set_mode("lightweight"))
            elif "balanced" in cmd:
                return self._schedule_async(self._set_mode("balanced"))
            elif "full" in cmd:
                return self._schedule_async(self._set_mode("full"))

        return None

    def _schedule_async(self, coro):
        """
        Schedule coroutine to run and send results to assistant via on_async_result callback if present.
        Returns an immediate placeholder string.
        """
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return asyncio.run(coro)

        async def runner():
            try:
                result = await coro
            except Exception as e:
                logger.exception("Web automation task failed: %s", e)
                result = f"Error: {e}"
            # deliver result to assistant callback if available
            cb = None
            try:
                cb = getattr(self, "assistant", {}).get("on_async_result")
            except Exception:
                cb = None
            if callable(cb):
                try:
                    await asyncio.to_thread(cb, result)
                except Exception:
                    logger.exception("on_async_result delivery failed")
            else:
                logger.debug("No on_async_result callback; web task result: %s", result)

        if loop.is_running():
            loop.create_task(runner())
            return "Processing your web request..."
        else:
            return asyncio.run(coro)

    # --------------- async task implementations ---------------
    async def _amazon_search(self, query: str) -> str:
        agent = await self._get_agent()
        if not agent:
            return "Web agent is not available."
        try:
            result = await agent.search_amazon(query)
            if "error" in result:
                return f"Sorry, I couldn't search Amazon: {result['error']}"
            products = result.get("products", [])
            if not products:
                return f"I couldn't find any products for '{query}' on Amazon."
            response_lines = [f"I found {len(products)} products on Amazon for '{query}':"]
            for i, product in enumerate(products, 1):
                response_lines.append(
                    f"{i}. {product.get('title', '<no title>')}\n   Price: {product.get('price', 'N/A')}"
                )
            return "\n\n".join(response_lines)
        except Exception as e:
            logger.exception("Amazon search error: %s", e)
            return f"Amazon search failed: {e.__class__.__name__}"

    async def _google_search(self, query: str) -> str:
        agent = await self._get_agent()
        if not agent:
            return "Web agent is not available."
        try:
            results = await agent.google_search(query, num_results=5)
            if not results:
                return f"I couldn't find any results for '{query}'."
            lines = [f"Top results for '{query}':"]
            for i, r in enumerate(results, 1):
                title = r.get("title", "<no title>")
                url = r.get("url", "")
                snippet = (r.get("snippet") or "")[:140]
                lines.append(f"{i}. {title}\n   {url}\n   {snippet}...")
            return "\n\n".join(lines)
        except Exception as e:
            logger.exception("Google search error: %s", e)
            return f"Google search failed: {e.__class__.__name__}"

    async def _take_screenshot(self, url: str) -> str:
        agent = await self._get_agent()
        if not agent:
            return "Web agent is not available."
        try:
            path = await agent.take_screenshot(url)
            return f"Screenshot saved as {path}" if path else "Failed to take screenshot."
        except Exception as e:
            logger.exception("Screenshot error: %s", e)
            return f"Screenshot failed: {e.__class__.__name__}"

    async def _navigate(self, url: str) -> str:
        agent = await self._get_agent()
        if not agent:
            return "Web agent is not available."
        try:
            page = await agent.navigate(url)
            if page:
                title = await page.title()
                await page.close()
                return f"Opened {title} at {url}"
            return f"Failed to open {url}"
        except Exception as e:
            logger.exception("Navigation error: %s", e)
            return f"Navigation failed: {e.__class__.__name__}"

    async def _get_stats(self) -> str:
        agent = await self._get_agent()
        if not agent:
            return "Web agent is not available."
        try:
            stats = agent.get_stats()
            return (
                f"Web Agent: Mode={stats.get('mode', '?').upper()}, "
                f"Status={'Active' if stats.get('initialized') else 'Idle'}, "
                f"ActiveTasks={stats.get('active_tasks', 0)}, "
                f"MemMB={stats.get('memory_current_mb', 0)}, RAM_GB={stats.get('ram_total_gb', '?')}"
            )
        except Exception as e:
            logger.exception("Stats error: %s", e)
            return f"Stats retrieval failed: {e.__class__.__name__}"

    async def _set_mode(self, mode: str) -> str:
        agent = await self._get_agent()
        if not agent:
            return "Web agent is not available."
        try:
            success = await agent.upgrade_mode(mode)
            return (
                f"Web agent switched to {mode.upper()} mode."
                if success
                else f"Cannot switch to {mode} mode."
            )
        except Exception as e:
            logger.exception("Mode switch error: %s", e)
            return f"Mode switch failed: {e.__class__.__name__}"

    # cleanup for graceful shutdown
    async def shutdown(self):
        if self._agent_initialized and self.agent:
            try:
                await self.agent.close()
                self.agent = None
                self._agent_initialized = False
                logger.info("Web agent shut down")
            except Exception:
                logger.exception("Error shutting down web agent")

    def help(self) -> str:
        return """
Web Automation Skill - Commands:
• "search amazon for [product]"
• "google search [query]"
• "screenshot of [url]"
• "open website [url]"
• "web agent stats"
"""
