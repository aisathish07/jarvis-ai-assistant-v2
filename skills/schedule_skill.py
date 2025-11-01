"""
skills/schedule_skill.py
──────────────────────────────────────────────
Unified Scheduling Skill for Jarvis
(SQLite + Recurrence + Spoken Summaries + Proactive Alerts)
"""

from jarvis_skills import BaseSkill
import asyncio
import re
import sqlite3
from datetime import datetime, timedelta
import dateparser
import os
import calendar

DB_FILE = "jarvis_schedule.db"


class Skill(BaseSkill):
    name = "schedule"
    keywords = [
        "remind", "reminder", "event", "meeting", "calendar", "schedule",
        "in", "tomorrow", "today", "next", "cancel", "every",
        "weekday", "weekend", "agenda", "what's on"
    ]

    def __init__(self):
        super().__init__()
        self._init_db()
        self._proactive_task = None

    # ───────────────────────────────────────────────
    # Main Entry Point
    # ───────────────────────────────────────────────
    async def handle(self, text, jarvis):
        text = text.lower().strip()

        # Start background proactive alert loop once
        if self._proactive_task is None:
            self._proactive_task = asyncio.create_task(self._proactive_alert_loop(jarvis))

        if "cancel" in text:
            return await self._cancel_reminder(text)
        if any(k in text for k in ["what", "agenda", "calendar", "schedule", "reminders"]):
            return await self._speak_schedule_summary(text, jarvis)
        if any(k in text for k in ["remind", "add", "schedule", "meeting", "event"]):
            return await self._add_reminder(text, jarvis)

        return "Try 'remind me every weekday at 9 AM to start work' or 'what’s on my schedule today'."

    # ───────────────────────────────────────────────
    # Voice Summary
    # ───────────────────────────────────────────────
    async def _speak_schedule_summary(self, text, jarvis):
        """Reads out upcoming schedule for today/tomorrow/week."""
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        now = datetime.now()

        # Determine time window
        if "tomorrow" in text:
            start = now + timedelta(days=1)
            end = start + timedelta(days=1)
            label = "tomorrow"
        elif "week" in text or "upcoming" in text:
            start = now
            end = now + timedelta(days=7)
            label = "this week"
        else:
            start = now.replace(hour=0, minute=0, second=0)
            end = start + timedelta(days=1)
            label = "today"

        cur.execute(
            "SELECT id, message, time, recurring FROM schedule "
            "WHERE time BETWEEN ? AND ? AND status='pending' ORDER BY time ASC",
            (start.isoformat(), end.isoformat())
        )
        rows = cur.fetchall()
        conn.close()

        if not rows:
            msg = f"You have no events scheduled {label}."
            jarvis.core.voice.speak(msg)
            return msg

        summary_lines = []
        spoken_lines = []
        for _, message, time_str, recurring in rows:
            t = datetime.fromisoformat(time_str)
            time_phrase = t.strftime("%I:%M %p")
            tag = f" ({recurring})" if recurring != "none" else ""
            summary_lines.append(f"• {message} — {t.strftime('%a %b %d, %I:%M %p')}{tag}")
            spoken_lines.append(f"At {time_phrase}, {message}.")

        text_summary = f"📅 Schedule for {label}:\n" + "\n".join(summary_lines)
        spoken = f"You have {len(rows)} event{'s' if len(rows) > 1 else ''} {label}: " + " ".join(spoken_lines)
        await asyncio.to_thread(jarvis.core.voice.speak, spoken)
        return text_summary

    # ───────────────────────────────────────────────
    # Add / Trigger / Reschedule logic
    # ───────────────────────────────────────────────
    async def _add_reminder(self, text, jarvis):
        try:
            recurring = self._detect_recurring_pattern(text)

            match = re.search(r"(remind me|add|schedule)\s*(.*?)\s*(?:at|in|on|tomorrow|next|today|every)?\s*(.*)", text)
            if not match:
                return "Could not parse your reminder."

            _, action, time_part = match.groups()
            message = action.strip() or "something"
            when = dateparser.parse(time_part, settings={"PREFER_DATES_FROM": "future"})

            if not when:
                return "I couldn't understand when to schedule that."

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO schedule (message, time, created_at, status, recurring, alerted) VALUES (?, ?, ?, ?, ?, ?)",
                (message, when.isoformat(), datetime.now().isoformat(), "pending", recurring or "none", 0)
            )
            conn.commit()
            conn.close()

            if hasattr(jarvis, "scheduler"):
                await jarvis.scheduler.add_task(
                    lambda: self._trigger_reminder(message, jarvis, recurring),
                    when
                )

            confirmation = f"⏰ Reminder set for {when.strftime('%A, %I:%M %p')} — '{message}'."
            if recurring != "none":
                confirmation = f"🔁 Recurring reminder set — '{message}' ({recurring})."
            jarvis.core.voice.speak(confirmation)
            return confirmation
        except Exception as e:
            return f"Failed to add reminder: {e}"

    def _detect_recurring_pattern(self, text: str) -> str | None:
        text = text.lower()
        if "every day" in text: return "daily"
        if "every week" in text: return "weekly"
        if "every month" in text: return "monthly"
        if "every weekday" in text: return "weekdays"
        if "every weekend" in text: return "weekends"
        days = [d.lower() for d in calendar.day_name]
        matches = [d for d in days if f"every {d}" in text]
        if matches: return ",".join(matches)
        match = re.search(r"every\s+(\d+)\s*(minute|hour|day|week|month)", text)
        if match: return f"every_{match.group(1)}_{match.group(2)}"
        return "none"

    async def _trigger_reminder(self, message, jarvis, recurring):
        jarvis.core.voice.speak(f"🔔 Reminder: {message}")
        if recurring and recurring != "none":
            await self._reschedule_recurring(message, recurring, jarvis)

    async def _reschedule_recurring(self, message, recurring, jarvis):
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("SELECT id, time FROM schedule WHERE message=? AND recurring=?", (message, recurring))
            row = cur.fetchone()
            if not row: return
            rid, time_str = row
            old_time = datetime.fromisoformat(time_str)
            new_time = self._calculate_next_occurrence(old_time, recurring)
            cur.execute("UPDATE schedule SET time=?, alerted=0 WHERE id=?", (new_time.isoformat(), rid))
            conn.commit()
            conn.close()
            if hasattr(jarvis, "scheduler"):
                await jarvis.scheduler.add_task(
                    lambda: self._trigger_reminder(message, jarvis, recurring),
                    new_time
                )
        except Exception as e:
            print(f"[Reschedule Error] {e}")

    def _calculate_next_occurrence(self, old_time: datetime, recurring: str) -> datetime:
        recurring = recurring or "none"
        if recurring == "daily": return old_time + timedelta(days=1)
        if recurring == "weekly": return old_time + timedelta(weeks=1)
        if recurring == "monthly": return old_time + timedelta(days=30)
        if recurring == "weekdays":
            next_day = old_time + timedelta(days=1)
            while next_day.weekday() >= 5: next_day += timedelta(days=1)
            return next_day
        if recurring == "weekends":
            next_day = old_time + timedelta(days=1)
            while next_day.weekday() < 5: next_day += timedelta(days=1)
            return next_day
        if "," in recurring:
            days = recurring.split(",")
            current_day = old_time.weekday()
            day_map = {d: i for i, d in enumerate(calendar.day_name)}
            next_days = [day_map[d] for d in days if d in day_map]
            next_days.sort()
            for d in next_days:
                if d > current_day:
                    diff = d - current_day
                    return old_time + timedelta(days=diff)
            return old_time + timedelta(days=(7 - current_day + next_days[0]))
        match = re.match(r"every_(\d+)_(minute|hour|day|week|month)", recurring)
        if match:
            n, unit = int(match.group(1)), match.group(2)
            return old_time + timedelta(**{f"{unit}s": n})
        return old_time + timedelta(days=1)

    # ───────────────────────────────────────────────
    # Proactive Alert Loop
    # ───────────────────────────────────────────────
    async def _proactive_alert_loop(self, jarvis):
        """Runs in the background and checks every minute for events within next 5–10 minutes."""
        await asyncio.sleep(5)
        while True:
            try:
                now = datetime.now()
                soon = now + timedelta(minutes=10)

                conn = sqlite3.connect(DB_FILE)
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, message, time FROM schedule WHERE status='pending' AND alerted=0"
                )
                rows = cur.fetchall()
                for rid, msg, t in rows:
                    event_time = datetime.fromisoformat(t)
                    if now <= event_time <= soon:
                        jarvis.core.voice.speak(f"⚡ Upcoming: {msg} in {(event_time - now).seconds // 60} minutes.")
                        cur.execute("UPDATE schedule SET alerted=1 WHERE id=?", (rid,))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[Proactive Loop Error] {e}")

            await asyncio.sleep(60)  # check every minute

    # ───────────────────────────────────────────────
    # Cancel Reminder
    # ───────────────────────────────────────────────
    async def _cancel_reminder(self, text: str) -> str:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        match = re.search(r"cancel\s+(.*)", text)
        if not match:
            return "Specify what to cancel (e.g., 'cancel meeting')."
        keyword = match.group(1).strip()
        cur.execute("SELECT id, message FROM schedule WHERE message LIKE ?", (f"%{keyword}%",))
        row = cur.fetchone()
        if not row:
            conn.close()
            return f"No reminder found containing '{keyword}'."
        rid, msg = row
        cur.execute("UPDATE schedule SET status='canceled' WHERE id=?", (rid,))
        conn.commit()
        conn.close()
        return f"❌ Canceled reminder '{msg}'."

    # ───────────────────────────────────────────────
    # DB Setup
    # ───────────────────────────────────────────────
    def _init_db(self):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            recurring TEXT DEFAULT 'none',
            alerted INTEGER DEFAULT 0
        )
        """)
        conn.commit()
        conn.close()
