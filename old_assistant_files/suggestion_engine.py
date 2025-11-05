import logging
from datetime import datetime
from typing import List

from attic.predictive_model import PredictiveModel
from memory_manager import MemoryManager

logger = logging.getLogger("AI_Assistant.SuggestionEngine")


class SuggestionEngine:
    """Generates proactive suggestions using a hybrid of ML and rule-based logic."""

    def __init__(self, memory_manager: MemoryManager, predictor: PredictiveModel):
        self.memory_manager = memory_manager
        self.predictor = predictor
        # Initial training on startup
        logger.info("Performing initial training of predictive model...")
        self.predictor.train(self.memory_manager.export_training_data())

    async def generate_suggestions(self) -> List[str]:
        """Generates proactive context-aware suggestions."""
        suggestions = []
        now = datetime.now()

        # Predictive model suggestion
        predicted = self.predictor.predict(now.hour, now.weekday())
        if predicted:
            suggestions.append(f"Should I run '{predicted}'?")

        # Frequent commands
        frequent = self.memory_manager.get_frequent_commands(3)
        if frequent:
            suggestions.append(f"You often run '{frequent[0][0]}'. Should I do that?")

        # Time-based suggestions
        if 8 <= now.hour < 10:
            suggestions.append("Morning! Check weather or open development tools?")
        elif 12 <= now.hour < 13:
            suggestions.append("Lunch break? Close work apps and relax?")
        elif 17 <= now.hour < 18:
            suggestions.append("Wrap up the day? Close all apps?")

        # Reminders
        reminders = self.memory_manager.get_reminders(time_window_hours=1)
        for r in reminders:
            suggestions.append(f"Reminder: {r['text']}")

        return suggestions[:3]
