
FILE: jarvis_core_optimized.py
DESCRIPTION: COMPLETE UNIFIED JARVIS CORE - All systems integrated
OPTIMIZED FOR: i5-13th Gen + RTX 3050 4GB + 16GB RAM
FEATURES:
- Turbo manager integration
- Skill system
- App control
- Scheduler/reminders
- Non-blocking TTS
- Optimized memory management
- Context summarization


import asyncio
import logging
import time
import os
import sys
from typing import List, Optional, Tuple, Dict

# Add current directory to path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Module Imports with availability checks ---
try:
    from jarvis_turbo_manager import OptimizedTurboManager, TurboProfile
    TURBO_AVAILABLE = True
except ImportError:
    TURBO_AVAILABLE = False

try:
    from jarvis_skills import SkillManager
    SKILLS_AVAILABLE = True
except ImportError:
    SKILLS_AVAILABLE = False

try:
    from jarvis_app_control import AppControlIntegration
    APP_CONTROL_AVAILABLE = True
except ImportError:
    APP_CONTROL_AVAILABLE = False

try:
    from jarvis_scheduler import ReminderScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

try:
    from jarvis_app_scanner import AppManager
    APP_SCANNER_AVAILABLE = True
except ImportError:
    APP_SCANNER_AVAILABLE = False

try:
    from jarvis_app_controller import AppController
    APP_CONTROLLER_AVAILABLE = True
except ImportError:
    APP_CONTROLLER_AVAILABLE = False

try:
    from jarvis_web_agent import WebAgent
    WEB_AGENT_AVAILABLE = True
except ImportError:
    WEB_AGENT_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("Jarvis.Core")

# ============================================================================
# OPTIMIZED MEMORY MANAGER
# ============================================================================

class OptimizedMemoryManager:
    """Lightweight in-memory management for conversations and summaries."""
    
    def __init__(self):
        self.conversations: List[Tuple[str, str, str]] = []  # (user, assistant, model)
        self.summary_history: List[str] = []
        self.current_summary: Optional[str] = None
        self.max_conversations = 10
        logger.debug("Memory manager initialized (in-memory mode)")
    
    async def save(self, user: str, assistant: str, model: str = "auto"):
        """Save conversation to memory."""
        user = user[:200] + "..." if len(user) > 200 else user
        assistant = assistant[:300] + "..." if len(assistant) > 300 else assistant
        self.conversations.append((user, assistant, model))
        if len(self.conversations) > self.max_conversations:
            self.conversations.pop(0)

    async def save_summary(self, summary: str):
        """Save a conversation summary."""
        self.current_summary = summary
        self.summary_history.append(summary)
        if len(self.summary_history) > 5:
            self.summary_history.pop(0)
        logger.info(f"📝 New context summary stored: {summary[:70]}...")

    async def get_summary(self) -> Optional[str]:
        """Get the current conversation summary."""
        return self.current_summary
    
    async def get_recent(self, limit: int = 3) -> List[Tuple[str, str]]:
        """Get recent conversations."""
        if not self.conversations:
            return []
        recent = self.conversations[-limit:]
        return [(user, assistant) for user, assistant, _ in recent]

    async def cleanup(self):
        """Cleanup memory."""
        self.conversations.clear()
        self.summary_history.clear()
        self.current_summary = None
        logger.debug("Memory cleaned")

# ============================================================================
# UNIFIED JARVIS CORE
# ============================================================================

