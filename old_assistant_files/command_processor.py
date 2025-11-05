# command_processor.py – FINAL edition (web-agent + app-controller wired)
from __future__ import annotations

import asyncio
import importlib
import json
import logging
import os
import pathlib
import platform
import re
import subprocess
import sys
import webbrowser
from collections import deque
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import certifi
import dateparser
import pyautogui
import spacy
from apscheduler.schedulers.asyncio import AsyncIOScheduler

_ALIAS = (
    json.loads(pathlib.Path("aliases.json").read_text())
    if pathlib.Path("aliases.json").exists()
    else {}
)
# ------------------------------------------------------------------
#  Optional soft-fail imports
# ------------------------------------------------------------------
try:
    from llm_manager import close_sessions, get_llm_response
except ImportError:
    get_llm_response = None
    close_sessions = None

try:
    from attic.suggestion_engine import SuggestionEngine
except ImportError:
    SuggestionEngine = None

# ------------------------------------------------------------------
#  NEW: force-import the previously orphaned modules
# ------------------------------------------------------------------
from attic.app_controller import AppController  # was missing → in-app controls dead
from attic.web_agent import WebAgent  # was missing → web features dead

if TYPE_CHECKING:
    from app_scanner import AppManager
    from attic.predictive_model import PredictiveModel
    from gui import AssistantGUI
    from memory_manager import MemoryManager
    from tts import TextToSpeech

logger = logging.getLogger("AI_Assistant.CommandProcessor")

# ------------------------------------------------------------------
#  Certifi auto-repair (idempotent)
# ------------------------------------------------------------------
CERTIFI_VERSION = "2025.8.3"


def ensure_certifi() -> None:
    try:
        pem = certifi.where()
        if not os.path.isfile(pem):
            raise FileNotFoundError(pem)
        logger.info("[Startup Check] ✅ certifi OK: %s", pem)
    except Exception as exc:
        logger.warning("[Startup Check] ⚠️  Repairing certifi: %s", exc)
        for action in (
            ["uninstall", "-y", "certifi"],
            ["install", "--force-reinstall", "--no-deps", f"certifi=={CERTIFI_VERSION}"],
        ):
            subprocess.run([sys.executable, "-m", "pip", *action], check=True)
        importlib.invalidate_caches()
        if not os.path.isfile(certifi.where()):
            raise RuntimeError("Certifi auto-repair failed.")
        logger.info("[Startup Check] 🔧 certifi reinstalled.")


