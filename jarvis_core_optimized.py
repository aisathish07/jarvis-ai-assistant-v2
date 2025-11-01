"""
═══════════════════════════════════════════════════════════════════════════════
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
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import logging
import time
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor

import psutil

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import turbo manager
try:
    from jarvis_turbo_manager import OptimizedTurboManager, TurboProfile
    TURBO_AVAILABLE = True
except ImportError:
    TURBO_AVAILABLE = False
    logging.warning("Turbo manager not available")

# Import skill system
try:
    from jarvis_skills import SkillManager
    SKILLS_AVAILABLE = True
except ImportError:
    SKILLS_AVAILABLE = False
    logging.warning("Skill system not available")

# Import app control
try:
    from jarvis_app_control import AppControlIntegration
    APP_CONTROL_AVAILABLE = True
except ImportError:
    APP_CONTROL_AVAILABLE = False
    logging.warning("App control not available")

# Import scheduler
try:
    from jarvis_scheduler import ReminderScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    logging.warning("Scheduler not available")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("Jarvis.Core")

# ============================================================================
# OPTIMIZED MEMORY MANAGER
# ============================================================================

class OptimizedMemoryManager:
    """Lightweight memory management without SQLite overhead"""
    
    def __init__(self, db_path: str = "jarvis_memory.db"):
        self.conversations: List[Tuple[str, str, str]] = []  # (user, assistant, model)
        self.max_conversations = 10
        logger.debug("Memory manager initialized (in-memory mode)")
    
    async def save(self, user: str, assistant: str, model: str = "auto"):
        """Save conversation to memory"""
        # Truncate for performance
        user = user[:200] + "..." if len(user) > 200 else user
        assistant = assistant[:300] + "..." if len(assistant) > 300 else assistant
        
        self.conversations.append((user, assistant, model))
        
        # Maintain size limit
        if len(self.conversations) > self.max_conversations:
            self.conversations.pop(0)
    
    # In OptimizedMemoryManager class, add:
    async def get_recent(self, limit: int = 3) -> List[Tuple[str, str]]:
        """Get recent conversations"""
        if not self.conversations:
            return []

        recent = self.conversations[-limit:]
        return [(user, assistant) for user, assistant, _ in recent]

    async def cleanup(self):
        """Cleanup memory"""
        self.conversations.clear()
        logger.debug("Memory cleaned")

# ============================================================================
# OPTIMIZED VOICE IO
# ============================================================================

class OptimizedVoiceIO:
    """Non-blocking TTS with smart queue management"""
    
    def __init__(self, rate: int = 185, volume: float = 0.9, enabled: bool = True):
        self.rate = rate
        self.volume = volume
        self.enabled = enabled
        self._engine = None
        self._queue = asyncio.Queue(maxsize=3)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="TTS")
        self._initialized = False
        self._speaking = False
        
        if enabled:
            asyncio.create_task(self._init())
            asyncio.create_task(self._speaker_loop())
    
    async def _init(self):
        """Initialize TTS engine in background"""
        try:
            def _create():
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
                return engine
            
            self._engine = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                _create
            )
            self._initialized = True
            logger.info("🔊 TTS engine ready")
        except Exception as e:
            logger.warning(f"TTS unavailable: {e}")
            self.enabled = False
            self._initialized = False
    
    async def speak(self, text: str):
        """Queue text for speaking (non-blocking)"""
        if not self.enabled or not text:
            return
        
        # Truncate long text
        if len(text) > 200:
            text = text[:197] + "..."
        
        try:
            # Non-blocking put
            self._queue.put_nowait(text)
        except asyncio.QueueFull:
            # Skip if queue full (prevents blocking)
            logger.debug("TTS queue full, skipping")
    
    async def _speaker_loop(self):
        """Background TTS processing loop"""
        while True:
            try:
                text = await self._queue.get()
                if text and self._engine:
                    self._speaking = True
                    await asyncio.get_event_loop().run_in_executor(
                        self._executor,
                        self._speak_blocking,
                        text
                    )
                    self._speaking = False
            except Exception as e:
                logger.error(f"TTS error: {e}")
                self._speaking = False
    
    def _speak_blocking(self, text: str):
        """Blocking TTS call (runs in executor)"""
        try:
            if self._engine:
                self._engine.say(text)
                self._engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS speak error: {e}")
    
    def toggle(self):
        """Toggle voice on/off"""
        self.enabled = not self.enabled
        return self.enabled

# ============================================================================
# UNIFIED JARVIS CORE
# ============================================================================

class JarvisOptimizedCore:
    """Complete JARVIS system with all components integrated"""
    
    def __init__(self, enable_voice: bool = True):
        # Core systems
        self.memory = OptimizedMemoryManager()
        self.voice = OptimizedVoiceIO(enabled=enable_voice)
        
        # Turbo manager
        if TURBO_AVAILABLE:
            self.turbo = OptimizedTurboManager()
            self._has_turbo = True
        else:
            self.turbo = None
            self._has_turbo = False
        
        # Skill system
        if SKILLS_AVAILABLE:
            self.skill_manager = SkillManager()
            self._has_skills = True
        else:
            self.skill_manager = None
            self._has_skills = False
        
        # App control
        if APP_CONTROL_AVAILABLE:
            self.app_control = AppControlIntegration()
            self._has_app_control = True
        else:
            self.app_control = None
            self._has_app_control = False
        
        # Scheduler
        if SCHEDULER_AVAILABLE:
            self.reminder_scheduler = ReminderScheduler()
            self.reminder_scheduler.set_callback(self._on_reminder)
            self._has_scheduler = True
        else:
            self.reminder_scheduler = None
            self._has_scheduler = False
        
        # Statistics
        self.stats = {
            "total_queries": 0,
            "total_time": 0.0,
            "skill_usage": {},
            "app_commands": 0,
            "ai_queries": 0
        }
        
        # Optimization
        self._optimize_cpu()
    
    def _optimize_cpu(self):
        """Optimize CPU for i5-13th gen (P-cores)"""
        try:
            p = psutil.Process()
            cpu_count = psutil.cpu_count()
            # Use P-cores (0-7 on i5-13th gen)
            p.cpu_affinity(list(range(min(8, cpu_count))))
            logger.info("✅ CPU affinity optimized for P-cores")
        except Exception as e:
            logger.debug(f"CPU optimization skipped: {e}")
    
    async def initialize(self):
        """Initialize all JARVIS systems"""
        logger.info("🚀 Initializing JARVIS Optimized Core")
        
        # Initialize turbo manager
        if self._has_turbo:
            await self.turbo.initialize()
            logger.info("✅ Turbo manager ready")
        
        # Load skills
        if self._has_skills:
            self.skill_manager.load_skills()
            skills = list(self.skill_manager.skills.keys())
            logger.info(f"✅ Loaded {len(skills)} skills: {', '.join(skills)}")
        
        # Start scheduler
        if self._has_scheduler:
            self.reminder_scheduler.start()
            logger.info("✅ Scheduler started")
        
        # Log available features
        features = []
        if self._has_turbo:
            features.append("AI Models")
        if self._has_skills:
            features.append("Skills")
        if self._has_app_control:
            features.append("App Control")
        if self._has_scheduler:
            features.append("Scheduler")
        if self.voice.enabled:
            features.append("Voice")
        
        logger.info(f"🎯 Active features: {', '.join(features)}")
        logger.info("✅ JARVIS Ready!")
    
    def _on_reminder(self, message: str):
        """Callback for reminder notifications"""
        logger.info(f"⏰ Reminder: {message}")
        asyncio.create_task(self.voice.speak(message))
    
    async def process_query(
        self,
        user_input: str,
        speak: bool = True,
        model: Optional[str] = None
    ) -> str:
        """Main query processing pipeline"""
        start_time = time.perf_counter()
        self.stats["total_queries"] += 1
        
        logger.info(f"📥 Query #{self.stats['total_queries']}: {user_input[:50]}...")
        
        # Step 1: Try skills first
        if self._has_skills:
            skill_response = await self.skill_manager.handle(user_input, self)
            try:
                skill_response = await self.skill_manager.handle(user_input, self)
                if skill_response:
                    # Track skill usage
                    skill_name = self._identify_skill(user_input)
                    self.stats["skill_usage"][skill_name] = \
                        self.stats["skill_usage"].get(skill_name, 0) + 1
                    
                    logger.info(f"🎯 Handled by skill: {skill_name}")
                    
                    if speak:
                        await self.voice.speak(skill_response)
                    
                    elapsed = time.perf_counter() - start_time
                    self.stats["total_time"] += elapsed
                    logger.info(f"⚡ Response time: {elapsed:.2f}s")
                    
                    return skill_response
            except Exception as e:
                logger.error(f"Skill error: {e}")
        
        # Step 2: Try app control
        if self._has_app_control:
            try:
                app_response = await asyncio.to_thread(
                    self.app_control.parse_command,
                    user_input
                )
                if app_response and "Could not perform" not in app_response:
                    self.stats["app_commands"] += 1
                    logger.info(f"🖥️ Handled by app control")
                    
                    if speak:
                        await self.voice.speak(app_response)
                    
                    elapsed = time.perf_counter() - start_time
                    self.stats["total_time"] += elapsed
                    
                    return app_response
            except Exception as e:
                logger.error(f"App control error: {e}")
        
        # Step 3: Try scheduler
        if self._has_scheduler and any(kw in user_input.lower() 
                                      for kw in ["remind", "reminder", "schedule"]):
            try:
                # Import scheduler integration if available
                from jarvis_scheduler import SchedulerIntegration
                scheduler_int = SchedulerIntegration(self.reminder_scheduler)
                scheduler_response = scheduler_int.parse_command(user_input)
                
                if scheduler_response and "Could not understand" not in scheduler_response:
                    logger.info(f"⏰ Handled by scheduler")
                    
                    if speak:
                        await self.voice.speak(scheduler_response)
                    
                    elapsed = time.perf_counter() - start_time
                    self.stats["total_time"] += elapsed
                    
                    return scheduler_response
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
        
        # Step 4: Fall back to AI
        if self._has_turbo:
            ai_response = await self._ai_query(user_input, model)
            self.stats["ai_queries"] += 1
            
            # Save to memory
            current_model = self.turbo.model_cache.current_model if hasattr(
                self.turbo, 'model_cache') else "auto"
            await self.memory.save(user_input, ai_response, current_model)
            
            if speak:
                await self.voice.speak(ai_response)
            
            elapsed = time.perf_counter() - start_time
            self.stats["total_time"] += elapsed
            logger.info(f"⚡ AI response time: {elapsed:.2f}s")
            
            return ai_response
        else:
            # No AI available - provide helpful message
            response = ("I can help with specific tasks like app control, file management, "
                       "weather, system info, and scheduling. What would you like to do?")
            
            if speak:
                await self.voice.speak(response)
            
            return response
    
    def _identify_skill(self, text: str) -> str:
        """Identify which skill handled the query"""
        if not self._has_skills:
            return "unknown"
        
        text_lower = text.lower()
        for skill_name, skill in self.skill_manager.skills.items():
            if any(kw in text_lower for kw in skill.keywords):
                return skill_name
        
        return "unknown"
    
    async def _ai_query(self, user_input: str, model: Optional[str] = None) -> str:
        """Query AI model with context"""
        # Get conversation context
        context = await self.memory.get_recent(2)
        
        # Build prompt with context
        prompt = self._build_prompt(user_input, context)
        
        # Query with turbo
        response = await self.turbo.query_with_turbo(
            prompt=prompt,
            model=model,
            system="You are JARVIS, a helpful AI assistant. Be concise and professional."
        )
        
        return response
    
    def _build_prompt(self, user: str, context: List[Tuple[str, str]]) -> str:
        """Build optimized prompt with context"""
        parts = []
        
        # Add only recent context (last exchange)
        if context:
            last_user, last_assistant = context[-1]
            # Only add if not too long
            if len(last_user) < 100 and len(last_assistant) < 150:
                parts.append(f"Previous:\nUser: {last_user}\nAssistant: {last_assistant}\n")
        
        parts.append(f"Current:\nUser: {user}\nAssistant:")
        return "\n".join(parts)
    
    async def handle_user_input(self, text: str) -> str:
        """Convenience method for handling user input"""
        return await self.process_query(text, speak=True)
    
    def get_status(self) -> Dict:
        """Get comprehensive status"""
        status = {
            "queries": self.stats["total_queries"],
            "avg_time": self.stats["total_time"] / max(self.stats["total_queries"], 1),
            "voice_enabled": self.voice.enabled,
            "features": {
                "turbo": self._has_turbo,
                "skills": self._has_skills,
                "app_control": self._has_app_control,
                "scheduler": self._has_scheduler
            },
            "usage": {
                "ai_queries": self.stats["ai_queries"],
                "app_commands": self.stats["app_commands"],
                "skill_usage": dict(self.stats["skill_usage"])
            }
        }
        
        # Add turbo status if available
        if self._has_turbo:
            turbo_status = self.turbo.get_status()
            status["turbo"] = {
                "profile": turbo_status["profile"]["name"],
                "vram": turbo_status["system"]["vram"],
                "current_model": turbo_status["cache"].get("current_model")
            }
        
        return status
    
    def print_status(self):
        """Print formatted status"""
        status = self.get_status()
        
        print("\n" + "="*60)
        print("🤖 JARVIS STATUS")
        print("="*60)
        
        print(f"\n📊 Performance:")
        print(f"   Queries: {status['queries']}")
        print(f"   Avg Time: {status['avg_time']:.2f}s")
        print(f"   Voice: {'🟢 Enabled' if status['voice_enabled'] else '🔴 Disabled'}")
        
        print(f"\n🎯 Features:")
        for feature, enabled in status['features'].items():
            icon = "✅" if enabled else "❌"
            print(f"   {icon} {feature.replace('_', ' ').title()}")
        
        print(f"\n📈 Usage:")
        print(f"   AI Queries: {status['usage']['ai_queries']}")
        print(f"   App Commands: {status['usage']['app_commands']}")
        if status['usage']['skill_usage']:
            print(f"   Skills: {status['usage']['skill_usage']}")
        
        if self._has_turbo and 'turbo' in status:
            print(f"\n⚡ Turbo:")
            print(f"   Profile: {status['turbo']['profile']}")
            vram = status['turbo']['vram']
            print(f"   VRAM: {vram['used']:.1f}GB / {vram['total']:.1f}GB")
            if status['turbo']['current_model']:
                print(f"   Model: {status['turbo']['current_model']}")
        
        print("="*60 + "\n")
    
    async def cleanup(self):
        """Cleanup all systems"""
        logger.info("🧹 Cleaning up JARVIS...")
        
        if self._has_turbo:
            await self.turbo.shutdown()
        
        if self._has_scheduler:
            self.reminder_scheduler.stop()
        
        await self.memory.cleanup()
        
        logger.info("✅ Cleanup complete")

# ============================================================================
# COMPATIBILITY FUNCTIONS
# ============================================================================

async def create_jarvis(enable_voice: bool = True):
    """Create and initialize JARVIS instance"""
    jarvis = JarvisOptimizedCore(enable_voice=enable_voice)
    await jarvis.initialize()
    return jarvis

async def quick_query_mode(question: str, profile: str = "turbo_3050"):
    """Quick query without voice"""
    jarvis = await create_jarvis(enable_voice=False)
    try:
        # Switch profile if turbo available
        if jarvis._has_turbo and profile:
            try:
                await jarvis.turbo.switch_profile(TurboProfile(profile))
            except:
                pass
        
        return await jarvis.process_query(question, speak=False)
    finally:
        await jarvis.cleanup()

# ============================================================================
# INTERACTIVE MODE
# ============================================================================

async def interactive_mode():
    """Interactive JARVIS experience"""
    jarvis = await create_jarvis()
    
    print("\n" + "="*60)
    print("🤖 JARVIS - Optimized Core")
    print("="*60)
    print("\n💡 Commands:")
    print("  /status   - Show system status")
    print("  /voice    - Toggle voice output")
    print("  /exit     - Shutdown JARVIS")
    
    if jarvis._has_turbo:
        print("\nProfile Commands:")
        print("  /eco      - Eco mode (fastest)")
        print("  /balanced - Balanced mode")
        print("  /coding   - Coding mode")
        print("  /creative - Creative mode")
        print("  /turbo    - RTX 3050 optimized")
    
    print("="*60 + "\n")
    
    try:
        while True:
            user_input = input("You> ").strip()
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input[1:].lower()
                
                if cmd in ["exit", "quit"]:
                    print("\n\"Shutting down. Goodbye!\"\n")
                    break
                
                elif cmd == "status":
                    jarvis.print_status()
                
                elif cmd == "voice":
                    enabled = jarvis.voice.toggle()
                    status = "enabled" if enabled else "disabled"
                    print(f"\n✅ Voice {status}\n")
                
                elif jarvis._has_turbo:
                    profile_map = {
                        "eco": TurboProfile.ECO,
                        "balanced": TurboProfile.BALANCED,
                        "coding": TurboProfile.CODING,
                        "creative": TurboProfile.CREATIVE,
                        "turbo": TurboProfile.TURBO_3050
                    }
                    
                    if cmd in profile_map:
                        await jarvis.turbo.switch_profile(profile_map[cmd])
                        print(f"\n✅ Switched to {cmd} mode\n")
                    else:
                        print(f"\n❌ Unknown command: /{cmd}\n")
                else:
                    print(f"\n❌ Unknown command: /{cmd}\n")
                
                continue
            
            # Process query
            print("🤔 Processing...")
            response = await jarvis.handle_user_input(user_input)
            print(f"\n🤖 JARVIS> {response}\n")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted!\n")
    finally:
        await jarvis.cleanup()
        print("👋 Systems offline.\n")

# ============================================================================
# DEMO MODE
# ============================================================================

async def demo_mode():
    """Demo mode showcasing features"""
    jarvis = await create_jarvis(enable_voice=False)
    
    print("\n🚀 JARVIS Demo Mode\n")
    
    demos = [
        "Hello!",
        "What can you do?",
        "What's the weather like?",
        "Write a Python hello world"
    ]
    
    for query in demos:
        print(f"You: {query}")
        response = await jarvis.process_query(query, speak=False)
        print(f"JARVIS: {response}\n")
        await asyncio.sleep(1)
    
    print("📊 Final Status:")
    jarvis.print_status()
    
    await jarvis.cleanup()

# ============================================================================
# COMPATIBILITY CLASS
# ============================================================================

# Keep old class name for backward compatibility
JarvisIntegrated = JarvisOptimizedCore
JarvisIntegratedCore = JarvisOptimizedCore

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "demo":
            asyncio.run(demo_mode())
        elif command == "query" and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            result = asyncio.run(quick_query_mode(query))
            print(f"\n{result}\n")
        else:
            print("Usage: python jarvis_core_optimized.py [demo|query <text>]")
    else:
        asyncio.run(interactive_mode())