class JarvisOptimizedCore:
    """Complete JARVIS system with all components integrated."""
    
    def __init__(self, enable_voice: bool = True):
        self.memory = OptimizedMemoryManager()
        # self.voice = OptimizedVoiceIO(enabled=enable_voice) # Voice IO can be added back here
        
        self.turbo = OptimizedTurboManager() if TURBO_AVAILABLE else None
        self.skill_manager = SkillManager() if SKILLS_AVAILABLE else None
        self.app_control = AppControlIntegration() if APP_CONTROL_AVAILABLE else None
        self.reminder_scheduler = ReminderScheduler() if SCHEDULER_AVAILABLE else None
        self.app_scanner = AppManager() if APP_SCANNER_AVAILABLE else None
        self.app_controller = AppController() if APP_CONTROLLER_AVAILABLE else None
        self.web_agent = WebAgent() if WEB_AGENT_AVAILABLE else None
        if self.reminder_scheduler:
            self.reminder_scheduler.set_callback(self._on_reminder)
        
        self.stats = {"total_queries": 0, "total_time": 0.0, "skill_usage": {}, "app_commands": 0, "ai_queries": 0}
        self.queries_since_last_summary = 0
    
    async def initialize(self):
        """Initialize all JARVIS systems."""
        logger.info("🚀 Initializing JARVIS Optimized Core")
        if self.turbo:
            await self.turbo.initialize()
            logger.info("✅ Turbo manager ready")
        if self.skill_manager:
            self.skill_manager.load_skills()
            logger.info(f"✅ Loaded {len(self.skill_manager.skills)} skills")
        if self.reminder_scheduler:
            self.reminder_scheduler.start()
            logger.info("✅ Scheduler started")
        logger.info("✅ JARVIS Ready!")
    
    def _on_reminder(self, message: str):
        """Callback for reminder notifications."""
        logger.info(f"⏰ Reminder: {message}")
        # asyncio.create_task(self.voice.speak(message))

    async def _create_and_store_summary(self):
        """Generate and store a summary of recent conversation."""
        if not self.turbo:
            return

        recent_conversations = await self.memory.get_recent(self.memory.max_conversations)
        if len(recent_conversations) < 3:
            return

        conversation_text = "\n".join([f"User: {u}\nAssistant: {a}" for u, a in recent_conversations])
        summary_prompt = f"Summarize the key points of this conversation in one paragraph:\n\n{conversation_text}"

        try:
            summary_stream = self.turbo.query_with_turbo(prompt=summary_prompt, model="gemma:2b", system="You are a summarization AI.", stream=True)
            summary_content = "".join([chunk['message']['content'] async for chunk in summary_stream if 'message' in chunk])

            if summary_content:
                await self.memory.save_summary(summary_content)
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")

    def _build_prompt(self, user: str, context: List[Tuple[str, str]], summary: Optional[str]) -> str:
        """Build optimized prompt with context and summary."""
        parts = []
        if summary:
            parts.append(f"This is a summary of the conversation so far: {summary}\n")
        if context:
            parts.append("This was the most recent exchange:")
            last_user, last_assistant = context[-1]
            parts.append(f"User: {last_user}\nAssistant: {last_assistant}\n")
        parts.append(f"Now, answer the user's current prompt: {user}")
        return "\n".join(parts)

    async def open_application(self, app_name: str) -> str:
        """Open an application."""
        if not self.app_scanner:
            return "Application scanner not available."

        match = self.app_scanner.find_best_match(app_name)
        if not match:
            return f"Application '{app_name}' not found."

        try:
            os.startfile(self.app_scanner.apps[match])
            return f"Opening {match}..."
        except Exception as e:
            logger.error(f"Failed to open application {match}: {e}")
            return f"Failed to open application {match}."

    async def web_search(self, query: str) -> str:
        """Perform a web search."""
        if not self.web_agent:
            return "Web agent not available."

        results = await self.web_agent.search(query)
        if not results:
            return f"I couldn't find anything about {query}."

        response = f"Here's what I found about {query}:\n"
        for result in results:
            response += f"- {result['title']}: {result['url']}\n"
        return response

    async def execute_app_command(self, app_name: str, command: str, params: dict) -> str:
        """Execute a command for an application."""
        if not self.app_controller:
            return "Application controller not available."

        return self.app_controller.execute_command(app_name, command, **params)

    async def _ai_query(self, user_input: str, model: Optional[str] = None):
        """Query AI model with context and stream the response."""
        context = await self.memory.get_recent(1)
        summary = await self.memory.get_summary()
        prompt = self._build_prompt(user_input, context, summary)
        
        async for chunk in self.turbo.query_with_turbo(prompt=prompt, model=model, system="You are JARVIS, a helpful AI assistant.", stream=True):
            yield chunk

    async def process_query(self, user_input: str, speak: bool = True, model: Optional[str] = None, stream: bool = False) -> str:
        """Main query processing pipeline."""
        start_time = time.perf_counter()
        self.stats["total_queries"] += 1
        logger.info(f"📥 Query #{self.stats['total_queries']}: {user_input[:50]}...")

        # Periodically summarize context
        if self.queries_since_last_summary >= 5:
            await self._create_and_store_summary()
            self.queries_since_last_summary = 0
        else:
            self.queries_since_last_summary += 1

        # Step 1: Check for local commands
        if user_input.lower().startswith("open "):
            app_name = user_input[5:].strip()
            return await self.open_application(app_name)
        
        if user_input.lower().startswith("search for "):
            query = user_input[11:].strip()
            return await self.web_search(query)

        # Step 2: Check for app commands
        parts = user_input.lower().split()
        if len(parts) >= 2 and self.app_controller:
            app_name = parts[0]
            command = parts[1]
            if app_name in self.app_controller.list_supported_apps() and command in self.app_controller.list_app_commands(app_name):
                params = {}
                if len(parts) > 2:
                    # This is a simple parsing, assuming the rest of the input is a single parameter
                    params["query"] = " ".join(parts[2:])
                    params["text"] = " ".join(parts[2:])
                    params["message"] = " ".join(parts[2:])
                    params["contact"] = " ".join(parts[2:])
                    params["url"] = " ".join(parts[2:])
                    params["filename"] = " ".join(parts[2:])
                return await self.execute_app_command(app_name, command, params)

        # Step 3: Try skills first
        if self.skill_manager:
            skill_response = await self.skill_manager.handle(user_input, self)
            if skill_response:
                logger.info("🎯 Handled by skill.")
                print(f"\n🤖 JARVIS> {skill_response}\n")
                # if speak: await self.voice.speak(skill_response)
                return skill_response

        # Step 4: Fall back to AI
        if self.turbo:
            print("\n🤖 JARVIS> ", end="")
            full_response = ""
            try:
                async for chunk in self._ai_query(user_input, model):
                    content = chunk.get('message', {}).get('content', '')
                    print(content, end="", flush=True)
                    full_response += content
                print("\n")
            except Exception as e:
                logger.error(f"AI stream error: {e}")
                full_response = "Sorry, I encountered an error."
                print(full_response)
            
            await self.memory.save(user_input, full_response, "ai_query")
            # if speak: await self.voice.speak(full_response)
            return full_response
        
        return "No AI or skills available to handle the request."

    async def cleanup(self):
        """Cleanup all systems."""
        logger.info("🧹 Cleaning up JARVIS...")
        if self.turbo:
            await self.turbo.shutdown()
        if self.reminder_scheduler:
            self.reminder_scheduler.stop()
        if self.web_agent:
            await self.web_agent.close()
        await self.memory.cleanup()
        logger.info("✅ Cleanup complete")

