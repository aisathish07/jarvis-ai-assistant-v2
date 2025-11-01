"""
jarvis_scheduler.py
──────────────────────────────────────────────
Lightweight async scheduler for Jarvis.
Used by reminder & schedule skills.
"""

import asyncio
from datetime import datetime, timedelta
from jarvis_core_optimized import JarvisIntegrated

class Scheduler:
    def __init__(self):
        self.tasks = []
        self.loop = asyncio.get_event_loop()

    async def add_task(self, callback, run_at: datetime):
        """Schedule a callback to run at a specific time."""
        delay = (run_at - datetime.now()).total_seconds()
        if delay < 0:
            delay = 0
        task = self.loop.create_task(self._delayed_run(callback, delay))
        self.tasks.append(task)
        return task

    async def _delayed_run(self, callback, delay):
        await asyncio.sleep(delay)
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                callback()
        except Exception as e:
            print(f"[Scheduler Error] {e}")

    def cancel_all(self):
        """Cancel all scheduled tasks."""
        for task in self.tasks:
            if not task.done():
                task.cancel()
        self.tasks.clear()

    def cleanup(self):
        """Remove completed tasks."""
        self.tasks = [t for t in self.tasks if not t.done()]
"""
═══════════════════════════════════════════════════════════════════════════════
FILE: jarvis_scheduler.py
DESCRIPTION: Reminder and task scheduling system with natural language parsing
DEPENDENCIES: sqlite3, datetime, re
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable, List
import re

logger = logging.getLogger("Jarvis.Scheduler")


# ═══════════════════════════════════════════════════════════════════════════
# REMINDER CLASS
# ═══════════════════════════════════════════════════════════════════════════

class Reminder:
    """Individual reminder object"""
    
    def __init__(self, task: str, scheduled_time: datetime, reminder_id: Optional[int] = None):
        self.id = reminder_id
        self.task = task
        self.scheduled_time = scheduled_time
        self.completed = False
    
    def __repr__(self):
        return f"Reminder({self.task}, {self.scheduled_time})"


# ═══════════════════════════════════════════════════════════════════════════
# REMINDER SCHEDULER
# ═══════════════════════════════════════════════════════════════════════════

class ReminderScheduler:
    """Manages reminders and scheduled notifications"""
    
    def __init__(self, db_path: str = "jarvis_memory.db"):
        self.db_path = db_path
        self.reminders: List[Reminder] = []
        self.is_running = False
        self.check_thread = None
        self.callback = None
        self.load_reminders()
    
    def set_callback(self, callback: Callable[[str], None]):
        """Set callback for reminder notifications"""
        self.callback = callback
    
    def add_reminder(self, task: str, scheduled_time: datetime) -> Reminder:
        """Add a new reminder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO reminders (task, scheduled_time, completed) VALUES (?, ?, ?)",
            (task, scheduled_time.isoformat(), 0)
        )
        
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        reminder = Reminder(task, scheduled_time, reminder_id)
        self.reminders.append(reminder)
        
        logger.info(f"Added reminder: {reminder}")
        return reminder
    
    def load_reminders(self):
        """Load pending reminders from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, task, scheduled_time FROM reminders WHERE completed = 0"
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        self.reminders = []
        for row in rows:
            reminder_id, task, scheduled_time_str = row
            scheduled_time = datetime.fromisoformat(scheduled_time_str)
            self.reminders.append(Reminder(task, scheduled_time, reminder_id))
        
        logger.info(f"Loaded {len(self.reminders)} pending reminders")
    
    def mark_completed(self, reminder: Reminder):
        """Mark reminder as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE reminders SET completed = 1 WHERE id = ?",
            (reminder.id,)
        )
        
        conn.commit()
        conn.close()
        
        reminder.completed = True
        self.reminders.remove(reminder)
        
        logger.info(f"Completed reminder: {reminder}")
    
    def check_reminders(self):
        """Check for due reminders"""
        now = datetime.now()
        
        for reminder in self.reminders[:]:
            if reminder.scheduled_time <= now:
                logger.info(f"⏰ Reminder due: {reminder.task}")
                
                # Trigger callback
                if self.callback:
                    self.callback(f"⏰ Reminder: {reminder.task}")
                
                # Mark as completed
                self.mark_completed(reminder)
    
    def start(self):
        """Start the reminder checker thread"""
        if self.is_running:
            return
        
        self.is_running = True
        
        def checker_loop():
            logger.info("Reminder checker started")
            while self.is_running:
                self.check_reminders()
                time.sleep(10)  # Check every 10 seconds
        
        self.check_thread = threading.Thread(target=checker_loop, daemon=True)
        self.check_thread.start()
    
    def stop(self):
        """Stop the reminder checker"""
        self.is_running = False
        logger.info("Reminder checker stopped")
    
    def get_upcoming(self, limit: int = 5) -> List[Reminder]:
        """Get upcoming reminders"""
        sorted_reminders = sorted(self.reminders, key=lambda r: r.scheduled_time)
        return sorted_reminders[:limit]


