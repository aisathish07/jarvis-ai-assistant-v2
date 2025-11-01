"""
skills/network_skill.py
──────────────────────────────────────────────
Network diagnostic and connectivity skill for Jarvis.
Provides Wi-Fi details, IP info, ping, and speed tests.
"""

from jarvis_skills import BaseSkill
import asyncio
import socket
import subprocess
import re
import psutil
import platform
import aiohttp

class Skill(BaseSkill):
    name = "network"
    keywords = [
        "network", "internet", "wifi", "wi-fi", "connection",
        "ip", "ping", "speed", "test", "online", "offline"
    ]

    async def handle(self, text, jarvis):
        text = text.lower().strip()

        # Intent detection
        if "ping" in text:
            return await self._ping(text)
        elif "speed" in text:
            return await self._speed_test()
        elif "ip" in text:
            return self._get_ip_info()
        elif "wifi" in text or "wi-fi" in text:
            return self._get_wifi_info()
        elif "check" in text or "connection" in text or "internet" in text:
            return await self._check_connectivity()
        else:
            return "Try saying 'ping google', 'check internet', or 'show my IP'."

    # ───────────────────────────────────────────────
    # Connectivity Checks
    # ───────────────────────────────────────────────

    async def _check_connectivity(self) -> str:
        """Checks if the system has active internet access."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://1.1.1.1", timeout=3):
                    return "✅ Internet connection is active."
        except Exception:
            return "⚠️ No active internet connection detected."

    async def _ping(self, text: str) -> str:
        """Ping a host to test latency."""
        match = re.search(r"ping\s+(\S+)", text)
        host = match.group(1) if match else "8.8.8.8"
        try:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            proc = await asyncio.create_subprocess_exec(
                "ping", param, "3", host,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if stderr:
                return f"Error: {stderr.decode().strip()}"
            return f"📡 Ping results for {host}:\n{stdout.decode().strip()}"
        except Exception as e:
            return f"Ping failed: {e}"

    async def _speed_test(self) -> str:
        """Runs a quick async download speed test using Cloudflare CDN."""
        try:
            url = "https://speed.cloudflare.com/__down?bytes=5000000"
            async with aiohttp.ClientSession() as session:
                start = asyncio.get_event_loop().time()
                async with session.get(url, timeout=10) as resp:
                    await resp.read()
                end = asyncio.get_event_loop().time()

            mbps = (5 * 8) / (end - start)  # 5 MB in megabits
            return f"⚡ Approximate download speed: {mbps:.2f} Mbps"
        except Exception:
            return "⚠️ Could not perform speed test (no internet or timeout)."

    def _get_ip_info(self) -> str:
        """Shows local and public IP address."""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            result = f"💻 Local IP: {local_ip}"

            # Attempt to fetch public IP (non-blocking fallback)
            try:
                import requests
                public_ip = requests.get("https://api.ipify.org").text
                result += f"\n🌐 Public IP: {public_ip}"
            except Exception:
                result += "\n🌐 Public IP: unavailable (offline mode)."
            return result
        except Exception as e:
            return f"IP info error: {e}"

    def _get_wifi_info(self) -> str:
        """Retrieves Wi-Fi SSID and signal strength (Windows/Linux)."""
        try:
            if platform.system().lower() == "windows":
                output = subprocess.check_output(
                    ["netsh", "wlan", "show", "interfaces"], encoding="utf-8"
                )
                ssid = re.search(r"SSID\s*:\s*(.+)", output)
                signal = re.search(r"Signal\s*:\s*(\d+)%", output)
                if ssid:
                    wifi_name = ssid.group(1).strip()
                    strength = signal.group(1).strip() if signal else "N/A"
                    return f"📶 Connected Wi-Fi: {wifi_name} ({strength}% signal)"
                else:
                    return "⚠️ Not connected to any Wi-Fi network."
            else:
                output = subprocess.check_output(
                    ["iwgetid"], encoding="utf-8"
                )
                match = re.search(r'SSID:"(.+?)"', output)
                if match:
                    return f"📶 Connected Wi-Fi: {match.group(1)}"
                else:
                    return "⚠️ No Wi-Fi connection found."
        except Exception as e:
            return f"Wi-Fi info unavailable: {e}"
