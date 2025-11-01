"""
═══════════════════════════════════════════════════════════════════════════════
    JARVIS - Just A Rather Very Intelligent System
    Complete AI Assistant in One File
    
    All modules combined for easy deployment and debugging
    
    Author: Built for MSI Thin 15 (16GB RAM, RTX 3050)
    Python: 3.9+
    Dependencies: ollama, pyttsx3, sounddevice, numpy, pynput, pyautogui, psutil
    
    Usage:
        python JARVIS_ALL_IN_ONE.py install    # Install dependencies
        python JARVIS_ALL_IN_ONE.py chat       # Start chat mode
        python JARVIS_ALL_IN_ONE.py demo       # Run demo
        python JARVIS_ALL_IN_ONE.py            # Interactive menu
═══════════════════════════════════════════════════════════════════════════════
"""
from jarvis_core_optimized import JarvisIntegratedimport
import sys
import os
import json
import sqlite3
import logging
import asyncio
import subprocess
import tempfile
import time
import re
import platform
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, asdict
from urllib.parse import quote_plus

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JARVIS")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: CONFIGURATION MANAGER
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class VoiceConfig:
    tts_rate: int = 175
    tts_volume: float = 0.9
    stt_model: str = "base"
    wake_word_enabled: bool = False
    wake_word: str = "jarvis"
    hotkey: str = "ctrl+space"
    auto_speak: bool = True

@dataclass
class ModelConfig:
    default_model: str = "dolphin-llama3:8b"
    coding_model: str = "deepseek-coder:6.7b"
    creative_model: str = "mistral:7b"
    fast_model: str = "phi3:3.8b"
    lightweight_model: str = "gemma:2b"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048

@dataclass
class AppConfig:
    startup_enabled: bool = False
    system_tray_enabled: bool = True
    gui_theme: str = "dark"
    log_level: str = "INFO"
    memory_limit: int = 100
    auto_cleanup: bool = True

@dataclass
class WebConfig:
    headless_browser: bool = True
    browser_timeout: int = 30
    max_search_results: int = 5
    enable_web_agent: bool = False

@dataclass
class JarvisConfig:
    voice: VoiceConfig
    models: ModelConfig
    app: AppConfig
    web: WebConfig
    
    def __init__(self):
        self.voice = VoiceConfig()
        self.models = ModelConfig()
        self.app = AppConfig()
        self.web = WebConfig()

class ConfigManager:
    def __init__(self, config_file: str = "jarvis_config.json"):
        self.config_file = Path(config_file)
        self.config = JarvisConfig()
        self.load()
    
    def load(self) -> bool:
        if not self.config_file.exists():
            self.save()
            return False
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            if 'voice' in data:
                self.config.voice = VoiceConfig(**data['voice'])
            if 'models' in data:
                self.config.models = ModelConfig(**data['models'])
            if 'app' in data:
                self.config.app = AppConfig(**data['app'])
            if 'web' in data:
                self.config.web = WebConfig(**data['web'])
            return True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False
    
    def save(self) -> bool:
        try:
            data = {
                'voice': asdict(self.config.voice),
                'models': asdict(self.config.models),
                'app': asdict(self.config.app),
                'web': asdict(self.config.web)
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: MEMORY MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class MemoryManager:
    def __init__(self, db_path: str = "jarvis_memory.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_input TEXT,
                assistant_response TEXT,
                model_used TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                scheduled_time TEXT,
                completed INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, user_input: str, response: str, model: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (timestamp, user_input, assistant_response, model_used) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), user_input, response, model)
        )
        conn.commit()
        conn.close()
    
    def get_recent_context(self, limit: int = 5) -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_input, assistant_response FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        results = cursor.fetchall()
        conn.close()
        return list(reversed(results))

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: MODEL ROUTER
# ═══════════════════════════════════════════════════════════════════════════

