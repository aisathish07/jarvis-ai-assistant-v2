"""
═══════════════════════════════════════════════════════════════════════════════
FILE: jarvis_install.py
DESCRIPTION: One-click installation and diagnostic system
DEPENDENCIES: subprocess, sys
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# Remove the incorrect import line and replace with:
try:
    from jarvis_core_optimized import JarvisOptimizedCore
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


# ═══════════════════════════════════════════════════════════════════════════
# JARVIS INSTALLER
# ═══════════════════════════════════════════════════════════════════════════

class JarvisInstaller:
    """Complete installation and setup manager"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.is_windows = platform.system() == "Windows"
        self.python_cmd = sys.executable
        self.checks_passed = []
        self.checks_failed = []
    
    def check_python_version(self):
        """Step 1: Check Python version"""
        print_info("Checking Python version...")
        version = sys.version_info
        
        if version.major == 3 and version.minor >= 9:
            print_success(f"Python {version.major}.{version.minor}.{version.micro}")
            self.checks_passed.append("Python version")
            return True
        else:
            print_error(f"Python 3.9+ required (found {version.major}.{version.minor})")
            self.checks_failed.append("Python version")
            return False
    
    def check_ollama(self):
        """Step 2: Check Ollama installation"""
        print_info("Checking Ollama...")
        
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print_success("Ollama is installed and running")
                lines = result.stdout.strip().split('\n')
                model_count = len(lines) - 1
                print_info(f"Found {model_count} models")
                self.checks_passed.append("Ollama")
                return True
            else:
                print_warning("Ollama not responding")
                self.checks_failed.append("Ollama")
                return False
                
        except FileNotFoundError:
            print_error("Ollama not found")
            print_info("Install from: https://ollama.com/download")
            self.checks_failed.append("Ollama")
            return False
        except Exception as e:
            print_error(f"Ollama check failed: {e}")
            self.checks_failed.append("Ollama")
            return False
    
    def verify_models(self):
        """Step 3: Verify required models"""
        print_info("Verifying AI models...")
        
        required_models = {
            "phi3:3.8b": "Balanced",
            "deepseek-coder:6.7b": "Coding", 
            "gemma:2b": "Lightweight"
        }
        
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True
            )
            
            installed = result.stdout.lower()
            missing = []
            
            for model, purpose in required_models.items():
                model_name = model.split(':')[0]
                if model_name in installed:
                    print_success(f"{model} ({purpose})")
                else:
                    print_warning(f"{model} - NOT FOUND ({purpose})")
                    missing.append(model)
            
            if missing:
                print_warning(f"\n{len(missing)} models missing")
                print_info("To install:")
                for model in missing:
                    print(f"  ollama pull {model}")
                return False
            else:
                print_success("All essential models installed")
                self.checks_passed.append("AI Models")
                return True
                
        except Exception as e:
            print_error(f"Model verification failed: {e}")
            self.checks_failed.append("AI Models")
            return False
    
    def install_dependencies(self):
        """Step 4: Install Python dependencies"""
        print_info("Installing Python dependencies...")
        
        packages = [
            "ollama",
            "pyttsx3", 
            "sounddevice",
            "numpy",
            "pynput",
            "pyautogui",
            "psutil",
            "aiohttp"
        ]
        
        success_count = 0
        for package in packages:
            print(f"  Installing {package}...", end=" ")
            try:
                result = subprocess.run(
                    [self.python_cmd, "-m", "pip", "install", package, "-q"],
                    capture_output=True,
                    timeout=120
                )
                if result.returncode == 0:
                    print(f"{Colors.GREEN}✓{Colors.END}")
                    success_count += 1
                else:
                    print(f"{Colors.YELLOW}⚠{Colors.END}")
            except:
                print(f"{Colors.YELLOW}⚠{Colors.END}")
        
        if success_count >= len(packages) - 2:  # Allow 2 failures
            print_success("Dependencies installed")
            self.checks_passed.append("Dependencies")
            return True
        else:
            print_warning("Some dependencies failed to install")
            self.checks_failed.append("Dependencies")
            return False
    
    def create_project_structure(self):
        """Step 5: Create necessary directories"""
        print_info("Setting up project structure...")
        
        try:
            # Create skills directory if it doesn't exist
            skills_dir = self.project_dir / "skills"
            skills_dir.mkdir(exist_ok=True)
            
            # Create config file if it doesn't exist
            config_file = self.project_dir / "jarvis_config.json"
            if not config_file.exists():
                default_config = {
                    "voice": {
                        "tts_rate": 175,
                        "tts_volume": 0.9,
                        "stt_model": "base",
                        "wake_word_enabled": False,
                        "wake_word": "jarvis",
                        "hotkey": "ctrl+space",
                        "auto_speak": True
                    },
                    "models": {
                        "default_model": "phi3:3.8b",
                        "coding_model": "deepseek-coder:6.7b",
                        "creative_model": "phi3:3.8b",
                        "fast_model": "gemma:2b",
                        "lightweight_model": "gemma:2b",
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 2048
                    },
                    "app": {
                        "startup_enabled": False,
                        "system_tray_enabled": True,
                        "gui_theme": "dark",
                        "log_level": "INFO",
                        "memory_limit": 100,
                        "auto_cleanup": True
                    },
                    "web": {
                        "headless_browser": True,
                        "browser_timeout": 30,
                        "max_search_results": 5,
                        "enable_web_agent": False
                    }
                }
                import json
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                print_success("Default config created")
            
            print_success("Project structure ready")
            self.checks_passed.append("Project structure")
            return True
        except Exception as e:
            print_error(f"Failed to create structure: {e}")
            self.checks_failed.append("Project structure")
            return False
    
    def show_summary(self):
        """Show installation summary"""
        print("\n" + "="*60)
        print(f"{Colors.BOLD}INSTALLATION SUMMARY{Colors.END}")
        print("="*60)
        
        print(f"\n{Colors.BOLD}Passed Checks:{Colors.END}")
        for check in self.checks_passed:
            print(f"  {Colors.GREEN}✓{Colors.END} {check}")
        
        if self.checks_failed:
            print(f"\n{Colors.BOLD}Failed Checks:{Colors.END}")
            for check in self.checks_failed:
                print(f"  {Colors.RED}✗{Colors.END} {check}")
        
        print()
        
        if len(self.checks_failed) == 0:
            print_success("Installation complete! JARVIS is ready.")
            print()
            print(f"{Colors.BOLD}To start JARVIS:{Colors.END}")
            print(f"  python jarvis.py chat")
            print()
            print(f"{Colors.BOLD}Recommended models for RTX 3050:{Colors.END}")
            print(f"  ollama pull gemma:2b")
            print(f"  ollama pull phi3:3.8b")
            print(f"  ollama pull deepseek-coder:6.7b")
            print()
        else:
            print_warning("Installation incomplete. Fix failed checks.")
    
    def run_full_installation(self):
        """Execute complete installation"""
        print("\n" + "="*60)
        print(f"{Colors.BOLD}JARVIS AI ASSISTANT - INSTALLATION{Colors.END}")
        print("="*60)
        
        print(f"\nSystem: {Colors.BOLD}{platform.system()} {platform.release()}{Colors.END}")
        print(f"Python: {Colors.BOLD}{sys.version.split()[0]}{Colors.END}\n")
        
        input("Press Enter to begin...")
        
        # Run all checks
        self.check_python_version()
        self.check_ollama()
        self.verify_models()
        self.install_dependencies()
        self.create_project_structure()
        
        # Show summary
        self.show_summary()


