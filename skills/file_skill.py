"""
skills/file_skill.py
──────────────────────────────────────────────
File management and summarization skill for Jarvis.
Supports read, write, search, summarize, and delete operations.
"""

from jarvis_skills import BaseSkill
import os
import aiofiles
import asyncio
import glob
import re

class Skill(BaseSkill):
    name = "file"
    keywords = ["file", "open", "read", "delete", "remove", "summarize", "search", "show", "text"]

    async def handle(self, text, jarvis):
        text = text.lower().strip()

        # Infer intent
        if "delete" in text or "remove" in text:
            return await self._delete_file(text)
        if "search" in text:
            return await self._search_in_files(text)
        if "summarize" in text:
            return await self._summarize_file(text, jarvis)
        if "open" in text or "read" in text or "show" in text:
            return await self._read_file(text)

        return "Please specify an action like 'open', 'summarize', or 'delete'."

    # ───────────────────────────────────────────────
    # Helpers
    # ───────────────────────────────────────────────

    async def _read_file(self, text: str) -> str:
        """Reads the contents of a file."""
        file_path = self._extract_filename(text)
        if not file_path:
            return "Please specify which file to open."

        abs_path = self._resolve_path(file_path)
        if not abs_path or not os.path.exists(abs_path):
            return f"File '{file_path}' not found."

        try:
            async with aiofiles.open(abs_path, "r", encoding="utf-8") as f:
                content = await f.read()
            # Limit preview for large files
            preview = content[:800]
            if len(content) > 800:
                preview += "\n...[content truncated]"
            return f"📄 Content of {os.path.basename(abs_path)}:\n\n{preview}"
        except Exception as e:
            return f"Error reading file: {e}"

    async def _summarize_file(self, text: str, jarvis) -> str:
        """Summarizes a file using the local model."""
        file_path = self._extract_filename(text)
        if not file_path:
            return "Please specify which file to summarize."

        abs_path = self._resolve_path(file_path)
        if not abs_path or not os.path.exists(abs_path):
            return f"File '{file_path}' not found."

        try:
            async with aiofiles.open(abs_path, "r", encoding="utf-8") as f:
                content = await f.read()
            # Trim very long files for summary
            snippet = content[:3000]
            prompt = f"Summarize this document in a few concise sentences:\n\n{snippet}"
            result = await jarvis.core.process_query(prompt, speak=False)
            return f"📘 Summary of {os.path.basename(abs_path)}:\n{result}"
        except Exception as e:
            return f"Error summarizing file: {e}"

    async def _delete_file(self, text: str) -> str:
        """Deletes a file safely."""
        file_path = self._extract_filename(text)
        if not file_path:
            return "Please specify which file to delete."

        abs_path = self._resolve_path(file_path)
        if not abs_path or not os.path.exists(abs_path):
            return f"File '{file_path}' not found."

        try:
            os.remove(abs_path)
            return f"🗑️ File '{os.path.basename(abs_path)}' deleted successfully."
        except Exception as e:
            return f"Failed to delete file: {e}"

    async def _search_in_files(self, text: str) -> str:
        """Searches all text files in the current directory for a term."""
        match = re.search(r"search\s+(?:for\s+)?['\"]?([\w\s]+)['\"]?", text)
        if not match:
            return "Please specify what to search for."
        term = match.group(1).strip().lower()

        found = []
        for file in glob.glob("*.txt"):
            try:
                async with aiofiles.open(file, "r", encoding="utf-8") as f:
                    content = (await f.read()).lower()
                    if term in content:
                        found.append(file)
            except Exception:
                continue

        if not found:
            return f"No files contain the term '{term}'."
        return f"🔍 Term '{term}' found in: {', '.join(found)}"

    # ───────────────────────────────────────────────
    # Utility
    # ───────────────────────────────────────────────

    def _extract_filename(self, text: str) -> str | None:
        """Extract a file name from text like 'open report.txt'."""
        match = re.search(r"(\w+\.(txt|docx|md|csv|json))", text)
        return match.group(1) if match else None

    def _resolve_path(self, filename: str) -> str | None:
        """Search for the file in current or Documents folder."""
        # Try current directory
        if os.path.exists(filename):
            return os.path.abspath(filename)

        # Try user Documents
        docs = os.path.join(os.path.expanduser("~"), "Documents")
        candidate = os.path.join(docs, filename)
        if os.path.exists(candidate):
            return candidate

        return None
