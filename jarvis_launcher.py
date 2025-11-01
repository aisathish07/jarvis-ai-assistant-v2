"""
═══════════════════════════════════════════════════════════════════════════════
FILE: jarvis_launcher.py
DESCRIPTION: Multi-mode launcher with setup utilities
DEPENDENCIES: jarvis_core_optimized, jarvis_gui
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import logging
from pathlib import Path
from jarvis_core_optimized import JarvisIntegrated
logger = logging.getLogger("Jarvis.Launcher")


# ═══════════════════════════════════════════════════════════════════════════
# JARVIS LAUNCHER
# ═══════════════════════════════════════════════════════════════════════════

class JarvisLauncher:
    """Launch the full Jarvis system in different modes"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
    
    def launch_cli(self):
        """Launch command-line interface"""
        logger.info("Starting JARVIS CLI mode...")
        from jarvis_core_optimized import interactive_mode
        import asyncio
        
        asyncio.run(interactive_mode())
    
    def launch_gui(self):
        """Launch GUI interface"""
        logger.info("Starting JARVIS GUI mode...")
        
        try:
            from jarvis_core_optimized import JarvisIntegrated
            from jarvis_gui import launch_gui
            
            jarvis = JarvisIntegrated()
            launch_gui(jarvis)
        
        except ImportError as e:
            print("\n" + "="*60)
            print("GUI MODE ERROR")
            print("="*60)
            print(f"\nMissing dependency: {e}")
            print("\nTo use GUI mode, install PyQt6:")
            print("  pip install PyQt6")
            print("\nAlternatively, use CLI mode:")
            print("  python jarvis.py chat")
            print("\n" + "="*60 + "\n")
    
    def launch_demo(self):
        """Launch demo mode"""
        logger.info("Starting JARVIS demo mode...")
        from jarvis_core_optimized import demo_mode
        import asyncio
        
        asyncio.run(demo_mode())
    
    def show_status(self):
        """Show system status"""
        from jarvis_core_optimized import JarvisIntegrated
        
        jarvis = JarvisIntegrated()
        print(jarvis.get_status_summary())
        jarvis.cleanup()


# ═══════════════════════════════════════════════════════════════════════════
# SETUP UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

class SetupUtilities:
    """Setup and configuration utilities"""
    
    @staticmethod
    def setup_startup():
        """Configure Windows startup (optional)"""
        import platform
        import os
        
        if platform.system() != "Windows":
            print("Startup setup is only available on Windows")
            return
        
        print("\n" + "="*60)
        print("WINDOWS STARTUP CONFIGURATION")
        print("="*60)
        print("\nThis will make JARVIS start automatically when Windows boots.")
        
        choice = input("\nAdd to startup? (yes/no): ").strip().lower()
        
        if choice == 'yes':
            try:
                startup_folder = Path(os.getenv('APPDATA')) / "Microsoft/Windows/Start Menu/Programs/Startup"
                script_path = Path(__file__).parent / "jarvis.py"
                
                shortcut_path = startup_folder / "JARVIS.bat"
                
                batch_content = f"""@echo off
cd /d "{script_path.parent}"
start /B pythonw jarvis.py gui
exit
"""
                
                with open(shortcut_path, 'w') as f:
                    f.write(batch_content)
                
                print(f"\n✓ Startup shortcut created at {shortcut_path}")
                print("JARVIS will now start automatically with Windows")
            
            except Exception as e:
                print(f"\n✗ Failed to create startup shortcut: {e}")
        else:
            print("\nStartup setup cancelled")
        
        print("\n" + "="*60 + "\n")
    
    @staticmethod
    def create_desktop_shortcut():
        """Create desktop shortcut"""
        print("\n" + "="*60)
        print("DESKTOP SHORTCUT")
        print("="*60)
        print("\nTo create a desktop shortcut:")
        print("1. Right-click on jarvis.py")
        print("2. Select 'Send to' → 'Desktop (create shortcut)'")
        print("3. Right-click the shortcut → Properties")
        print("4. In 'Target', add: python jarvis.py chat")
        print("\n" + "="*60 + "\n")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point for launcher"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        launcher = JarvisLauncher()
        
        if command == "cli" or command == "chat":
            launcher.launch_cli()
        
        elif command == "gui":
            launcher.launch_gui()
        
        elif command == "demo":
            launcher.launch_demo()
        
        elif command == "status":
            launcher.show_status()
        
        elif command == "setup":
            print("\n🤖 JARVIS SETUP")
            print("="*40)
            print("1. Configure Windows Startup")
            print("2. Desktop Shortcut Info")
            print("3. Exit")
            
            choice = input("\nSelect (1-3): ").strip()
            
            if choice == "1":
                SetupUtilities.setup_startup()
            elif choice == "2":
                SetupUtilities.create_desktop_shortcut()
            else:
                print("Goodbye!")
        
        else:
            print(f"Unknown command: {command}")
            print("Available: cli, gui, demo, status, setup")
    
    else:
        print("\nUsage: python jarvis_launcher.py [command]")
        print("\nCommands:")
        print("  cli    - Command-line interface")
        print("  gui    - Graphical interface")
        print("  demo   - Feature demonstration")
        print("  status - Show system status")
        print("  setup  - Setup utilities")


if __name__ == "__main__":
    main()