class ModelRouter:
    MODELS = {
        'coding': 'deepseek-coder:6.7b',
        'creative': 'mistral:7b',
        'general': 'dolphin-llama3:8b',
        'fast': 'phi3:3.8b',
        'lightweight': 'gemma:2b'
    }
    
    KEYWORDS = {
        'coding': ['code', 'debug', 'function', 'python', 'javascript', 'programming', 'script', 'error'],
        'creative': ['story', 'write', 'poem', 'creative', 'character', 'scene', 'narrative'],
        'fast': ['quick', 'briefly', 'fast', 'short answer'],
    }
    
    @classmethod
    def select_model(cls, user_input: str) -> str:
        user_lower = user_input.lower()
        for task_type, keywords in cls.KEYWORDS.items():
            if any(kw in user_lower for kw in keywords):
                return cls.MODELS[task_type]
        return cls.MODELS['general']

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: VOICE I/O
# ═══════════════════════════════════════════════════════════════════════════

class VoiceIO:
    def __init__(self):
        self.tts_engine = None
        self.init_tts()
    
    def init_tts(self):
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 175)
            self.tts_engine.setProperty('volume', 0.9)
            logger.info("TTS initialized")
        except Exception as e:
            logger.warning(f"TTS initialization failed: {e}")
    
    def speak(self, text: str):
        if self.tts_engine:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS error: {e}")
    
    def stop_speech(self):
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: WINDOWS APP CONTROL
# ═══════════════════════════════════════════════════════════════════════════

class WindowsAppController:
    APP_PATHS = {
        'chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        'firefox': r'C:\Program Files\Mozilla Firefox\firefox.exe',
        'edge': r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        'notepad': 'notepad.exe',
        'calculator': 'calc.exe',
    }
    
    def open_app(self, app_name: str) -> bool:
        try:
            app_lower = app_name.lower()
            if app_lower in self.APP_PATHS:
                subprocess.Popen([self.APP_PATHS[app_lower]])
                logger.info(f"Opened {app_name}")
                return True
            else:
                subprocess.Popen(app_name, shell=True)
                return True
        except Exception as e:
            logger.error(f"Failed to open {app_name}: {e}")
            return False
    
    def close_app(self, app_name: str) -> bool:
        try:
            import psutil
            closed_any = False
            app_lower = app_name.lower()
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if app_lower in proc_name:
                        proc.terminate()
                        logger.info(f"Terminated {proc.info['name']}")
                        closed_any = True
                except:
                    pass
            return closed_any
        except Exception as e:
            logger.error(f"Failed to close {app_name}: {e}")
            return False
    
    def type_text(self, text: str):
        try:
            import pyautogui
            time.sleep(0.5)
            pyautogui.write(text, interval=0.05)
            logger.info(f"Typed {len(text)} characters")
        except Exception as e:
            logger.error(f"Failed to type: {e}")
    
    def save_file(self):
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', 's')
            logger.info("Pressed Ctrl+S")
        except Exception as e:
            logger.error(f"Failed to save: {e}")

