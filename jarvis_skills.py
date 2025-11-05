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
    config: Dict[str, Any] = {}

    async def handle(self, text: str, jarvis: Any) -> Optional[str]:
        """Override in child class"""
        raise NotImplementedError

import pickle

class SkillManager:
    def __init__(self, config_manager=None):
        self.skill_dir = "skills"
        self.skills: Dict[str, BaseSkill] = {}
        self.config_manager = config_manager
        self.intent_model = None
        self.load_skills()
        self.load_intent_model()

    def load_intent_model(self):
        """Load the trained intent recognition model."""
        try:
            with open('intent_model.pkl', 'rb') as f:
                self.intent_model = pickle.load(f)
            logger.info("✅ Intent recognition model loaded.")
        except FileNotFoundError:
            logger.warning("Intent model not found. Falling back to keyword matching.")
        except Exception as e:
            logger.error(f"Failed to load intent model: {e}")
    
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
                        # Pass config to skill
                        if self.config_manager and instance.name in self.config_manager.config.skills:
                            instance.config = self.config_manager.config.skills[instance.name]
                        self.skills[instance.name] = instance
                        logger.info(f"✅ Loaded skill: {instance.name}")
            except Exception as e:
                logger.error(f"Failed to load skill {module_name}: {e}")

    async def handle(self, text: str, jarvis: Any) -> Optional[str]:
        """Try each skill based on keywords"""
        text_lower = self._normalize(text)

        # Intent recognition
        if self.intent_model:
            predicted_intent = self.intent_model.predict([text_lower])[0]
            if predicted_intent in self.skills:
                skill = self.skills[predicted_intent]
                try:
                    logger.info(f"🧠 Dispatching to skill via intent: {skill.name}")
                    return await skill.handle(text, jarvis)
                except Exception as e:
                    logger.error(f"Skill '{skill.name}' failed: {e}")

        # Fallback to keyword matching
        for skill in self.skills.values():
            if any(kw in text_lower for kw in skill.keywords):
                try:
                    logger.info(f"🧩 Dispatching to skill via keyword: {skill.name}")
                    result = await skill.handle(text, jarvis)
                    if result:
                        return result
                except Exception as e:
                    logger.error(f"Skill '{skill.name}' failed: {e}")
        return None

    def get_loaded_skills(self) -> List[str]:
        """Get list of loaded skill names"""
        return list(self.skills.keys())