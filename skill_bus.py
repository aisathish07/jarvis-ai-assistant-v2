import importlib.util, inspect, pathlib, logging
logger = logging.getLogger("jarvis.skill_bus")

class BaseSkill:
    """All skills inherit from this."""
    intent_regex: str = ""          # regex that triggers this skill
    def handle(self, text: str) -> str | None:
        return None

def load_skills(skills_dir: pathlib.Path):
    """Return dict {regex: skill_instance}"""
    skills = {}
    for py in skills_dir.glob("*.py"):
        if py.name.startswith("_"): continue
        spec = importlib.util.spec_from_file_location(py.stem, py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for _, cls in inspect.getmembers(mod, inspect.isclass):
            if issubclass(cls, BaseSkill) and cls is not BaseSkill:
                inst = cls()
                skills[inst.intent_regex] = inst
                logger.info("Loaded skill: %s", cls.__name__)
    return skills

def dispatch(text: str, skills: dict[str, BaseSkill]) -> str | None:
    for regex, skill in skills.items():
        if (m := regex.search(text)):
            return skill.handle(m)
    return None