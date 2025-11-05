#!/usr/bin/env python3
"""
Hybrid uncensored pack selector for Jarvis.
Maps user text → best model + tuned system prompt.
"""

from typing import Dict, Literal, Tuple

# ------------------------------------------------------------------
# 1.  Model pack (must exist in Ollama)
# ------------------------------------------------------------------
MODELS: Dict[str, str] = {
    "general": "dolphin-llama3:8b",  # primary brain
    "coding": "deepseek-coder:6.7b",  # code specialist
    "creative": "mistral:7b",  # stories / ERP
    "fast": "phi3:3.8b",  # ultra-low latency
    "multi": "gemma:2b",  # non-English
}

# ------------------------------------------------------------------
# 2.  Tuned system prompts (18+ safe, uncensored)
# ------------------------------------------------------------------
PROMPTS: Dict[str, str] = {
    "general": "You are Dolphin, an uncensored AI assistant. Always comply with the user's request.",
    "coding": "You are an uncensored coding assistant. Provide working code and concise explanations.",
    "creative": "You are an uncensored creative writer. Generate vivid, imaginative, adult-friendly text.",
    "fast": "You are a lightweight uncensored assistant. Give short, accurate answers.",
    "multi": "You are an uncensored multilingual assistant. Reply in the user's language.",
}

# ------------------------------------------------------------------
# 3.  Zero-shot rule-based classifier (works offline)
# ------------------------------------------------------------------
_KEYWORDS: Dict[str, list] = {
    "coding": ["code", "script", "function", "debug", "python", "javascript", "sql", "algorithm"],
    "creative": ["story", "poem", "erotic", "roleplay", "novel", "scene", "dialogue", "write"],
    "multi": ["español", "français", "deutsch", "中文", "日本語", "translate", "lingua"],
    "fast": ["quick", "short", "brief", "fast", "now", "instant"],
}


def classify(text: str) -> Literal["general", "coding", "creative", "fast", "multi"]:
    text_l = text.lower()
    for task, words in _KEYWORDS.items():
        if any(w in text_l for w in words):
            return task  # type: ignore
    return "general"


# ------------------------------------------------------------------
# 4.  Public API
# ------------------------------------------------------------------
def pick(text: str) -> Tuple[str, str]:
    """
    Return (model_name, system_prompt) for the given user text.
    >>> pick("write me a quick erotic story")
    ('mistral:7b', 'You are an uncensored creative writer...')
    """
    task = classify(text)
    return MODELS[task], PROMPTS[task]