# ------------------------------------------------------------------
#  CommandProcessor
# ------------------------------------------------------------------
class CommandProcessor:
    def __init__(
        self,
        gui: AssistantGUI,
        app_manager: AppManager,
        memory_manager: MemoryManager,
        tts_engine: TextToSpeech,
        predictor: PredictiveModel,
    ) -> None:
        ensure_certifi()
        self.gui = gui
        self.app_manager = app_manager
        self.memory = memory_manager
        self.tts = tts_engine
        self.predictor = predictor

        # NEW: instantiate orphaned helpers
        self.web_agent = WebAgent()
        self.app_controller = AppController()

        # scheduler – created but not started until loop bound
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._scheduler_initialized = False
        self._context_lock = asyncio.Lock()

        # spaCy
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded.")
        except OSError:
            logger.error("spaCy model 'en_core_web_sm' not found.")
            self.nlp = None

        # memory layers + async lock for thread safety
        self.context_window: deque[Tuple[str, str]] = deque(maxlen=10)
        self.summary_memory: str = self.memory.get_user_preference("summary_memory") or ""
        self.summary_trigger = 5

        # metrics
        self.metrics: Dict[str, Any] = {
            "total_tokens": 0,
            "last_latency": 0.0,
            "last_provider": None,
        }

        # intent keywords – extended with web & app controls
        self.intents = {
            "remember_preference": ["remember", "my favorite is"],
            "open_app": ["open", "launch", "start"],
            "search_in_app": ["search", "find"],
            "play_media": ["play", "listen", "watch"],
            "get_time": ["time"],
            "get_date": ["date"],
            "take_screenshot": ["screenshot"],
            "set_reminder": ["remind", "reminder"],
            "show_reminders": ["reminders", "schedule"],
            "show_suggestions": ["suggestions", "suggest"],
            "exit": ["exit", "quit", "goodbye"],
            "greet": ["hello", "hi", "hey"],
            # NEW intents
            "web_search": ["google", "search google", "look up"],
            "amazon_search": ["amazon", "search amazon"],
            "fill_form": ["fill form", "complete form"],
            "web_screenshot": ["screenshot page"],
            "app_command": [
                "in chrome",
                "in spotify",
                "in discord",
                "in vscode",
                "in notepad",
                "in whatsapp",
            ],
        }
        self.last_context: Dict[str, Any] = {
            "intent": None,
            "app": None,
            "service": None,
            "query": None,
            "entities": {},
            "search_results": [],
        }

        # plugin manager (soft fail)
        try:
            from attic.plugin_system import PluginManager

            self.plugin_manager = PluginManager("skills")
            self.plugin_manager.discover_and_load({"speak": self.speak, "open_app": self.open_app})
            logger.info("Loaded skills: %s", self.plugin_manager.list_skills())
        except ImportError:
            logger.warning("PluginManager not available – skills disabled.")
            self.plugin_manager = None

        self._validate_dependencies()

    # ------------------------------------------------------------------
    #  Dependency validation
    # ------------------------------------------------------------------
    def _validate_dependencies(self) -> None:
        missing = []
        if get_llm_response is None:
            missing.append("llm_manager")
        if SuggestionEngine is None:
            missing.append("suggestion_engine")
        if missing:
            logger.warning("Missing optional dependencies: %s", missing)

    # ------------------------------------------------------------------
    #  Event-loop binding – starts scheduler on the correct loop
    # ------------------------------------------------------------------
    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        if not self._scheduler_initialized:
            self.scheduler = AsyncIOScheduler(event_loop=loop, timezone="UTC")
            self.scheduler.start()
            self._scheduler_initialized = True
            loop.create_task(self._load_and_schedule_reminders())
            logger.info("Scheduler started on event-loop.")

    async def web_search(self, text: str) -> str:
        query = re.sub(r"^(google|search google|look up)\s+", "", text, flags=re.I)
        quick = await self.qsearch.google(query)
        if quick:
            return f"Quick answer: {quick}"
        # fall back to full browser search
        results = await self.web_agent.google_search(query, num_results=3)
        if not results:
            return "No results found."
        return "Top results: " + " | ".join(r["title"] for r in results)

    # ------------------------------------------------------------------
    #  Reminders
    # ------------------------------------------------------------------
    async def _load_and_schedule_reminders(self) -> None:
        reminders = self.memory.get_reminders() or []
        count = 0
        for r in reminders:
            run_time_str = r.get("run_time")
            if not run_time_str:
                continue
            try:
                run_date = datetime.fromisoformat(run_time_str)
            except Exception:
                continue
            if run_date <= datetime.now():
                continue
            if self.scheduler:
                try:
                    self.scheduler.add_job(
                        self._trigger_reminder, "date", run_date=run_date, args=[r["id"], r["text"]]
                    )
                    count += 1
                except Exception as e:
                    logger.error("Failed to schedule reminder: %s", e)
        logger.info("Scheduled %d reminders.", count)

    async def _trigger_reminder(self, reminder_id: int, text: str) -> None:
        try:
            await self.speak(f"This is a reminder to {text}.")
            self.memory.mark_reminder_as_complete(reminder_id)
            logger.info("Reminder %d triggered.", reminder_id)
            logger.info("🔔 REMINDER FIRE: %s", text)
        except Exception as e:
            logger.error("Error triggering reminder %d: %s", reminder_id, e)

    # ------------------------------------------------------------------
    #  Main execution entry
    # ------------------------------------------------------------------
    async def execute(self, command_text: str) -> str:
        self.gui.gui_queue.put(("add_history", command_text, True))

        if not command_text.strip():
            return ""
        resolved = self._resolve_pronouns(command_text)
        intent, entities = self._parse_command_nlp(resolved)
        self.last_context.update({"intent": intent, **entities})

        # plugin hook
        if self.plugin_manager:
            plugin_replies = await asyncio.to_thread(
                self.plugin_manager.handle_command, resolved, self._build_context_for_plugins()
            )
            if plugin_replies:
                for reply in plugin_replies:
                    await self.speak(reply)
                    self.gui.gui_queue.put(("add_history", reply, False))
                self.memory.log_command(command_text, ", ".join(plugin_replies), True)
                return ""

        # intent routing
        response_text: Optional[str] = None
        try:
            if intent == "remember_preference":
                response_text = await self.remember_preference(resolved)
            elif intent == "open_app":
                m = re.search(r"open\s+(.+)", resolved, re.I)
                response_text = (
                    await asyncio.to_thread(self.open_app, m.group(1))
                    if m
                    else "Which application?"
                )
            elif intent == "get_time":
                response_text = self.get_time()
            elif intent == "get_date":
                response_text = self.get_date()
            elif intent == "take_screenshot":
                response_text = await asyncio.to_thread(self.take_screenshot)
            elif intent == "show_suggestions":
                await self.show_suggestions()
                return ""
            elif intent == "set_reminder":
                response_text = await self.set_reminder(resolved)
            elif intent == "show_reminders":
                response_text = await self.show_reminders()
            elif intent == "greet":
                response_text = "Hello! How can I help you?"
            elif intent == "exit":
                await self.speak("Goodbye!")
                return "exit"

            # NEW web intents
            elif intent == "web_search":
                response_text = await self.web_search(resolved)
            elif intent == "amazon_search":
                response_text = await self.amazon_search(resolved)
            elif intent == "fill_form":
                response_text = await self.fill_form(resolved)
            elif intent == "web_screenshot":
                response_text = await self.web_screenshot(resolved)

            # NEW in-app control intent
            elif intent == "app_command":
                response_text = await self.app_command(resolved)

            else:
                await self.handle_unknown(resolved)
                return ""
        except Exception:
            logger.exception("Error handling intent %s", intent)
            response_text = "I ran into an error while performing that action."

        # Add assistant's reply to GUI and memory
        if response_text:
            await self.speak(response_text)
            self.gui.gui_queue.put(("add_history", response_text, False))
            self.memory.log_command(command_text, response_text, True)
            async with self._context_lock:
                self.context_window.append((command_text, response_text))
                if len(self.context_window) >= self.summary_trigger:
                    await self._summarize_context()
        return ""

    # ------------------------------------------------------------------
    #  NEW – web-agent helpers
    # ------------------------------------------------------------------
    async def web_search(self, text: str) -> str:
        query = re.sub(r"^(google|search google|look up)\s+", "", text, flags=re.I)
        if not query:
            return "What should I search for?"
        await self.speak(f"Searching for {query}")

        # NEW: smart search (HTTP first → browser fallback)
        results = await self.web_agent.search(query, num_results=3)

        if not results:
            return "I couldn't find any results."

        # pretty numbered list
        reply = "Top results:\n"
        for i, r in enumerate(results, 1):
            reply += f"{i}. {r['title']}\n   {r['url']}\n"
        return reply

    async def amazon_search(self, text: str) -> str:
        query = re.sub(r"^(amazon|search amazon)\s+", "", text, flags=re.I)
        if not query:
            return "What product should I look for?"
        await self.speak(f"Searching Amazon for {query}")
        data = await self.web_agent.search_amazon(query)
        if data.get("error"):
            return f"Amazon search failed: {data['error']}"
        prods = data.get("products", [])
        if not prods:
            return "No products found."
        reply = "Found: " + " | ".join(f"{p['title']} ({p['price']})" for p in prods[:3])
        return reply

    async def fill_form(self, text: str) -> str:
        # Very naive parser – demo only
        m = re.search(r"fill form at (.+?) with (.+)", text, re.I)
        if not m:
            return "Say: fill form at <url> with field1=value1, field2=value2"
        url, pairs = m.groups()
        form_data = {}
        for pair in pairs.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                form_data[k.strip()] = v.strip()
        ok = await self.web_agent.fill_form(url.strip(), form_data)
        return "Form filled successfully." if ok else "Form filling failed."

    async def web_screenshot(self, text: str) -> str:
        m = re.search(r"screenshot page (.+)", text, re.I)
        if not m:
            return "Which page should I capture?"
        url = m.group(1).strip()
        path = await self.web_agent.take_screenshot(url)
        return f"Screenshot saved as {path}" if path else "Screenshot failed."

    # ------------------------------------------------------------------
    #  NEW – in-app controller
    # ------------------------------------------------------------------
    async def app_command(self, text: str) -> str:
        # crude regex:  "in <app> <command> [args]"
        m = re.search(r"in (\w+)\s+(\w+)\s*(.+)?", text, re.I)
        if not m:
            return "Say: in <app> <command> [arguments]"
        app, cmd, args = m.groups()
        params = {}
        if args:
            # very simple key=val splitter
            for bit in args.split():
                if "=" in bit:
                    k, v = bit.split("=", 1)
                    params[k] = v
        return await asyncio.to_thread(
            self.app_controller.execute_command, app.lower(), cmd.lower(), **params
        )

    # ------------------------------------------------------------------
    #  Unknown intent → LLM
    # ------------------------------------------------------------------
    async def handle_unknown(self, text: str) -> None:
        if get_llm_response is None:
            await self.speak("I don't know how to help with that.")
            self.gui.gui_queue.put(("add_history", "I don't know how to help with that.", False))
            return

        PERSONALITY = (
            "You are Jarvis, a helpful AI assistant. Answer directly and naturally. "
            "Stay in character. Never reveal you are a language model."
        )
        async with self._context_lock:
            history = "\n".join(
                f"User: {u}\nJarvis: {a}" for u, a in list(self.context_window)[-5:]
            )
        prompt = f"{PERSONALITY}\n\nLong-term summary:\n{self.summary_memory}\n\nRecent chat:\n{history}\n\nUser: {text}\nJarvis:"

        try:
            provider = self._choose_provider(text)
            raw = await asyncio.wait_for(get_llm_response(prompt, provider=provider), timeout=30)
            if raw and isinstance(raw, str):
                cleaned = self._postprocess(raw)
                await self.speak(cleaned)
                self.gui.gui_queue.put(("add_history", cleaned, False))
                self.memory.log_command(text, cleaned, success=True)
                async with self._context_lock:
                    self.context_window.append((text, cleaned))
                    if len(self.context_window) >= self.summary_trigger:
                        await self._summarize_context()
            else:
                msg = "I'm not sure how to respond to that."
                await self.speak(msg)
                self.gui.gui_queue.put(("add_history", msg, False))
        except asyncio.TimeoutError:
            msg = "The LLM service took too long to respond."
            await self.speak(msg)
            logger.warning("LLM timeout for provider: %s", provider)
        except Exception as e:
            logger.error("LLM error in handle_unknown: %s", e)
            msg = "I encountered an error processing your request."
            await self.speak(msg)
            self.gui.gui_queue.put(("add_history", msg, False))

    def _choose_provider(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in ("weather", "news", "explain", "define", "what is", "who is")):
            return "gemini"
        if any(k in t for k in ("code", "python", "javascript", "programming", "debug")):
            return "ollama"
        if any(k in t for k in ("calculate", "math", "solve", "how many")):
            return "gemini"
        return "gemini"

    def _postprocess(self, text: str) -> str:
        if not text:
            return "I'm not sure how to respond to that."
        text = text.strip()
        for prefix in ("Jarvis:", "AI:", "Assistant:"):
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix) :].strip()
        return text

    # ------------------------------------------------------------------
    #  Long-term memory summarisation
    # ------------------------------------------------------------------
    async def _summarize_context(self) -> None:
        if not self.context_window or get_llm_response is None:
            return
        history = "\n".join(f"User: {u}\nJarvis: {a}" for u, a in self.context_window)
        prompt = (
            "Summarise this recent conversation, keeping key facts and preferences:\n\n"
            f"{history}\n\nSummary:"
        )
        try:
            summary = await get_llm_response(prompt, provider="gemini")
            if summary and isinstance(summary, str):
                self.summary_memory += f"\n{summary.strip()}"
                self.memory.set_user_preference("summary_memory", self.summary_memory)
                self.context_window.clear()
                logger.info("Context summarised and saved to long-term memory.")
        except Exception as e:
            logger.error("Error summarising context: %s", e)

    # ------------------------------------------------------------------
    #  Suggestions
    # ------------------------------------------------------------------
    async def show_suggestions(self) -> None:
        if SuggestionEngine is None:
            await self.speak("The suggestion system is not available right now.")
            return
        try:
            engine = SuggestionEngine(self.memory, self.predictor)
            suggestions = engine.generate_suggestions()
            if suggestions:
                await self.speak("Based on your activity, I have a few suggestions.")
                await asyncio.sleep(0.5)
                for suggestion in suggestions:
                    await self.speak(suggestion)
                    await asyncio.sleep(1)
            else:
                await self.speak("I don't have any new suggestions at the moment.")
        except Exception as e:
            logger.error("Error generating suggestions: %s", e)
            await self.speak("I couldn't generate any suggestions.")

    # ------------------------------------------------------------------
    #  Feature helpers
    # ------------------------------------------------------------------
    async def speak(self, text):
        if hasattr(self, "wake_detector"):
            self.wake_detector.speak_and_pause_tts(text)
        else:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()

    def _resolve_pronouns(self, text: str) -> str:
        t = text.lower()
        if "my favorite playlist" in t or "my playlist" in t:
            pl = self.memory.get_user_preference("spotify_playlist")
            if pl:
                return f"play {pl} on spotify"
        return text

    def _parse_command_nlp(self, text: str) -> Tuple[str, Dict[str, Any]]:
        text = " ".join(_ALIAS.get(w, w) for w in text.lower().split())  # <-- add this
        if not self.nlp:
            return "unknown", {}

        doc = self.nlp(text.lower())

        # Extract entities
        entities = {ent.label_: ent.text for ent in doc.ents}

        # Check for intent keywords
        text_lower = text.lower()
        for intent, keywords in self.intents.items():
            if any(keyword in text_lower for keyword in keywords):
                return intent, entities
        return "unknown", entities

    def _build_context_for_plugins(self) -> Dict[str, Any]:
        return {"recent": list(self.context_window), "summary_memory": self.summary_memory}

    async def remember_preference(self, text: str) -> str:
        m = re.search(r'my favorite playlist is\s+[\'"](.+?)[\'"]', text, re.I)
        if not m:
            return "I'm not sure what you want me to remember. Try: 'remember my favorite playlist is \"[name]\"'."
        pl = m.group(1).strip()
        if not pl:
            return "Please provide a valid playlist name."
        self.memory.set_user_preference("spotify_playlist", pl)
        return f"Okay, I'll remember that your favorite playlist is {pl}."

    async def set_reminder(self, text: str) -> str:
        m1 = re.search(r"remind me to\s+(.+?)(?=\s+at|\s+in|$)", text, re.I)
        m2 = re.search(r"(at|in)\s+(.+)", text, re.I)
        if not (m1 and m2):
            return "Please say 'remind me to [task] at [time]'."
        rem_text = m1.group(1).strip()
        time_str = m2.group(0).strip()
        run_date = dateparser.parse(time_str, settings={"PREFER_DATES_FROM": "future"})
        if not run_date:
            return f"I couldn't understand the time '{time_str}'."
        rid = self.memory.add_reminder(rem_text, run_date)
        if self.scheduler:
            try:
                self.scheduler.add_job(
                    self._trigger_reminder, "date", run_date=run_date, args=[rid, rem_text]
                )
            except Exception as e:
                logger.error("Failed to schedule reminder: %s", e)
                return f"Reminder created but scheduling failed: {e}"
        else:
            logger.warning("Scheduler not initialized when setting reminder")
            return "Reminder saved but scheduler not ready."
        return f"Okay, I will remind you to {rem_text} at {run_date.strftime('%I:%M %p')}."

    async def show_reminders(self) -> str:
        reminders = self.memory.get_reminders() or []
        if not reminders:
            return "You have no upcoming reminders."
        reply = "Here are your reminders: "
        for r in reminders:
            try:
                rd = datetime.fromisoformat(r["run_time"])
                reply += f"{r['text']} at {rd.strftime('%I:%M %p on %A')}. "
            except Exception:
                reply += f"{r['text']} at unknown time. "
        return reply

    def get_time(self) -> str:
        return f"The current time is {datetime.now().strftime('%I:%M %p')}."

    def get_date(self) -> str:
        return f"Today's date is {datetime.now().strftime('%B %d, %Y')}."

    async def take_screenshot(self) -> str:
        try:
            fname = f"screenshot_{datetime.now():%Y%m%d_%H%M%S}.png"
            pyautogui.screenshot(fname)
            logger.info("Screenshot saved: %s", fname)
            return f"Screenshot saved as {fname}."
        except FileNotFoundError:
            logger.error("Invalid path for screenshot")
            return "I couldn't save the screenshot (invalid path)."
        except Exception as e:
            logger.error("Screenshot failed: %s", e, exc_info=True)
            return "I couldn't take a screenshot."

    # ------------------------------------------------------------------
    #  Cross-platform app launcher (fixed)
    # ------------------------------------------------------------------
    def open_app(self, app_name: str) -> str:
        if not app_name:
            return "Which application?"
        match = self.app_manager.find_best_match(app_name)
        if not match:
            return f"I couldn't find an application named {app_name}."
        path = self.app_manager.apps[match]
        try:
            system = platform.system()
            if system == "Windows":
                if path.startswith("shell:appsFolder"):
                    subprocess.run(f'explorer.exe "{path}"', shell=True, check=True)
                else:
                    os.startfile(path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", path], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", path], check=True)
            self.memory.update_app_usage(match)
            return f"Opening {match.title()}."
        except subprocess.CalledProcessError as e:
            logger.error("Failed to open %s: %s", match, e)
            return f"Sorry, I couldn't open {match}."
        except Exception as e:
            logger.error("Unexpected error opening %s: %s", match, e)
            return f"An error occurred while opening {match}."

    def open_website(self, url: str) -> str:
        if not url or not isinstance(url, str):
            return "Please provide a valid URL."
        url = url.strip()
        if "." not in url or " " in url.split(".")[0]:
            search = f"https://www.google.com/search?q={url}"
            webbrowser.open(search)
            return f"Searching Google for '{url}'."
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            webbrowser.open(url)
            return f"Opening {url.split('//')[1].split('/')[0]}."
        except Exception as e:
            logger.error("Failed to open website: %s", e)
            return "I couldn't open that URL."

    # ------------------------------------------------------------------
    #  Suggestion handlers
    # ------------------------------------------------------------------
    def handle_suggestion_accept(self, data: Any) -> str:
        return str(data)

    def handle_suggestion_dismiss(self, data: Any) -> None:
        logger.info("Suggestion dismissed: %s", data)

    # ------------------------------------------------------------------
    #  Graceful shutdown
    # ------------------------------------------------------------------
    async def close(self) -> None:
        logger.info("Shutting down scheduler...")
        if self.scheduler:
            self.scheduler.shutdown()
        # NEW: close web-agent browser
        await self.web_agent.close()
        if close_sessions:
            await close_sessions()
        logger.info("CommandProcessor closed.")


async def get_llm_response(prompt: str, provider: Optional[str] = None) -> str:
    # use local model router via Ollama-compatible API
    import aiohttp

    from model_selector import pick

    model, system = pick(prompt)
    prompt = f"{system}\n\nUser: {prompt}\nAssistant:"

    # ------------------------------------------------------------------
    #  send to local router (Ollama) instead of cloud
    # ------------------------------------------------------------------
    async with aiohttp.ClientSession() as s:
        async with s.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=aiohttp.ClientTimeout(total=45),
        ) as r:
            r.raise_for_status()
            return (await r.json()).get("response", "").strip()
