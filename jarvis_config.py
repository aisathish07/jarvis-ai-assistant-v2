"""
═══════════════════════════════════════════════════════════════════════════════
FILE: jarvis_config.py
DESCRIPTION: Configuration management system for JARVIS - OPTIMIZED FOR RTX 3050
USAGE: python jarvis_config.py edit     # Interactive editor
       python jarvis_config.py show     # Show current config
DEPENDENCIES: json, dataclasses
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import logging
from pathlib import Path
from typing import Any
from dataclasses import dataclass, asdict

logger = logging.getLogger("Jarvis.Config")


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION DATACLASSES - OPTIMIZED FOR RTX 3050
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class VoiceConfig:
    """Voice-related settings optimized for performance"""
    tts_rate: int = 175           # Words per minute (speech speed)
    tts_volume: float = 0.9       # Volume level (0.0 to 1.0)
    stt_model: str = "base"       # Whisper model: tiny, base, small, medium
    wake_word_enabled: bool = False
    wake_word: str = "jarvis"
    hotkey: str = "ctrl+space"
    auto_speak: bool = True       # Automatically speak responses
    max_speech_length: int = 200  # Limit speech length for performance


@dataclass
class ModelConfig:
    """AI model preferences optimized for RTX 3050"""
    default_model: str = "phi3:3.8b"
    coding_model: str = "deepseek-coder:6.7b"
    creative_model: str = "phi3:3.8b"
    fast_model: str = "gemma:2b"
    lightweight_model: str = "gemma:2b"
    temperature: float = 0.7      # Creativity level (0.0-1.0)
    top_p: float = 0.9
    max_tokens: int = 2048        # Maximum response length
    max_context_length: int = 4000  # Limit context to save VRAM


@dataclass
class AppConfig:
    """Application behavior settings"""
    startup_enabled: bool = False
    system_tray_enabled: bool = True
    gui_theme: str = "dark"       # dark or light
    log_level: str = "INFO"       # DEBUG, INFO, WARNING, ERROR
    memory_limit: int = 50        # Reduced for performance
    auto_cleanup: bool = True
    enable_turbo_mode: bool = True  # Use optimized mode


@dataclass
class WebConfig:
    """Web agent settings"""
    headless_browser: bool = True
    browser_timeout: int = 30     # seconds
    max_search_results: int = 5
    enable_web_agent: bool = False  # Disabled by default for performance


@dataclass
class PerformanceConfig:
    """RTX 3050 performance optimizations"""
    vram_limit_gb: float = 3.8    # Leave 200MB buffer
    max_loaded_models: int = 2
    auto_unload_seconds: int = 120
    pre_warm_models: bool = True
    emergency_cleanup: bool = True
    process_priority: str = "below_normal"


@dataclass
class JarvisConfig:
    """Complete JARVIS configuration optimized for RTX 3050"""
    voice: VoiceConfig
    models: ModelConfig
    app: AppConfig
    web: WebConfig
    performance: PerformanceConfig
    
    def __init__(self):
        self.voice = VoiceConfig()
        self.models = ModelConfig()
        self.app = AppConfig()
        self.web = WebConfig()
        self.performance = PerformanceConfig()


# ═══════════════════════════════════════════════════════════════════════════
# CONFIG MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class ConfigManager:
    """Manage configuration persistence"""
    
    def __init__(self, config_file: str = "jarvis_config.json"):
        self.config_file = Path(config_file)
        self.config = JarvisConfig()
        self.load()
    
    def load(self) -> bool:
        """Load configuration from file"""
        if not self.config_file.exists():
            logger.info("No config file found, creating optimized configuration")
            self.save()
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Load each section
            if 'voice' in data:
                self.config.voice = VoiceConfig(**data['voice'])
            if 'models' in data:
                self.config.models = ModelConfig(**data['models'])
            if 'app' in data:
                self.config.app = AppConfig(**data['app'])
            if 'web' in data:
                self.config.web = WebConfig(**data['web'])
            if 'performance' in data:
                self.config.performance = PerformanceConfig(**data['performance'])
            
            logger.info(f"Configuration loaded from {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False
    
    def save(self) -> bool:
        """Save configuration to file"""
        try:
            data = {
                'voice': asdict(self.config.voice),
                'models': asdict(self.config.models),
                'app': asdict(self.config.app),
                'web': asdict(self.config.web),
                'performance': asdict(self.config.performance)
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a specific configuration value"""
        try:
            section_obj = getattr(self.config, section)
            return getattr(section_obj, key, default)
        except:
            return default
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """Set a specific configuration value"""
        try:
            section_obj = getattr(self.config, section)
            setattr(section_obj, key, value)
            self.save()
            logger.info(f"Updated {section}.{key} = {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to set config: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset all settings to optimized defaults"""
        self.config = JarvisConfig()
        self.save()
        logger.info("Configuration reset to optimized defaults")


# ═══════════════════════════════════════════════════════════════════════════
# CONFIG EDITOR
# ═══════════════════════════════════════════════════════════════════════════

class ConfigEditor:
    """Interactive configuration editor"""
    
    def __init__(self, config_manager: ConfigManager):
        self.manager = config_manager
    
    def show_current_config(self):
        """Display current configuration"""
        config = self.manager.config
        
        print("\n" + "="*60)
        print("JARVIS CONFIGURATION - RTX 3050 OPTIMIZED")
        print("="*60)
        
        print("\n[VOICE SETTINGS]")
        print(f"  TTS Rate: {config.voice.tts_rate} words/min")
        print(f"  TTS Volume: {config.voice.tts_volume}")
        print(f"  STT Model: {config.voice.stt_model}")
        print(f"  Wake Word: {config.voice.wake_word} (Enabled: {config.voice.wake_word_enabled})")
        print(f"  Hotkey: {config.voice.hotkey}")
        print(f"  Auto Speak: {config.voice.auto_speak}")
        print(f"  Max Speech Length: {config.voice.max_speech_length}")
        
        print("\n[MODEL SETTINGS]")
        print(f"  Default Model: {config.models.default_model}")
        print(f"  Coding Model: {config.models.coding_model}")
        print(f"  Creative Model: {config.models.creative_model}")
        print(f"  Fast Model: {config.models.fast_model}")
        print(f"  Temperature: {config.models.temperature}")
        print(f"  Max Tokens: {config.models.max_tokens}")
        print(f"  Max Context: {config.models.max_context_length}")
        
        print("\n[APP SETTINGS]")
        print(f"  Startup Enabled: {config.app.startup_enabled}")
        print(f"  System Tray: {config.app.system_tray_enabled}")
        print(f"  Theme: {config.app.gui_theme}")
        print(f"  Log Level: {config.app.log_level}")
        print(f"  Memory Limit: {config.app.memory_limit}")
        print(f"  Turbo Mode: {config.app.enable_turbo_mode}")
        
        print("\n[PERFORMANCE SETTINGS]")
        print(f"  VRAM Limit: {config.performance.vram_limit_gb}GB")
        print(f"  Max Loaded Models: {config.performance.max_loaded_models}")
        print(f"  Auto Unload: {config.performance.auto_unload_seconds}s")
        print(f"  Pre-warm Models: {config.performance.pre_warm_models}")
        print(f"  Emergency Cleanup: {config.performance.emergency_cleanup}")
        print(f"  Process Priority: {config.performance.process_priority}")
        
        print("\n[WEB SETTINGS]")
        print(f"  Web Agent Enabled: {config.web.enable_web_agent}")
        print(f"  Headless Browser: {config.web.headless_browser}")
        print(f"  Timeout: {config.web.browser_timeout}s")
        print(f"  Max Results: {config.web.max_search_results}")
        
        print("="*60 + "\n")
    
    def edit_voice_settings(self):
        """Interactive voice settings editor"""
        print("\n[VOICE SETTINGS EDITOR]")
        config = self.manager.config.voice
        
        rate = input(f"TTS Rate (current: {config.tts_rate}): ").strip()
        if rate:
            config.tts_rate = int(rate)
        
        volume = input(f"TTS Volume 0.0-1.0 (current: {config.tts_volume}): ").strip()
        if volume:
            config.tts_volume = float(volume)
        
        max_length = input(f"Max Speech Length (current: {config.max_speech_length}): ").strip()
        if max_length:
            config.max_speech_length = int(max_length)
        
        auto_speak = input(f"Auto Speak [yes/no] (current: {config.auto_speak}): ").strip().lower()
        if auto_speak:
            config.auto_speak = (auto_speak == 'yes')
        
        self.manager.save()
        print("✓ Voice settings saved")
    
    def edit_model_settings(self):
        """Interactive model settings editor"""
        print("\n[MODEL SETTINGS EDITOR]")
        config = self.manager.config.models
        
        print("Recommended models for RTX 3050:")
        print("  gemma:2b, phi3:3.8b, deepseek-coder:6.7b")
        
        default = input(f"Default Model (current: {config.default_model}): ").strip()
        if default:
            config.default_model = default
        
        temp = input(f"Temperature 0.0-1.0 (current: {config.temperature}): ").strip()
        if temp:
            config.temperature = float(temp)
        
        tokens = input(f"Max Tokens (current: {config.max_tokens}): ").strip()
        if tokens:
            config.max_tokens = int(tokens)
        
        context = input(f"Max Context Length (current: {config.max_context_length}): ").strip()
        if context:
            config.max_context_length = int(context)
        
        self.manager.save()
        print("✓ Model settings saved")
    
    def edit_performance_settings(self):
        """Interactive performance settings editor"""
        print("\n[PERFORMANCE SETTINGS EDITOR]")
        config = self.manager.config.performance
        
        vram = input(f"VRAM Limit in GB (current: {config.vram_limit_gb}): ").strip()
        if vram:
            config.vram_limit_gb = float(vram)
        
        max_models = input(f"Max Loaded Models (current: {config.max_loaded_models}): ").strip()
        if max_models:
            config.max_loaded_models = int(max_models)
        
        unload = input(f"Auto Unload Seconds (current: {config.auto_unload_seconds}): ").strip()
        if unload:
            config.auto_unload_seconds = int(unload)
        
        pre_warm = input(f"Pre-warm Models [yes/no] (current: {config.pre_warm_models}): ").strip().lower()
        if pre_warm:
            config.pre_warm_models = (pre_warm == 'yes')
        
        self.manager.save()
        print("✓ Performance settings saved")
    
    def interactive_menu(self):
        """Main interactive configuration menu"""
        while True:
            print("\n" + "="*60)
            print("JARVIS CONFIGURATION EDITOR - RTX 3050 OPTIMIZED")
            print("="*60)
            print("1. Show Current Configuration")
            print("2. Edit Voice Settings")
            print("3. Edit Model Settings")
            print("4. Edit Performance Settings")
            print("5. Reset to Optimized Defaults")
            print("6. Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                self.show_current_config()
            elif choice == "2":
                self.edit_voice_settings()
            elif choice == "3":
                self.edit_model_settings()
            elif choice == "4":
                self.edit_performance_settings()
            elif choice == "5":
                confirm = input("Reset all settings to optimized defaults? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    self.manager.reset_to_defaults()
                    print("✓ Configuration reset to optimized defaults")
            elif choice == "6":
                break
            else:
                print("Invalid option. Please select 1-6.")


# ═══════════════════════════════════════════════════════════════════════════
# QUICK ACCESS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_config() -> JarvisConfig:
    """Quick access to current configuration"""
    manager = ConfigManager()
    return manager.config


def update_config(section: str, key: str, value: Any):
    """Quick update a config value"""
    manager = ConfigManager()
    manager.set(section, key, value)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point for config management"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "edit":
            # Interactive editor
            manager = ConfigManager()
            editor = ConfigEditor(manager)
            editor.interactive_menu()
        
        elif command == "show":
            # Show current config
            manager = ConfigManager()
            editor = ConfigEditor(manager)
            editor.show_current_config()
        
        else:
            print("Unknown command. Available: edit, show")
    
    else:
        # Default: show current config
        manager = ConfigManager()
        editor = ConfigEditor(manager)
        editor.show_current_config()
        
        print("Usage:")
        print("  python jarvis_config.py edit  - Interactive editor")
        print("  python jarvis_config.py show  - Show configuration")


if __name__ == "__main__":
    main()