class AppControlIntegration:
    def __init__(self):
        self.controller = WindowsAppController()
    
    def parse_command(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        
        if 'open' in text_lower or 'launch' in text_lower:
            for app in self.controller.APP_PATHS.keys():
                if app in text_lower:
                    success = self.controller.open_app(app)
                    return f"Opening {app}..." if success else f"Failed to open {app}"
        
        if 'close' in text_lower or 'quit' in text_lower:
            for app in self.controller.APP_PATHS.keys():
                if app in text_lower:
                    success = self.controller.close_app(app)
                    return f"Closed {app}" if success else f"{app} not found"
        
        if 'save' in text_lower and 'file' in text_lower:
            self.controller.save_file()
            return "Saved file"
        
        if 'type' in text_lower and '"' in text:
            start = text.index('"') + 1
            end = text.rindex('"')
            to_type = text[start:end]
            self.controller.type_text(to_type)
            return f"Typed: {to_type}"
        
        return None

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: REMINDER SCHEDULER
# ═══════════════════════════════════════════════════════════════════════════

class Reminder:
    def __init__(self, task: str, scheduled_time: datetime, reminder_id: Optional[int] = None):
        self.id = reminder_id
        self.task = task
        self.scheduled_time = scheduled_time
        self.completed = False

class ReminderScheduler:
    def __init__(self, db_path: str = "jarvis_memory.db"):
        self.db_path = db_path
        self.reminders: List[Reminder] = []
        self.is_running = False
        self.callback = None
        self.load_reminders()
    
    def set_callback(self, callback: Callable[[str], None]):
        self.callback = callback
    
    def add_reminder(self, task: str, scheduled_time: datetime) -> Reminder:
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
        logger.info(f"Added reminder: {reminder.task}")
        return reminder
    
    def load_reminders(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, task, scheduled_time FROM reminders WHERE completed = 0")
        rows = cursor.fetchall()
        conn.close()
        
        self.reminders = []
        for row in rows:
            reminder_id, task, scheduled_time_str = row
            scheduled_time = datetime.fromisoformat(scheduled_time_str)
            self.reminders.append(Reminder(task, scheduled_time, reminder_id))
    
    def mark_completed(self, reminder: Reminder):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE reminders SET completed = 1 WHERE id = ?", (reminder.id,))
        conn.commit()
        conn.close()
        reminder.completed = True
        self.reminders.remove(reminder)
    
    def check_reminders(self):
        now = datetime.now()
        for reminder in self.reminders[:]:
            if reminder.scheduled_time <= now:
                logger.info(f"⏰ Reminder: {reminder.task}")
                if self.callback:
                    self.callback(f"⏰ Reminder: {reminder.task}")
                self.mark_completed(reminder)
    
    def get_upcoming(self, limit: int = 5) -> List[Reminder]:
        return sorted(self.reminders, key=lambda r: r.scheduled_time)[:limit]

class NaturalLanguageParser:
    @staticmethod
    def parse_time_expression(text: str) -> Optional[datetime]:
        now = datetime.now()
        text_lower = text.lower()
        
        # "in X minutes/hours/days"
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
        
        # "at 3pm"
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
            if scheduled <= now:
                scheduled += timedelta(days=1)
            return scheduled
        
        return None

class SchedulerIntegration:
    def __init__(self, scheduler: ReminderScheduler):
        self.scheduler = scheduler
        self.parser = NaturalLanguageParser()
    
    def parse_command(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        
        if not ('remind' in text_lower or 'reminder' in text_lower):
            return None
        
        if ' to ' in text_lower:
            parts = text.split(' to ', 1)
            task_and_time = parts[1]
            scheduled_time = self.parser.parse_time_expression(task_and_time)
            
            if scheduled_time:
                task = re.sub(r'\s+(in|at|tomorrow)\s+.*$', '', task_and_time, flags=re.IGNORECASE).strip()
                self.scheduler.add_reminder(task, scheduled_time)
                time_str = scheduled_time.strftime("%I:%M %p on %B %d")
                return f"✓ Reminder set: '{task}' at {time_str}"
            else:
                return "⚠️ Could not parse time. Try 'in 30 minutes' or 'at 3pm'"
        
        if 'list' in text_lower or 'show' in text_lower:
            upcoming = self.scheduler.get_upcoming()
            if not upcoming:
                return "No upcoming reminders"
            response = "📋 Upcoming reminders:\n\n"
            for i, reminder in enumerate(upcoming, 1):
                time_str = reminder.scheduled_time.strftime("%I:%M %p on %b %d")
                response += f"{i}. {reminder.task} - {time_str}\n"
            return response
        
        return None

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: CORE JARVIS
# ═══════════════════════════════════════════════════════════════════════════

class JarvisCore:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.memory = MemoryManager()
        self.voice = VoiceIO()
        self.router = ModelRouter()
    
    async def process_query(self, user_input: str, speak: bool = True) -> str:
        try:
            model = self.router.select_model(user_input)
            context = self.memory.get_recent_context(limit=3)
            prompt = self._build_prompt(user_input, context)
            
            logger.info(f"Processing with {model}...")
            response = await self._query_ollama(model, prompt)
            
            self.memory.save_conversation(user_input, response, model)
            
            if speak and self.config_manager.config.voice.auto_speak:
                self.voice.speak(response)
            
            return response
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _build_prompt(self, user_input: str, context: list) -> str:
        prompt_parts = ["You are Jarvis, a helpful AI assistant.\n\n"]
        
        if context:
            prompt_parts.append("Recent conversation:\n")
            for user_msg, asst_msg in context:
                prompt_parts.append(f"User: {user_msg}\n")
                prompt_parts.append(f"Assistant: {asst_msg}\n")
            prompt_parts.append("\n")
        
        prompt_parts.append(f"User: {user_input}\nAssistant:")
        return "".join(prompt_parts)
    
    async def _query_ollama(self, model: str, prompt: str) -> str:
        try:
            import ollama
            response = ollama.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'temperature': self.config_manager.config.models.temperature,
                    'top_p': self.config_manager.config.models.top_p,
                    'num_predict': self.config_manager.config.models.max_tokens
                }
            )
            return response['message']['content']
        except Exception as e:
            return f"Ollama error: {str(e)}"

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: INTEGRATED JARVIS
# ═══════════════════════════════════════════════════════════════════════════

class JarvisIntegrated(JarvisCore):
    def __init__(self):
        super().__init__()
        self.app_control = AppControlIntegration()
        self.reminder_scheduler = ReminderScheduler()
        self.scheduler_integration = SchedulerIntegration(self.reminder_scheduler)
        self.reminder_scheduler.set_callback(self.on_reminder)
        logger.info("✓ All integrations loaded")
    
    def on_reminder(self, message: str):
        logger.info(message)
        self.voice.speak(message)
    
    async def process_query(self, user_input: str, speak: bool = True) -> str:
        try:
            # Try app control
            app_response = self.app_control.parse_command(user_input)
            if app_response:
                if speak:
                    self.voice.speak(app_response)
                self.memory.save_conversation(user_input, app_response, "app_control")
                return app_response
            
            # Try scheduler
            scheduler_response = self.scheduler_integration.parse_command(user_input)
            if scheduler_response:
                if speak:
                    self.voice.speak(scheduler_response)
                self.memory.save_conversation(user_input, scheduler_response, "scheduler")
                return scheduler_response
            
            # Default: AI processing
            response = await super().process_query(user_input, speak=speak)
            return response
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_status_summary(self) -> str:
        status = "🤖 JARVIS System Status\n"
        status += "=" * 40 + "\n\n"
        status += "📊 Available Models:\n"
        for task, model in ModelRouter.MODELS.items():
            status += f"  • {task}: {model}\n"
        status += "\n"
        recent = self.memory.get_recent_context(limit=5)
        status += f"💾 Conversation History: {len(recent)} recent exchanges\n\n"
        upcoming = self.reminder_scheduler.get_upcoming()
        status += f"⏰ Upcoming Reminders: {len(upcoming)}\n"
        for reminder in upcoming[:3]:
            time_str = reminder.scheduled_time.strftime("%I:%M %p")
            status += f"  • {reminder.task} at {time_str}\n"
        status += "\n" + "=" * 40
        return status
    
    def cleanup(self):
        logger.info("Cleaning up...")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 9: INSTALLER
# ═══════════════════════════════════════════════════════════════════════════

class JarvisInstaller:
    def __init__(self):
        self.python_cmd = sys.executable
    
    def check_ollama(self):
        print("\n[INFO] Checking Ollama installation...")
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✓ Ollama is installed and running")
                return True
            else:
                print("✗ Ollama not responding")
                return False
        except FileNotFoundError:
            print("✗ Ollama not found")
            print("  Install from: https://ollama.com/download")
            return False
        except Exception as e:
            print(f"✗ Ollama check failed: {e}")
            return False
    
    def install_dependencies(self):
        print("\n[INFO] Installing dependencies...")
        packages = [
            "ollama",
            "pyttsx3",
            "sounddevice",
            "numpy",
            "pynput",
            "pyautogui",
            "psutil"
        ]
        
        for package in packages:
            print(f"  Installing {package}...")
            try:
                subprocess.run(
                    [self.python_cmd, "-m", "pip", "install", package, "-q"],
                    check=True,
                    timeout=120
                )
                print(f"  ✓ {package}")
            except:
                print(f"  ⚠ {package} (may need manual install)")
        
        print("\n✓ Dependencies installed")
    
    def run_installation(self):
        print("\n" + "="*60)
        print("  JARVIS AI ASSISTANT - INSTALLATION")
        print("="*60)
        
        # Check Ollama
        if not self.check_ollama():
            print("\n⚠ Please install Ollama first: https://ollama.com/download")
            return False
        
        # Install dependencies
        self.install_dependencies()
        
        # Create database
        MemoryManager()
        print("\n✓ Database initialized")
        
        # Create config
        ConfigManager()
        print("✓ Configuration created")
        
        print("\n" + "="*60)
        print("  ✓ INSTALLATION COMPLETE!")
        print("="*60)
        print("\nTo start JARVIS:")
        print("  python JARVIS_ALL_IN_ONE.py chat")
        return True

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 10: CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

async def interactive_mode():
    jarvis = JarvisIntegrated()
    
    print("\n" + "=" * 60)
    print("🤖 JARVIS AI ASSISTANT - Interactive Mode")
    print("=" * 60)
    print("\nType your questions or commands.")
    print("Commands: 'status', 'exit'\n")
    print("=" * 60 + "\n")
    
    try:
        while True:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nJarvis: Goodbye!\n")
                break
            
            if user_input.lower() == 'status':
                print("\n" + jarvis.get_status_summary() + "\n")
                continue
            
            response = await jarvis.process_query(user_input, speak=False)
            print(f"\nJarvis: {response}\n")
    
    except KeyboardInterrupt:
        print("\n\nShutting down...\n")
    finally:
        jarvis.cleanup()

async def demo_mode():
    jarvis = JarvisIntegrated()
    
    print("\n" + "=" * 60)
    print("🎬 JARVIS DEMO MODE")
    print("=" * 60 + "\n")
    
    demos = [
        ("Introduction", "What are you?"),
        ("Coding", "Write a Python function to reverse a string"),
        ("App Control", "open notepad"),
        ("Reminder", "remind me to stretch in 2 minutes"),
    ]
    
    for category, query in demos:
        print(f"\n{'='*60}")
        print(f"📍 {category}: {query}")
        print('='*60)
        response = await jarvis.process_query(query, speak=False)
        print(f"{response}\n")
        await asyncio.sleep(2)
    
    print("\n✓ Demo complete!\n")
    jarvis.cleanup()

def quick_query(query: str):
    jarvis = JarvisIntegrated()
    async def run():
        response = await jarvis.process_query(query, speak=False)
        print(response)
        jarvis.cleanup()
    asyncio.run(run())

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 11: MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def show_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗             ║
║        ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝             ║
║        ██║███████║██████╔╝██║   ██║██║███████╗             ║
║   ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║             ║
║   ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║             ║
║    ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝             ║
║                                                              ║
║              Just A Rather Very Intelligent System          ║
║                  All-In-One Edition v1.0                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

def show_menu():
    show_banner()
    print("\n🎯 What would you like to do?\n")
    print("  1. Start Interactive Chat")
    print("  2. Run Feature Demo")
    print("  3. Show System Status")
    print("  4. Install Dependencies")
    print("  5. Quick Query")
    print("  6. Exit")
    print("\n" + "="*62)

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "install":
            installer = JarvisInstaller()
            installer.run_installation()
        
        elif command == "chat":
            asyncio.run(interactive_mode())
        
        elif command == "demo":
            asyncio.run(demo_mode())
        
        elif command == "status":
            jarvis = JarvisIntegrated()
            print(jarvis.get_status_summary())
            jarvis.cleanup()
        
        elif command == "query" or command.startswith("-"):
            # Treat as query
            query = " ".join(sys.argv[1:]) if command.startswith("-") else " ".join(sys.argv[2:])
            if query:
                quick_query(query)
            else:
                print("Usage: python JARVIS_ALL_IN_ONE.py query 'your question'")
        
        else:
            # Treat entire argument as query
            query = " ".join(sys.argv[1:])
            quick_query(query)
    
    else:
        # Interactive menu
        while True:
            show_menu()
            choice = input("\nYour choice: ").strip()
            
            if choice == "1":
                asyncio.run(interactive_mode())
                input("\nPress Enter to continue...")
            
            elif choice == "2":
                asyncio.run(demo_mode())
                input("\nPress Enter to continue...")
            
            elif choice == "3":
                jarvis = JarvisIntegrated()
                print("\n" + jarvis.get_status_summary())
                jarvis.cleanup()
                input("\nPress Enter to continue...")
            
            elif choice == "4":
                installer = JarvisInstaller()
                installer.run_installation()
                input("\nPress Enter to continue...")
            
            elif choice == "5":
                query = input("\nEnter your question: ").strip()
                if query:
                    quick_query(query)
                input("\nPress Enter to continue...")
            
            elif choice == "6":
                print("\n👋 Goodbye!\n")
                break
            
            else:
                print("\n❌ Invalid choice. Please select 1-6.")
                time.sleep(1)

if __name__ == "__main__":
    main()

# ═══════════════════════════════════════════════════════════════════════════
# END OF JARVIS ALL-IN-ONE
# ═══════════════════════════════════════════════════════════════════════════

"""
USAGE EXAMPLES:

1. Install dependencies:
   python JARVIS_ALL_IN_ONE.py install

2. Start chat mode:
   python JARVIS_ALL_IN_ONE.py chat

3. Run demo:
   python JARVIS_ALL_IN_ONE.py demo

4. Check status:
   python JARVIS_ALL_IN_ONE.py status

5. Quick query:
   python JARVIS_ALL_IN_ONE.py "What is Python?"

6. Interactive menu:
   python JARVIS_ALL_IN_ONE.py

═══════════════════════════════════════════════════════════════════════════════

FEATURES INCLUDED IN THIS FILE:

✅ AI Chat (5 models with auto-routing)
✅ Conversation Memory (SQLite)
✅ Configuration Management
✅ Voice Output (TTS)
✅ Windows App Control
✅ Smart Reminders
✅ Natural Language Processing
✅ Model Selection Intelligence
✅ Context-Aware Responses
✅ One-Click Installation

REQUIREMENTS:

- Python 3.9+
- Ollama (https://ollama.com/download)
- Models: dolphin-llama3:8b, deepseek-coder:6.7b, mistral:7b, phi3:3.8b, gemma:2b
- Dependencies: ollama, pyttsx3, sounddevice, numpy, pynput, pyautogui, psutil

INSTALLATION:

1. Install Ollama: https://ollama.com/download
2. Pull models: ollama pull dolphin-llama3:8b (and others)
3. Run: python JARVIS_ALL_IN_ONE.py install
4. Start: python JARVIS_ALL_IN_ONE.py chat

═══════════════════════════════════════════════════════════════════════════════

TROUBLESHOOTING:

Problem: "Ollama not found"
Solution: Install from https://ollama.com/download

Problem: "Model not found"
Solution: ollama pull [model-name]

Problem: Import errors
Solution: python JARVIS_ALL_IN_ONE.py install

Problem: Slow responses
Solution: Use phi3:3.8b or gemma:2b model

═══════════════════════════════════════════════════════════════════════════════

FILE STRUCTURE:

Section 1:  Configuration Manager
Section 2:  Memory Manager (SQLite)
Section 3:  Model Router (Auto-selection)
Section 4:  Voice I/O (TTS)
Section 5:  Windows App Control
Section 6:  Reminder Scheduler
Section 7:  Core Jarvis (AI Processing)
Section 8:  Integrated Jarvis (Full System)
Section 9:  Installer
Section 10: CLI Interface
Section 11: Main Entry Point

Total: ~700 lines of production-ready code

═══════════════════════════════════════════════════════════════════════════════

Made with ❤️ for local AI enthusiasts
"Sometimes you gotta run before you can walk." - Tony Stark

═══════════════════════════════════════════════════════════════════════════════
"""