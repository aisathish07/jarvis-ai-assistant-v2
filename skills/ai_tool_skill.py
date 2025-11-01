"""
skills/ai_tool_skill.py
──────────────────────────────────────────────
AI Tool Skill for Jarvis
Leverages local Ollama models for summarization, translation,
rewriting, and text enhancement — fully offline.
"""

from jarvis_skills import BaseSkill
import re
import asyncio

class Skill(BaseSkill):
    name = "ai_tools"
    keywords = [
        "summarize", "translate", "rewrite", "explain", "analyze",
        "shorten", "expand", "simplify", "improve", "grammar", "spell"
    ]

    async def handle(self, text, jarvis):
        text = text.lower().strip()

        # Determine operation
        if "summarize" in text:
            return await self._summarize(text, jarvis)
        elif "translate" in text:
            return await self._translate(text, jarvis)
        elif "rewrite" in text or "rephrase" in text:
            return await self._rewrite(text, jarvis)
        elif "explain" in text or "analyze" in text or "simplify" in text:
            return await self._explain(text, jarvis)
        elif "shorten" in text or "expand" in text:
            return await self._resize(text, jarvis)
        elif "grammar" in text or "spell" in text or "improve" in text:
            return await self._grammar(text, jarvis)

        return "Please specify what you’d like me to do — summarize, translate, or rewrite something."

    # ───────────────────────────────────────────────
    # Skill Actions
    # ───────────────────────────────────────────────

    async def _summarize(self, text, jarvis):
        content = self._extract_text(text)
        if not content:
            return "Please provide text to summarize."
        prompt = f"Summarize the following text clearly and concisely:\n\n{content}"
        result = await jarvis.core.process_query(prompt, speak=False)
        return f"🧾 Summary:\n{result}"

    async def _translate(self, text, jarvis):
        match = re.search(r"translate (.+?) (?:to|into) (\w+)", text)
        if match:
            content, lang = match.groups()
        else:
            content, lang = self._extract_text(text), "english"
        if not content:
            return "Please specify what to translate."
        prompt = f"Translate the following text into {lang}:\n\n{content}"
        result = await jarvis.core.process_query(prompt, speak=False)
        return f"🌐 Translation to {lang.capitalize()}:\n{result}"

    async def _rewrite(self, text, jarvis):
        content = self._extract_text(text)
        if not content:
            return "Please provide text to rewrite."
        prompt = f"Rewrite the following text in a more fluent and natural way:\n\n{content}"
        result = await jarvis.core.process_query(prompt, speak=False)
        return f"✍️ Rewritten Text:\n{result}"

    async def _explain(self, text, jarvis):
        content = self._extract_text(text)
        if not content:
            return "Please specify what you’d like me to explain."
        prompt = f"Explain the following concept in simple terms:\n\n{content}"
        result = await jarvis.core.process_query(prompt, speak=False)
        return f"💡 Explanation:\n{result}"

    async def _resize(self, text, jarvis):
        content = self._extract_text(text)
        if not content:
            return "Please provide text to shorten or expand."
        if "shorten" in text:
            prompt = f"Make this text shorter and more concise:\n\n{content}"
        else:
            prompt = f"Expand this text with more detail:\n\n{content}"
        result = await jarvis.core.process_query(prompt, speak=False)
        return f"📏 Adjusted Text:\n{result}"

    async def _grammar(self, text, jarvis):
        content = self._extract_text(text)
        if not content:
            return "Please provide text to correct or improve."
        prompt = f"Correct grammar and spelling, and improve clarity for this text:\n\n{content}"
        result = await jarvis.core.process_query(prompt, speak=False)
        return f"✅ Improved Version:\n{result}"

    # ───────────────────────────────────────────────
    # Utility
    # ───────────────────────────────────────────────

    def _extract_text(self, text: str) -> str | None:
        """Extracts quoted or following text content."""
        match = re.search(r"(?:summarize|translate|rewrite|explain|shorten|expand|improve|analyze|simplify)\s+['\"]?(.+?)['\"]?$", text)
        if match:
            return match.group(1).strip()
        return None