# ═══════════════════════════════════════════════════════════════════════════
# QUICK TEST
# ═══════════════════════════════════════════════════════════════════════════

class QuickTest:
    """Quick functionality tests"""
    
    @staticmethod
    def test_ollama():
        print("\n" + "="*60)
        print("Testing Ollama Connection")
        print("="*60)
        
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print_success("Ollama is responsive")
                print("\nInstalled models:")
                print(result.stdout)
                return True
            else:
                print_error("Ollama not responding")
                return False
                
        except Exception as e:
            print_error(f"Test failed: {e}")
            return False
    
    @staticmethod
    def test_imports():
        print("\n" + "="*60)
        print("Testing Python Imports")
        print("="*60)
        
        modules = [
            "ollama",
            "pyttsx3",
            "psutil",
            "aiohttp"
        ]
        
        all_passed = True
        
        for module in modules:
            try:
                __import__(module)
                print_success(f"{module}")
            except ImportError:
                print_error(f"{module} - NOT FOUND")
                all_passed = False
        
        return all_passed
    
    @staticmethod
    def test_core():
        """Test if core system can be imported"""
        print("\n" + "="*60)
        print("Testing Core System")
        print("="*60)
        
        try:
            from jarvis_core_optimized import JarvisOptimizedCore
            print_success("Core system import successful")
            return True
        except ImportError as e:
            print_error(f"Core system import failed: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "install":
            installer = JarvisInstaller()
            installer.run_full_installation()
        
        elif command == "test":
            QuickTest.test_ollama()
            QuickTest.test_imports()
            QuickTest.test_core()
        
        else:
            print("Unknown command. Available: install, test")
    
    else:
        print("\n🤖 JARVIS INSTALLATION TOOL")
        print("="*40)
        print("1. Full Installation")
        print("2. Quick Test")
        print("3. Exit")
        
        choice = input("\nSelect (1-3): ").strip()
        
        if choice == "1":
            installer = JarvisInstaller()
            installer.run_full_installation()
        elif choice == "2":
            QuickTest.test_ollama()
            QuickTest.test_imports()
            QuickTest.test_core()
        else:
            print("Goodbye!")


if __name__ == "__main__":
    main()