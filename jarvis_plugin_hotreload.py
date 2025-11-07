"""
jarvis_plugin_hotreload.py
═══════════════════════════════════════════════════════════════════════════════
Hot-Reload Plugin System for JARVIS
Watches skills folder and auto-reloads on changes
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import importlib
import logging
import sys
from pathlib import Path
from typing import Dict, Set
from datetime import datetime
import json

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logging.warning("watchdog not installed - hot reload disabled. Install: pip install watchdog")

from jarvis_skills import SkillManager, BaseSkill

logger = logging.getLogger("JARVIS.HotReload")


class PluginHotReloadManager:
    """Manages hot-reloading of plugins with file watching"""
    
    def __init__(self, skill_manager: SkillManager, skills_dir: str = "skills"):
        self.skill_manager = skill_manager
        self.skills_dir = Path(skills_dir)
        self.observer = None
        self.loaded_modules: Dict[str, float] = {}  # module_name -> last_modified
        self.pending_reloads: Set[str] = set()
        self.reload_lock = asyncio.Lock()
        
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(exist_ok=True)
            logger.info(f"📁 Created skills directory: {self.skills_dir}")
    
    def start(self):
        """Start watching for file changes"""
        if not WATCHDOG_AVAILABLE:
            logger.warning("⚠️ Hot reload not available - watchdog not installed")
            return False
        
        try:
            event_handler = PluginFileHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, str(self.skills_dir), recursive=False)
            self.observer.start()
            logger.info(f"👀 Hot reload active - watching {self.skills_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to start hot reload: {e}")
            return False
    
    def stop(self):
        """Stop watching for changes"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("🛑 Hot reload stopped")
    
    async def reload_plugin(self, file_path: Path):
        """Reload a specific plugin file"""
        async with self.reload_lock:
            try:
                # Extract module name
                module_name = f"skills.{file_path.stem}"
                
                logger.info(f"🔄 Reloading plugin: {file_path.name}")
                
                # Remove from skills dict
                skill_name = file_path.stem
                if skill_name in self.skill_manager.skills:
                    old_skill = self.skill_manager.skills[skill_name]
                    logger.info(f"  Unloading old version of {skill_name}")
                    del self.skill_manager.skills[skill_name]
                
                # Reload module
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                else:
                    importlib.import_module(module_name)
                
                # Reload all skills to catch the new one
                self.skill_manager.load_skills()
                
                # Verify it loaded
                if skill_name in self.skill_manager.skills:
                    logger.info(f"  ✅ Successfully reloaded {skill_name}")
                    self.broadcast_plugin_update(skill_name, 'reloaded')
                    return True
                else:
                    logger.warning(f"  ⚠️ Plugin {skill_name} not found after reload")
                    return False
                    
            except Exception as e:
                logger.error(f"  ❌ Failed to reload {file_path.name}: {e}")
                self.broadcast_plugin_update(file_path.stem, 'error', str(e))
                return False
    
    async def reload_all_plugins(self):
        """Reload all plugins"""
        logger.info("🔄 Reloading all plugins...")
        
        # Clear current skills
        self.skill_manager.skills.clear()
        
        # Reload all
        self.skill_manager.load_skills()
        
        logger.info(f"✅ Reloaded {len(self.skill_manager.skills)} plugins")
        self.broadcast_plugin_update('all', 'reloaded')
    
    def broadcast_plugin_update(self, plugin_name: str, status: str, error: str = None):
        """Broadcast plugin update to connected clients"""
        # This will be called from the API bridge to notify UI
        update = {
            'type': 'plugin_update',
            'plugin': plugin_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
        }
        if error:
            update['error'] = error
        
        # Store in a queue or broadcast mechanism
        # The API bridge will pick this up and send via WebSocket
        logger.debug(f"📡 Broadcasting: {update}")
    
    def get_plugin_info(self, plugin_name: str) -> Dict:
        """Get detailed info about a plugin"""
        if plugin_name not in self.skill_manager.skills:
            return None
        
        skill = self.skill_manager.skills[plugin_name]
        
        return {
            'id': plugin_name,
            'name': plugin_name.title(),
            'keywords': getattr(skill, 'keywords', []),
            'description': skill.__doc__ or 'No description',
            'config': getattr(skill, 'config', {}),
            'active': True,
            'module': skill.__class__.__module__,
        }
    
    def list_all_plugins(self) -> list:
        """Get list of all plugins with their info"""
        return [
            self.get_plugin_info(name) 
            for name in self.skill_manager.skills.keys()
        ]
    
    def create_plugin_template(self, plugin_name: str) -> Path:
        """Create a new plugin from template"""
        plugin_file = self.skills_dir / f"{plugin_name}_skill.py"
        
        if plugin_file.exists():
            raise FileExistsError(f"Plugin {plugin_name} already exists")
        
        template = f'''"""
skills/{plugin_name}_skill.py
──────────────────────────────────────────────
{plugin_name.title()} Skill for JARVIS
Auto-generated plugin template
"""

from jarvis_skills import BaseSkill
import asyncio

class Skill(BaseSkill):
    name = "{plugin_name}"
    keywords = ["{plugin_name}", "example"]

    async def handle(self, text, jarvis):
        """
        Handle commands for {plugin_name}
        
        Args:
            text: User input text
            jarvis: JARVIS core instance
            
        Returns:
            Response string or None if not handled
        """
        text = text.lower().strip()
        
        # TODO: Implement your logic here
        if "{plugin_name}" in text:
            return f"Hello from {plugin_name} plugin!"
        
        return None
'''
        
        plugin_file.write_text(template)
        logger.info(f"✨ Created new plugin template: {plugin_file}")
        
        return plugin_file


