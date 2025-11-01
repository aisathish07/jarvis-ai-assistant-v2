"""
skills/system_skill.py
──────────────────────────────────────────────
System Control Skill for Jarvis
Provides system information, power control, and hardware stats.
"""

from jarvis_skills import BaseSkill
import psutil
import platform
import asyncio
import os
import time
import subprocess

class Skill(BaseSkill):
    name = "system"
    keywords = [
        "system info", "cpu", "memory", "ram", "battery", "usage",
        "restart", "shutdown", "sleep", "uptime"
    ]

    async def handle(self, text, jarvis):
        text = text.lower().strip()

        # --- System info ---
        if "system" in text or "info" in text:
            info = self.get_system_info()
            return info

        # --- Resource usage ---
        if any(k in text for k in ["cpu", "ram", "memory", "usage"]):
            usage = self.get_usage()
            return usage

        # --- Power commands ---
        if "shutdown" in text:
            return await self.shutdown()

        if "restart" in text:
            return await self.restart()

        if "sleep" in text:
            return await self.sleep_mode()

        if "uptime" in text:
            return self.get_uptime()

        return "System command not recognized."

    # ─────────────────────────────────────────────
    # Internal methods
    # ─────────────────────────────────────────────

    def get_system_info(self):
        uname = platform.uname()
        info = (
            f"System: {uname.system}\n"
            f"Node Name: {uname.node}\n"
            f"Release: {uname.release}\n"
            f"Version: {uname.version}\n"
            f"Machine: {uname.machine}\n"
            f"Processor: {uname.processor}"
        )
        return info

    def get_usage(self):
        cpu = psutil.cpu_percent(interval=0.8)
        mem = psutil.virtual_memory()
        usage = (
            f"CPU usage: {cpu}%\n"
            f"Memory: {mem.percent}% of {round(mem.total / 1e9, 2)} GB used"
        )
        return usage

    def get_uptime(self):
        uptime_seconds = time.time() - psutil.boot_time()
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"System uptime: {hours} hours and {minutes} minutes."

    async def shutdown(self):
        await asyncio.sleep(0.1)
        try:
            os.system("shutdown /s /t 1")
            return "Shutting down system..."
        except Exception as e:
            return f"Failed to shut down: {e}"

    async def restart(self):
        await asyncio.sleep(0.1)
        try:
            os.system("shutdown /r /t 1")
            return "Restarting system..."
        except Exception as e:
            return f"Failed to restart: {e}"

    async def sleep_mode(self):
        await asyncio.sleep(0.1)
        try:
            subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
            return "System entering sleep mode..."
        except Exception as e:
            return f"Failed to enter sleep: {e}"
