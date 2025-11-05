import importlib.util
import inspect
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from plugin_watcher import start_watching

logger = logging.getLogger("AI_Assistant.PluginSystem")


class BaseSkill:
    """
    A base class that all skills must inherit from.
    It defines the interface for skills to be discovered and used by the assistant.
    """

    name = "base"

    def register(self, assistant_api: Dict[str, Any]) -> None:
        """
        Called once when the skill is loaded. It receives an API object
        to interact with the main assistant's capabilities.
        """
        self.assistant = assistant_api

    def on_command(self, command_text: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Called when a command is not recognized by the core processor.
        The skill should check if it can handle the command.

        Args:
            command_text: The full text of the user's command.
            context: The assistant's current conversational context.

        Returns:
            A string response if the command is handled, otherwise None.
        """
        return None

    def help(self) -> str:
        """Returns a brief help string for the skill."""
        return f"No specific help available for the '{self.name}' skill."


class PluginManager:
    """Discovers, loads, and manages all available skills for the assistant."""

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.plugins: Dict[str, BaseSkill] = {}

        start_watching(self, str(self.skills_dir))

    def discover_and_load(self, assistant_api: Dict[str, Any]) -> None:
        """
        Scans the skills directory for Python files, imports them,
        and registers any classes that inherit from BaseSkill.
        """
        if not self.skills_dir.exists():
            logger.info(f"Skills directory '{self.skills_dir}' not found. Creating it.")
            self.skills_dir.mkdir()
            return

        for py_file in self.skills_dir.glob("*.py"):
            if py_file.stem == "__init__":
                continue
            try:
                spec = importlib.util.spec_from_file_location(py_file.stem, str(py_file))
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                            instance = obj()
                            instance.register(assistant_api)
                            self.plugins[instance.name] = instance
                            logger.info(f"Successfully loaded skill: '{instance.name}'")
            except Exception as e:
                logger.exception(f"Failed to load plugin from {py_file.name}: {e}")

    def handle_command(self, command_text: str, context: Dict[str, Any]) -> List[str]:
        """
        Passes an unhandled command to all loaded plugins and collects their responses.
        """
        responses = []
        for skill in self.plugins.values():
            try:
                resp = skill.on_command(command_text, context)
                if resp:
                    responses.append(resp)
            except Exception:
                logger.exception(f"Plugin '{skill.name}' failed during on_command.")
        return responses

    def list_skills(self) -> List[str]:
        """Returns a list of the names of all loaded skills."""
        return list(self.plugins.keys())