# ═══════════════════════════════════════════════════════════════════════════
# NATURAL LANGUAGE PARSER
# ═══════════════════════════════════════════════════════════════════════════

class NaturalLanguageParser:
    """Parse natural language into datetime"""
    
    @staticmethod
    def parse_time_expression(text: str) -> Optional[datetime]:
        """
        Parse expressions like:
        - "in 30 minutes"
        - "in 2 hours"
        - "tomorrow at 3pm"
        - "at 5:30pm"
        """
        now = datetime.now()
        text_lower = text.lower()
        
        # Pattern: "in X minutes/hours/days"
        in_pattern = r'in (\d+)\s*(minute|hour|day|min|hr)s?'
        match = re.search(in_pattern, text_lower)
        
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            if unit.startswith('min'):
                return now + timedelta(minutes=amount)
            elif unit.startswith('hour') or unit == 'hr':
                return now + timedelta(hours=amount)
            elif unit.startswith('day'):
                return now + timedelta(days=amount)
        
        # Pattern: "tomorrow"
        if 'tomorrow' in text_lower:
            tomorrow = now + timedelta(days=1)
            
            # Check for time specification
            time_pattern = r'at (\d+):?(\d*)?\s*(am|pm)?'
            time_match = re.search(time_pattern, text_lower)
            
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                meridiem = time_match.group(3)
                
                if meridiem == 'pm' and hour != 12:
                    hour += 12
                elif meridiem == 'am' and hour == 12:
                    hour = 0
                
                return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            else:
                return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Pattern: "at 3pm" (today)
        time_pattern = r'at (\d+):?(\d*)?\s*(am|pm)?'
        time_match = re.search(time_pattern, text_lower)
        
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            meridiem = time_match.group(3)
            
            if meridiem == 'pm' and hour != 12:
                hour += 12
            elif meridiem == 'am' and hour == 12:
                hour = 0
            
            scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time has passed today, schedule for tomorrow
            if scheduled <= now:
                scheduled += timedelta(days=1)
            
            return scheduled
        
        return None


# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULER INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

class SchedulerIntegration:
    """Natural language interface for scheduler"""
    
    def __init__(self, scheduler: ReminderScheduler):
        self.scheduler = scheduler
        self.parser = NaturalLanguageParser()
    
    def parse_command(self, text: str) -> Optional[str]:
        """Parse natural language reminder commands"""
        text_lower = text.lower()
        
        # Check if it's a reminder command
        if not ('remind' in text_lower or 'reminder' in text_lower):
            return None
        
        # Extract the task and time
        if ' to ' in text_lower:
            parts = text.split(' to ', 1)
            task_and_time = parts[1]
            
            # Parse time expression
            scheduled_time = self.parser.parse_time_expression(task_and_time)
            
            if scheduled_time:
                # Extract task (remove time expression)
                task = re.sub(r'\s+(in|at|tomorrow)\s+.*$', '', task_and_time, flags=re.IGNORECASE).strip()
                
                # Add reminder
                reminder = self.scheduler.add_reminder(task, scheduled_time)
                
                time_str = scheduled_time.strftime("%I:%M %p on %B %d")
                return f"✓ Reminder set: '{task}' at {time_str}"
            else:
                return "⚠️ Could not parse time. Try 'in 30 minutes' or 'at 3pm'"
        
        # List reminders
        if 'list' in text_lower or 'show' in text_lower:
            upcoming = self.scheduler.get_upcoming()
            
            if not upcoming:
                return "No upcoming reminders"
            
            response = "📋 Upcoming reminders:\n\n"
            for i, reminder in enumerate(upcoming, 1):
                time_str = reminder.scheduled_time.strftime("%I:%M %p on %b %d")
                response += f"{i}. {reminder.task} - {time_str}\n"
            
            return response
        
        return "⚠️ Could not understand reminder command"


# ═══════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Initialize scheduler
    scheduler = ReminderScheduler()
    
    # Set callback
    def on_reminder(message: str):
        print(f"\n{message}\n")
    
    scheduler.set_callback(on_reminder)
    scheduler.start()
    
    # Create integration
    integration = SchedulerIntegration(scheduler)
    
    # Test commands
    print(integration.parse_command("remind me to stretch in 30 minutes"))
    print(integration.parse_command("remind me to call mom tomorrow at 3pm"))
    print()
    print(integration.parse_command("list reminders"))