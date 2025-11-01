"""
═══════════════════════════════════════════════════════════════════════════════
FILE: jarvis.py
DESCRIPTION: Main entry point - Master launcher for JARVIS - OPTIMIZED FOR RTX 3050
USAGE: python jarvis.py [command]
       python jarvis.py chat       # Start interactive chat
       python jarvis.py demo       # Run feature demo
       python jarvis.py status     # Show system status
       python jarvis.py install    # Run installation
       python jarvis.py            # Show menu
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import asyncio
import os
import psutil

# Import JARVIS modules
from jarvis_core_optimized import interactive_mode, demo_mode, JarvisOptimizedCore
from jarvis_install import JarvisInstaller, QuickTest
from jarvis_config import ConfigManager, ConfigEditor


# ═══════════════════════════════════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════════════════════════════════

BANNER = """
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
║                     Local AI Assistant                      ║
║                                                              ║
║                    ⚡ OPTIMIZED FOR RTX 3050 ⚡              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def show_banner():
    """Display JARVIS banner"""
    print(BANNER)


def show_main_menu():
    """Display main menu"""
    show_banner()
    print("\n🎯 What would you like to do?\n")
    print("  1️⃣  Start Interactive Chat (Optimized)")
    print("  2️⃣  Run Feature Demo")
    print("  3️⃣  Show System Status")
    print("  4️⃣  Edit Configuration")
    print("  5️⃣  Install/Setup")
    print("  6️⃣  Run Tests")
    print("  7️⃣  Quick Query")
    print("  8️⃣  Help")
    print("  0️⃣  Exit")
    print("\n" + "="*62)


def show_help():
    """Show help information"""
    print("\n" + "="*62)
    print("JARVIS HELP - RTX 3050 OPTIMIZED")
    print("="*62)
    print("\n📚 Commands:")
    print("  python jarvis.py chat      - Start optimized interactive chat")
    print("  python jarvis.py demo      - Run feature demo")
    print("  python jarvis.py status    - Show system status")
    print("  python jarvis.py config    - Edit configuration")
    print("  python jarvis.py install   - Run installation")
    print("  python jarvis.py test      - Run diagnostics")
    print("  python jarvis.py \"question\" - Quick query")
    
    print("\n⚡ RTX 3050 Optimized Features:")
    print("  • Smart VRAM management (never exceeds 3.8GB)")
    print("  • Auto model selection based on task type")
    print("  • Background model pre-warming")
    print("  • Emergency memory cleanup")
    print("  • Optimized process priority")
    
    print("\n💡 Example Commands:")
    print("  python jarvis.py \"Write a Python function\"")
    print("  python jarvis.py chat")
    print("  python jarvis.py demo")
    
    print("\n🎯 First Time Setup:")
    print("  1. Install Ollama from https://ollama.com")
    print("  2. Pull optimized models:")
    print("     ollama pull gemma:2b")
    print("     ollama pull phi3:3.8b")
    print("     ollama pull deepseek-coder:6.7b")
    print("  3. Run: python jarvis.py install")
    print("  4. Start: python jarvis.py chat")
    
    print("\n" + "="*62 + "\n")


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════

def optimize_system():
    """Set system optimizations at startup"""
    try:
        # Set process priority on Windows
        if hasattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS'):
            p = psutil.Process()
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            print("✅ Process priority optimized")
        
        # Force garbage collection
        import gc
        gc.collect()
        
        print("✅ System optimizations applied")
        
    except Exception as e:
        print(f"⚠️ System optimization failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# QUICK QUERY MODE
# ═══════════════════════════════════════════════════════════════════════════

async def quick_query_mode(query: str):
    """Quick query mode with optimization"""
    from jarvis_core_optimized import quick_query
    
    print(f"\n🤔 Processing: {query}")
    print("⚡ Using RTX 3050 optimized mode...")
    
    try:
        result = await quick_query(query, profile="turbo_3050")
        print(f"\n✅ Response:\n{result}\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")


# ═══════════════════════════════════════════════════════════════════════════
# COMMAND ROUTER
# ═══════════════════════════════════════════════════════════════════════════

def run_command(command: str):
    """Execute a JARVIS command"""
    
    if command == "chat" or command == "1":
        print("🚀 Starting JARVIS with RTX 3050 optimizations...")
        asyncio.run(interactive_mode())
    
    elif command == "demo" or command == "2":
        print("🎬 Starting demo with optimizations...")
        asyncio.run(demo_mode())
    
    elif command == "status" or command == "3":
        jarvis = JarvisOptimizedCore()
        asyncio.run(jarvis.initialize())
        print(jarvis.get_status())
        asyncio.run(jarvis.cleanup())
    
    elif command == "config" or command == "4":
        manager = ConfigManager()
        editor = ConfigEditor(manager)
        editor.interactive_menu()
    
    elif command == "install" or command == "5":
        installer = JarvisInstaller()
        installer.run_full_installation()
    
    elif command == "test" or command == "6":
        QuickTest.test_ollama()
        QuickTest.test_imports()
    
    elif command == "query" or command == "7":
        query = input("\nEnter your question: ").strip()
        if query:
            asyncio.run(quick_query_mode(query))
    
    elif command == "help" or command == "8":
        show_help()
    
    elif command == "0" or command == "exit":
        print("\n👋 Goodbye!\n")
        sys.exit(0)
    
    else:
        print(f"\n❌ Unknown command: {command}")
        print("💡 Type 'help' for available commands\n")


# ═══════════════════════════════════════════════════════════════════════════
# INTERACTIVE MENU
# ═══════════════════════════════════════════════════════════════════════════

def interactive_menu():
    """Run interactive menu loop"""
    # Apply system optimizations
    optimize_system()
    
    while True:
        show_main_menu()
        choice = input("\nYour choice: ").strip().lower()
        
        if choice in ['0', 'exit', 'quit']:
            print("\n👋 Goodbye!\n")
            break
        
        try:
            run_command(choice)
            
            # After command, ask to continue (except for chat mode)
            if choice not in ['1', 'chat']:
                input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\nPress Enter to continue...")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point"""
    
    # Apply system optimizations
    optimize_system()
    
    # Check if command provided
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        # Known commands
        known_commands = ['chat', 'demo', 'status', 'config', 'install', 'test', 'help']
        
        if command in known_commands:
            # Execute command
            run_command(command)
        
        elif command == "query":
            # Query mode with argument
            if len(sys.argv) > 2:
                query = " ".join(sys.argv[2:])
                asyncio.run(quick_query_mode(query))
            else:
                print("Usage: python jarvis.py query <your question>")
        
        else:
            # Treat entire argument as a query
            query = " ".join(sys.argv[1:])
            asyncio.run(quick_query_mode(query))
    
    else:
        # No command - show interactive menu
        try:
            interactive_menu()
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")


if __name__ == "__main__":
    main()