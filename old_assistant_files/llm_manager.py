#!/usr/bin/env python3
"""
Local-only LLM router for Jarvis.
Routes every prompt → Ollama + uncensored hybrid pack.
No cloud APIs, no keys, no refusals.
"""

import logging
from typing import Callable, Optional

import aiohttp

from model_selector import pick  # our tiny router

logger = logging.getLogger("AI_Assistant.LLM")

# ------------------------------------------------------------------
#  Configuration – edit here if you add more local models
# ------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_TEMP = 0.7
MAX_TOKENS = 2048
TIMEOUT_SEC = 60


# ------------------------------------------------------------------
#  Public API – identical signature to old cloud router
# ------------------------------------------------------------------
async def get_llm_response(
    prompt: str,
    provider: str = "local",  # kept for compatibility; ignored
    status_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Send prompt to the best *local* uncensored model and return text.
    Cloud-free, key-free, refusal-free.
    """
    if status_callback:
        status_callback("llm_local_start")

    model, system = pick(prompt)  # 1. pick model + 18+ system prompt
    full_prompt = f"{system}\n\nUser: {prompt}\nAssistant:"

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": DEFAULT_TEMP,
            "num_predict": MAX_TOKENS,
        },
    }

    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TIMEOUT_SEC)
        ) as session:
            async with session.post(OLLAMA_URL, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                reply = data.get("response", "").strip()
                if not reply:
                    return "Local model returned empty."
                if status_callback:
                    status_callback("llm_local_end")
                return reply

    except Exception as e:
        logger.error("Local LLM failed: %s", e)
        if status_callback:
            status_callback("llm_local_error")
        return f"Local model error: {e}"


# ------------------------------------------------------------------
#  Session cleanup (kept for compat)
# ------------------------------------------------------------------
async def close_sessions() -> None:
    # no persistent sessions → nothing to close
    pass
