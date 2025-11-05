import logging
from typing import Any, Dict, List, Optional

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

logger = logging.getLogger("AI_Assistant.PredictiveModel")


class PredictiveModel:
    """A simple ML model to predict user commands based on time."""

    def __init__(self):
        self.pipeline = make_pipeline(
            CountVectorizer(), LogisticRegression(max_iter=200, solver="liblinear")
        )
        self.is_trained = False

    def train(self, dataset: List[Dict[str, Any]]) -> bool:
        """Trains the model on the user's command history."""
        # The model needs at least two different commands to learn a pattern.
        if not dataset or len(set(d["command"] for d in dataset)) < 2:
            self.is_trained = False
            return False

        # Create feature strings from time and day, e.g., "hour_14 day_3"
        X = [f"hour_{d['hour']} day_{d['day_of_week']}" for d in dataset]
        y = [d["command"] for d in dataset]

        try:
            self.pipeline.fit(X, y)
            self.is_trained = True
            logger.info("Predictive model trained successfully on %d samples.", len(dataset))
            return True
        except Exception as e:
            logger.error(f"Failed to train predictive model: {e}")
            self.is_trained = False
            return False

    def predict(self, hour: int, day_of_week: int) -> Optional[str]:
        """Predicts the most likely command for a given time."""
        if not self.is_trained:
            return None

        try:
            X_new = [f"hour_{hour} day_{day_of_week}"]
            prediction = self.pipeline.predict(X_new)
            return prediction[0]
        except Exception as e:
            logger.error(f"Failed to predict next command: {e}")
            return None
