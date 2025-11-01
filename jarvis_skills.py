# jarvis_skills.py - COMPLETE FIXED VERSION
"""
jarvis_skills.py
──────────────────────────────────────────────
Dynamic Skill Loader for Jarvis AI Assistant - FIXED & WORKING
"""

import importlib
import inspect
import logging
import os
import pkgutil
import asyncio
from typing import Dict, Any, List, Optional
from functools import lru_cache

logger = logging.getLogger("Jarvis.Skills")

class BaseSkill:
    """Base class for all skills."""
    name: str = "base"
    keywords: List[str] = []

    async def handle(self, text: str, jarvis: Any) -> Optional[str]:
        """Override in child class"""
        raise NotImplementedError

class SkillManager:
    def __init__(self):
        self.skill_dir = "skills"
        self.skills: Dict[str, BaseSkill] = {}
        self.load_skills()
    
    @lru_cache(maxsize=128)
    def _normalize(self, text: str) -> str:
        return text.lower().strip()

    def load_skills(self):
        """Auto-import all modules in the skills folder"""
        # Create skills directory if it doesn't exist
        if not os.path.exists(self.skill_dir):
            os.makedirs(self.skill_dir)
            logger.warning(f"Created skills directory: {self.skill_dir}")
            return

        logger.info(f"🔍 Loading skills from: {os.path.abspath(self.skill_dir)}")

        for _, module_name, _ in pkgutil.iter_modules([self.skill_dir]):
            full_name = f"skills.{module_name}"
            try:
                module = importlib.import_module(full_name)
                # Find classes subclassing BaseSkill or named Skill
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (name.lower() == "skill" or 
                        (issubclass(obj, BaseSkill) and obj != BaseSkill)):
                        instance = obj()
                        self.skills[instance.name] = instance
                        logger.info(f"✅ Loaded skill: {instance.name}")
            except Exception as e:
                logger.error(f"Failed to load skill {module_name}: {e}")

    async def handle(self, text: str, jarvis: Any) -> Optional[str]:
        """Try each skill based on keywords"""
        text_lower = self._normalize(text)
        
        for skill in self.skills.values():
            if any(kw in text_lower for kw in skill.keywords):
                try:
                    logger.info(f"🧩 Dispatching to skill: {skill.name}")
                    result = await skill.handle(text, jarvis)
                    if result:
                        return result
                except Exception as e:
                    logger.error(f"Skill '{skill.name}' failed: {e}")
        return None

    def get_loaded_skills(self) -> List[str]:
        """Get list of loaded skill names"""
        return list(self.skills.keys())