class PluginFileHandler(FileSystemEventHandler):
    """Handle file system events for plugin files"""
    
    def __init__(self, manager: PluginHotReloadManager):
        self.manager = manager
        self.debounce_delay = 0.5  # seconds
        self.pending_events = {}
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        self._handle_file_event(event)
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        self._handle_file_event(event)
    
    def _handle_file_event(self, event):
        """Handle file modification with debouncing"""
        file_path = Path(event.src_path)
        
        # Only process Python files
        if file_path.suffix != '.py':
            return
        
        # Ignore __pycache__ and __init__.py
        if '__pycache__' in str(file_path) or file_path.name == '__init__.py':
            return
        
        logger.debug(f"📝 File changed: {file_path.name}")
        
        # Debounce rapid changes
        current_time = asyncio.get_event_loop().time()
        last_event = self.pending_events.get(str(file_path), 0)
        
        if current_time - last_event < self.debounce_delay:
            return
        
        self.pending_events[str(file_path)] = current_time
        
        # Schedule reload
        asyncio.create_task(self.manager.reload_plugin(file_path))


# ═══════════════════════════════════════════════════════════════════════════
# Integration with API Bridge
# ═══════════════════════════════════════════════════════════════════════════

class PluginAPI:
    """API endpoints for plugin management"""
    
    def __init__(self, hot_reload_manager: PluginHotReloadManager):
        self.manager = hot_reload_manager
    
    async def list_plugins(self):
        """Get all plugins with detailed info"""
        return {
            'plugins': self.manager.list_all_plugins(),
            'count': len(self.manager.skill_manager.skills),
            'skills_dir': str(self.manager.skills_dir),
        }
    
    async def get_plugin(self, plugin_name: str):
        """Get detailed info for one plugin"""
        info = self.manager.get_plugin_info(plugin_name)
        if not info:
            return {'error': 'Plugin not found'}
        return info
    
    async def reload_plugin(self, plugin_name: str):
        """Reload a specific plugin"""
        plugin_file = self.manager.skills_dir / f"{plugin_name}_skill.py"
        
        if not plugin_file.exists():
            return {'error': 'Plugin file not found'}
        
        success = await self.manager.reload_plugin(plugin_file)
        return {
            'success': success,
            'plugin': plugin_name,
            'timestamp': datetime.now().isoformat(),
        }
    
    async def reload_all_plugins(self):
        """Reload all plugins"""
        await self.manager.reload_all_plugins()
        return {
            'success': True,
            'count': len(self.manager.skill_manager.skills),
            'timestamp': datetime.now().isoformat(),
        }
    
    async def create_plugin(self, plugin_name: str):
        """Create a new plugin from template"""
        try:
            plugin_file = self.manager.create_plugin_template(plugin_name)
            return {
                'success': True,
                'plugin': plugin_name,
                'file': str(plugin_file),
            }
        except FileExistsError as e:
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to create plugin: {e}")
            return {'error': str(e)}
    
    async def delete_plugin(self, plugin_name: str):
        """Delete a plugin"""
        plugin_file = self.manager.skills_dir / f"{plugin_name}_skill.py"
        
        if not plugin_file.exists():
            return {'error': 'Plugin file not found'}
        
        try:
            # Remove from loaded skills
            if plugin_name in self.manager.skill_manager.skills:
                del self.manager.skill_manager.skills[plugin_name]
            
            # Delete file
            plugin_file.unlink()
            
            logger.info(f"🗑️ Deleted plugin: {plugin_name}")
            
            return {
                'success': True,
                'plugin': plugin_name,
            }
        except Exception as e:
            logger.error(f"Failed to delete plugin: {e}")
            return {'error': str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# Usage Example
# ═══════════════════════════════════════════════════════════════════════════

async def demo_hot_reload():
    """Demo of hot reload system"""
    from jarvis_skills import SkillManager
    
    # Create skill manager
    skill_manager = SkillManager()
    
    # Create hot reload manager
    hot_reload = PluginHotReloadManager(skill_manager)
    
    # Start watching
    if hot_reload.start():
        print("✅ Hot reload active!")
        print("📝 Try editing a file in the skills/ directory")
        print("🔄 Changes will be automatically reloaded")
        
        # Create API interface
        plugin_api = PluginAPI(hot_reload)
        
        # List plugins
        plugins = await plugin_api.list_plugins()
        print(f"
📦 Loaded {plugins['count']} plugins:")
        for p in plugins['plugins']:
            print(f"  - {p['name']}: {p['description'][:50]}...")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("
🛑 Stopping...")
            hot_reload.stop()
    else:
        print("❌ Hot reload not available")


if __name__ == "__main__":
    asyncio.run(demo_hot_reload())
