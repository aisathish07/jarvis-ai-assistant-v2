import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from attic.predictive_model import PredictiveModel
from config import Config

logger = logging.getLogger("AI_Assistant.Memory")


class MemoryManager:
    """Handles the SQLite database for storing app paths, commands, and chat history."""

    def __init__(self, predictor: Optional[PredictiveModel] = None, retrain_threshold: int = 10):
        self.db_path = Config.DB_FILE
        self.init_database()
        self.predictor = predictor
        self.retrain_threshold = retrain_threshold
        self.command_count_since_last_train = 0

    def init_database(self) -> None:
        """Initialize database schema with error handling."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS apps (
                        name TEXT UNIQUE PRIMARY KEY, path TEXT, 
                        usage_count INTEGER DEFAULT 0, last_used TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS commands (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, command_text TEXT, 
                        response_text TEXT, success BOOLEAN, 
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL,
                        content TEXT NOT NULL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_profile (
                        key TEXT UNIQUE PRIMARY KEY, value TEXT NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT NOT NULL,
                        run_time TIMESTAMP NOT NULL, is_active BOOLEAN DEFAULT 1
                    )
                """)
                conn.commit()
                logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error("Failed to initialize database: %s", e)
            raise

    # --- App Management ---
    def add_app(self, name: str, path: str) -> None:
        """Add or update an app entry (FIXED: with validation)."""
        if not name or not path:
            logger.warning("Cannot add app: name or path is empty")
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO apps (name, path, usage_count, last_used) VALUES (?, ?, COALESCE((SELECT usage_count FROM apps WHERE name = ?), 0), ?)",
                    (name.lower(), str(path), name.lower(), datetime.now()),
                )
                conn.commit()
        except Exception as e:
            logger.error("Error adding app '%s': %s", name, e)

    def update_app_usage(self, name: str) -> None:
        """Update app usage statistics."""
        if not name:
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE apps SET usage_count = usage_count + 1, last_used = ? WHERE name = ?",
                    (datetime.now(), name.lower()),
                )
                conn.commit()
        except Exception as e:
            logger.error("Error updating app usage for '%s': %s", name, e)

    def get_all_apps(self) -> Dict[str, str]:
        """Retrieves all stored application paths from the database (FIXED: with error handling)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, path FROM apps")
                return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            logger.error("Error retrieving apps: %s", e)
            return {}

    # --- Preference Management ---
    def set_user_preference(self, key: str, value: str) -> None:
        """Set user preference with validation."""
        if not key:
            logger.warning("Cannot set preference: key is empty")
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO user_profile (key, value) VALUES (?, ?)",
                    (key.lower(), str(value) if value else ""),
                )
                conn.commit()
        except Exception as e:
            logger.error("Error setting preference '%s': %s", key, e)

    def get_user_preference(self, key: str) -> Optional[str]:
        """Get user preference with error handling."""
        if not key:
            return None

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM user_profile WHERE key = ?", (key.lower(),))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error("Error getting preference '%s': %s", key, e)
            return None

    # --- Chat History & Command Logging ---
    def log_command(self, command: str, response: str, success: bool = True) -> None:
        """Log command execution (FIXED: with transaction handling)."""
        if not command:
            logger.warning("Cannot log empty command")
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO commands (command_text, response_text, success) VALUES (?, ?, ?)",
                    (str(command), str(response) if response else "", int(success)),
                )
                conn.commit()
                logger.debug("Command logged: %s", command[:50])
        except Exception as e:
            logger.error("Error logging command: %s", e)
            return

        self.command_count_since_last_train += 1
        if self.predictor and self.command_count_since_last_train >= self.retrain_threshold:
            dataset = self.export_training_data()
            try:
                if self.predictor.train(dataset):
                    logger.info("Predictive model auto-retrained with latest history.")
                    self.command_count_since_last_train = 0
            except Exception as e:
                logger.error("Error auto-retraining predictor: %s", e)

    # --- Reminder Management ---
    def add_reminder(self, text: str, run_time: datetime) -> int:
        """Add a reminder (FIXED: with validation)."""
        if not text or not run_time:
            logger.warning("Cannot add reminder: text or run_time is missing")
            return -1

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO reminders (text, run_time) VALUES (?, ?)",
                    (str(text), run_time.isoformat()),
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error("Error adding reminder: %s", e)
            return -1

    def mark_reminder_as_complete(self, reminder_id: int) -> None:
        """Mark reminder as inactive."""
        if reminder_id <= 0:
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE reminders SET is_active = 0 WHERE id = ?", (reminder_id,))
                conn.commit()
        except Exception as e:
            logger.error("Error marking reminder %d as complete: %s", reminder_id, e)

    def get_reminders(
        self, only_active: bool = True, time_window_hours: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get reminders with optional filtering (FIXED: with error handling)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                params = []
                query = "SELECT * FROM reminders"
                conditions = []

                if only_active:
                    conditions.append("is_active = 1 AND run_time > ?")
                    params.append(datetime.now().isoformat())

                if time_window_hours:
                    cutoff_time = datetime.now() + timedelta(hours=time_window_hours)
                    conditions.append("run_time <= ?")
                    params.append(cutoff_time.isoformat())

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY run_time ASC"
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error retrieving reminders: %s", e)
            return []

    # --- Analytical Methods for ML ---
    def get_frequent_commands(self, top_n: int = 3) -> List[tuple]:
        """Get most frequently executed commands (FIXED: with error handling)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT command_text, COUNT(command_text) as count FROM commands
                    WHERE success = 1 AND command_text NOT IN ('hi', 'hello', 'hey')
                    GROUP BY command_text ORDER BY count DESC LIMIT ?
                """,
                    (top_n,),
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error("Error getting frequent commands: %s", e)
            return []

    def export_training_data(self) -> List[Dict[str, Any]]:
        """Exports command history for ML training (FIXED: with robust error handling)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT timestamp, command_text, success FROM commands")
                dataset = []

                for ts_str, cmd, success in cursor.fetchall():
                    try:
                        # Handle both ISO format and other formats
                        if ts_str:
                            try:
                                ts = datetime.fromisoformat(ts_str)
                            except (ValueError, TypeError):
                                # Try parsing as string if fromisoformat fails
                                ts = datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S")

                            if cmd:  # Only add if command is not empty
                                dataset.append(
                                    {
                                        "hour": ts.hour,
                                        "day_of_week": ts.weekday(),
                                        "command": str(cmd),
                                        "success": int(success) if success is not None else 0,
                                    }
                                )
                    except Exception as e:
                        logger.debug("Skipped malformed record: %s", e)
                        continue

                logger.info("Exported %d training samples.", len(dataset))
                return dataset
        except Exception as e:
            logger.error("Error exporting training data: %s", e)
            return []
