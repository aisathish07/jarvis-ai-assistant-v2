import logging
import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("AI_Assistant.Config")


class Config:
    """Enhanced configuration class with better error handling and validation"""

    # ================== Core Configuration ==================
    LOCAL_ONLY = bool(os.getenv("LOCAL_ONLY", "").lower() in {"1", "true", "yes"})

    # ================== API Keys & Credentials ==================
    # All API keys should be loaded from environment variables
    OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY")
    SLACK_API_TOKEN = os.getenv("SLACK_API_TOKEN")

    # ================== Email Configuration ==================
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")
    EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "465"))

    # ================== TTS Configuration ==================
    PIPER_EXECUTABLE_PATH = os.getenv("PIPER_EXECUTABLE_PATH")

    # ================== LLM Configuration ==================
    LLM_PRIORITY = ["gemini", "ollama", "lm_studio"]

    # Gemini Models (validated and available)
    GEMINI_MODELS = [
        "gemini-1.0-pro",  # stable
        "gemini-1.0-flash",  # stable, cheaper
        "gemini-2.0-pro",  # new, may or may not be available
        "gemini-2.0-flash",
        "gemini-2.5-pro",  # experimental / AI Studio only
        "gemini-2.5-flash",
    ]

    # Local LLM Models
    LM_STUDIO_MODELS = [
        "lmstudio-community/Meta-Llama-3-8B-Instruct-Q4_K_M",
        "lmstudio-community/gemma-2-9b-it-q4_k_m",
    ]

    OLLAMA_MODELS = ["mistral:latest", "llama2:7b", "codellama:7b", "phi3:latest"]

    # API URLs
    LM_STUDIO_API_URL = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1")
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

    # Timeout configurations
    GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "15"))
    LM_STUDIO_TIMEOUT = int(os.getenv("LM_STUDIO_TIMEOUT", "30"))
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "45"))

    # Model selection strategy
    RANDOMIZE_MODELS = bool(os.getenv("RANDOMIZE_MODELS", "").lower() in {"1", "true", "yes"})

    # ================== TTS & STT Configuration ==================
    TTS_PRIORITY = ["elevenlabs", "piper", "gtts"]
    WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

    # ================== Audio Settings ==================
    SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))

    # ================== Paths ==================
    DB_FILE = os.getenv("DB_FILE", "assistant_memory.db")
    CACHE_DIR = os.getenv("CACHE_DIR", "cache")
    LOGS_DIR = os.getenv("LOGS_DIR", "logs")

    # ================== Web Agent Configuration ==================
    WEB_AGENT_ENABLED = bool(os.getenv("WEB_AGENT_ENABLED", "true").lower() in {"1", "true", "yes"})

    # Auto-detect system resources
    WEB_AGENT_MODE = os.getenv("WEB_AGENT_MODE", "auto")

    # Browser settings
    WEB_AGENT_BROWSER = os.getenv("WEB_AGENT_BROWSER", "chromium")
    WEB_AGENT_HEADLESS = bool(
        os.getenv("WEB_AGENT_HEADLESS", "true").lower() in {"1", "true", "yes"}
    )

    # Performance settings (auto-adjusted based on system)
    WEB_AGENT_AUTO_CLOSE_TIMEOUT = int(os.getenv("WEB_AGENT_AUTO_CLOSE_TIMEOUT", "300"))
    WEB_AGENT_MAX_MEMORY_MB = int(os.getenv("WEB_AGENT_MAX_MEMORY_MB", "600"))
    WEB_AGENT_MAX_CPU_PERCENT = int(os.getenv("WEB_AGENT_MAX_CPU_PERCENT", "50"))
    WEB_AGENT_MAX_CONCURRENT_TASKS = int(os.getenv("WEB_AGENT_MAX_CONCURRENT_TASKS", "2"))

    # Vision AI settings
    WEB_AGENT_VISION_ENABLED = bool(
        os.getenv("WEB_AGENT_VISION_ENABLED", "false").lower() in {"1", "true", "yes"}
    )
    WEB_AGENT_SCREENSHOT_QUALITY = os.getenv("WEB_AGENT_SCREENSHOT_QUALITY", "medium")

    # Browser window settings
    WEB_AGENT_WINDOW_WIDTH = int(os.getenv("WEB_AGENT_WINDOW_WIDTH", "1920"))
    WEB_AGENT_WINDOW_HEIGHT = int(os.getenv("WEB_AGENT_WINDOW_HEIGHT", "1080"))

    # User agent
    WEB_AGENT_USER_AGENT = os.getenv("WEB_AGENT_USER_AGENT", "auto")

    # ================== Performance Settings ==================
    # Memory management
    MAX_MEMORY_USAGE_MB = int(os.getenv("MAX_MEMORY_USAGE_MB", "1024"))
    MEMORY_CHECK_INTERVAL = int(os.getenv("MEMORY_CHECK_INTERVAL", "60"))

    # Threading
    MAX_WORKER_THREADS = int(os.getenv("MAX_WORKER_THREADS", "4"))

    # ================== Security Settings ==================
    # API key validation
    REQUIRE_API_KEY_VALIDATION = bool(
        os.getenv("REQUIRE_API_KEY_VALIDATION", "true").lower() in {"1", "true", "yes"}
    )

    # ================== Feature Flags ==================
    ENABLE_METRICS = bool(os.getenv("ENABLE_METRICS", "true").lower() in {"1", "true", "yes"})
    ENABLE_PREDICTIVE_SUGGESTIONS = bool(
        os.getenv("ENABLE_PREDICTIVE_SUGGESTIONS", "true").lower() in {"1", "true", "yes"}
    )
    ENABLE_AUTO_UPDATES = bool(
        os.getenv("ENABLE_AUTO_UPDATES", "false").lower() in {"1", "true", "yes"}
    )
    GAMING_MODE = bool(os.getenv("GAMING_MODE", "false").lower() in {"1", "true", "yes"})

    @classmethod
    def setup_directories(cls):
        """Setup required directories with error handling"""
        directories = [cls.CACHE_DIR, cls.LOGS_DIR, "skills", "backups", "temp"]

        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.debug(f"✅ Directory created/verified: {directory}")
            except Exception as e:
                logger.error(f"❌ Failed to create directory {directory}: {e}")
                raise

    @classmethod
    def validate_configuration(cls):
        """Validate configuration and log any issues"""
        issues = []

        # Check required API keys
        required_keys = {}

        for key_name, key_value in required_keys.items():
            if not key_value:
                if cls.LOCAL_ONLY and key_name == "GEMINI_API_KEY":
                    logger.info(f"ℹ️  {key_name} not set but LOCAL_ONLY mode enabled")
                else:
                    issues.append(f"Missing required API key: {key_name}")

        # Validate paths
        if cls.PIPER_EXECUTABLE_PATH and not os.path.exists(cls.PIPER_EXECUTABLE_PATH):
            issues.append(f"PIPER executable not found: {cls.PIPER_EXECUTABLE_PATH}")

        # Validate numeric configurations
        if cls.GEMINI_TIMEOUT <= 0:
            issues.append("GEMINI_TIMEOUT must be positive")

        if cls.MAX_MEMORY_USAGE_MB < 512:
            logger.warning("Low memory limit might cause performance issues")

        # Log validation results
        if issues:
            logger.error("❌ Configuration validation failed:")
            for issue in issues:
                logger.error(f"  • {issue}")
            return False
        else:
            logger.info("✅ Configuration validation passed")
            return True

    @classmethod
    def get_system_info(cls):
        """Get system information for optimization"""
        try:
            import psutil

            info = {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                "platform": sys.platform,
            }

            return info
        except ImportError:
            logger.warning("psutil not available for system info")
            return {}

    @classmethod
    def optimize_for_system(cls):
        """Optimize configuration based on system capabilities"""
        system_info = cls.get_system_info()

        if not system_info:
            logger.warning("Cannot optimize - system info not available")
            return

        memory_gb = system_info.get("memory_total_gb", 16)
        cpu_count = system_info.get("cpu_count", 8)

        # Optimize based on memory
        if memory_gb < 8:
            logger.info("🔋 Low memory system detected - applying optimizations")
            cls.WEB_AGENT_MAX_MEMORY_MB = min(cls.WEB_AGENT_MAX_MEMORY_MB, 300)
            cls.MAX_CONCURRENT_TASKS = 1
            cls.WEB_AGENT_VISION_ENABLED = False
            cls.MAX_WORKER_THREADS = min(cls.MAX_WORKER_THREADS, 2)
        elif memory_gb >= 16:
            logger.info("⚡ High memory system detected - enabling full features")
            cls.WEB_AGENT_MAX_MEMORY_MB = max(cls.WEB_AGENT_MAX_MEMORY_MB, 800)
            cls.MAX_CONCURRENT_TASKS = max(cls.MAX_CONCURRENT_TASKS, 3)
            cls.WEB_AGENT_VISION_ENABLED = True
            cls.MAX_WORKER_THREADS = max(cls.MAX_WORKER_THREADS, 4)

        # Optimize based on CPU
        if cpu_count < 4:
            cls.MAX_WORKER_THREADS = min(cls.MAX_WORKER_THREADS, 2)

        logger.info(f"📊 Optimized for system: {memory_gb:.1f}GB RAM, {cpu_count} CPU cores")


# Initialize configuration
try:
    Config.setup_directories()
    Config.validate_configuration()
    Config.optimize_for_system()
except Exception as e:
    logger.error(f"Failed to initialize configuration: {e}")
    raise