# ============================================================================
# COMPATIBILITY & LAUNCHER FUNCTIONS
# ============================================================================

async def create_jarvis(enable_voice: bool = True):
    """Create and initialize JARVIS instance."""
    jarvis = JarvisOptimizedCore(enable_voice=enable_voice)
    await jarvis.initialize()
    return jarvis

async def interactive_mode():
    """Interactive JARVIS experience."""
    jarvis = await create_jarvis()
    print("\n" + "="*60)
    print("🤖 JARVIS - Optimized Core")
    print("="*60)
    print("\n💡 Type /exit to quit, /status for system info.")
    print("="*60 + "\n")
    
    try:
        while True:
            user_input = input("You> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["/exit", "/quit"]:
                break
            
            print("🤔 Processing...")
            await jarvis.process_query(user_input, stream=True)
    except KeyboardInterrupt:
        print("\n\nInterrupted!")
    finally:
        await jarvis.cleanup()
        print("👋 Systems offline.\n")

async def demo_.mode():
    """Demo mode showcasing features."""
    jarvis = await create_jarvis(enable_voice=False)
    print("\n🚀 JARVIS Demo Mode\n")
    demos = ["Hello!", "What can you do?", "What's the weather like?", "Write a Python hello world"]
    for query in demos:
        print(f"You: {query}")
        response = await jarvis.process_query(query, speak=False)
        print(f"JARVIS: {response}\n")
        await asyncio.sleep(1)
    await jarvis.cleanup()

# Keep old class name for backward compatibility
JarvisIntegrated = JarvisOptimizedCore
