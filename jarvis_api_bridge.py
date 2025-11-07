"""
jarvis_api_bridge.py
═══════════════════════════════════════════════════════════════════════════════
Bridge layer between React UI and JARVIS Core
Provides WebSocket streaming + REST API endpoints
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import aiohttp
from aiohttp import web
import aiofiles

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from jarvis_core_optimized import JarvisOptimizedCore
from jarvis_skills import SkillManager
from jarvis_plugin_hotreload import PluginHotReloadManager, PluginAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS.API")

# ═══════════════════════════════════════════════════════════════════════════
# Global JARVIS Instance
# ═══════════════════════════════════════════════════════════════════════════

class JarvisAPIServer:
    def __init__(self):
        self.jarvis_core: Optional[JarvisOptimizedCore] = None
        self.hot_reload_manager: Optional[PluginHotReloadManager] = None
        self.plugin_api: Optional[PluginAPI] = None
        self.active_connections = set()
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize JARVIS core"""
        logger.info("🚀 Initializing JARVIS Core...")
        self.jarvis_core = JarvisOptimizedCore(enable_voice=False)
        await self.jarvis_core.initialize()
        logger.info("✅ JARVIS Core ready!")

        logger.info("🔥 Initializing Plugin Hot-Reload...")
        self.hot_reload_manager = PluginHotReloadManager(self.jarvis_core.skill_manager)
        if self.hot_reload_manager.start():
            self.plugin_api = PluginAPI(self.hot_reload_manager)
            logger.info("✅ Hot-Reload ready!")
        else:
            logger.warning("⚠️  Could not start Hot-Reload Manager.")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.hot_reload_manager:
            self.hot_reload_manager.stop()
        if self.jarvis_core:
            await self.jarvis_core.cleanup()
        logger.info("🧹 Cleanup complete")

# Global server instance
server = JarvisAPIServer()

# ═══════════════════════════════════════════════════════════════════════════
# WebSocket Handler - Real-time Streaming
# ═══════════════════════════════════════════════════════════════════════════

async def websocket_handler(request):
    """Handle WebSocket connections for streaming AI responses"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    server.active_connections.add(ws)
    
    logger.info(f"📡 New WebSocket connection (total: {len(server.active_connections)})")
    
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                
                if data['type'] == 'chat':
                    await handle_chat_message(ws, data)
                elif data['type'] == 'ping':
                    await ws.send_json({'type': 'pong'})
                    
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f'WebSocket error: {ws.exception()}')
    
    finally:
        server.active_connections.discard(ws)
        logger.info(f"📡 WebSocket closed (remaining: {len(server.active_connections)})")
    
    return ws


async def handle_chat_message(ws: web.WebSocketResponse, data: Dict[str, Any]):
    """Process chat message and stream response"""
    try:
        user_message = data.get('message', '')
        web_search = data.get('webSearch', False)
        thinking_mode = data.get('thinkingMode', False)
        model = data.get('model', None)
        
        if not user_message:
            await ws.send_json({
                'type': 'error',
                'message': 'Empty message'
            })
            return
        
        # Send thinking status
        await ws.send_json({
            'type': 'status',
            'status': 'thinking'
        })
        
        # Build enhanced prompt with modes
        prompt = user_message
        if thinking_mode:
            prompt = f"[Deep Analysis Mode] {prompt}"
        if web_search:
            prompt = f"[Web Search Enabled] {prompt}"
        
        # Stream response from JARVIS
        full_response = ""
        async for chunk in server.jarvis_core._ai_query(prompt, model=model):
            content = chunk.get('message', {}).get('content', '')
            if content:
                full_response += content
                await ws.send_json({
                    'type': 'chunk',
                    'content': content,
                    'full': full_response
                })
        
        # Send completion
        await ws.send_json({
            'type': 'complete',
            'message': full_response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error handling chat: {e}", exc_info=True)
        await ws.send_json({
            'type': 'error',
            'message': str(e)
        })


# ═══════════════════════════════════════════════════════════════════════════
# REST API Endpoints
# ═══════════════════════════════════════════════════════════════════════════

async def health_check(request):
    """Health check endpoint"""
    return web.json_response({
        'status': 'online',
        'jarvis_ready': server.jarvis_core is not None,
        'active_connections': len(server.active_connections),
        'timestamp': datetime.now().isoformat()
    })


async def get_system_status(request):
    """Get system status"""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Get JARVIS stats if available
        jarvis_stats = {}
        if server.jarvis_core and hasattr(server.jarvis_core, 'stats'):
            jarvis_stats = server.jarvis_core.stats
        
        return web.json_response({
            'system': {
                'cpu_usage': f"{cpu_percent}%",
                'memory_used': f"{memory.used / (1024**3):.1f} GB",
                'memory_total': f"{memory.total / (1024**3):.1f} GB",
                'memory_percent': f"{memory.percent}%",
            },
            'jarvis': jarvis_stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def get_plugins(request):
    """Get list of available plugins"""
    if not server.plugin_api:
        return web.json_response({'error': 'Plugin API not ready'}, status=503)
    
    try:
        data = await server.plugin_api.list_plugins()
        return web.json_response(data)
    except Exception as e:
        logger.error(f"Error getting plugins: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def get_plugin_details(request):
    """Get details for a single plugin"""
    if not server.plugin_api:
        return web.json_response({'error': 'Plugin API not ready'}, status=503)
    
    plugin_name = request.match_info.get('name')
    data = await server.plugin_api.get_plugin(plugin_name)
    if 'error' in data:
        return web.json_response(data, status=404)
    return web.json_response(data)

async def reload_plugin_endpoint(request):
    """Reload a specific plugin"""
    if not server.plugin_api:
        return web.json_response({'error': 'Plugin API not ready'}, status=503)
    
    data = await request.json()
    plugin_name = data.get('plugin')
    if not plugin_name:
        return web.json_response({'error': 'Plugin name required'}, status=400)
        
    result = await server.plugin_api.reload_plugin(plugin_name)
    return web.json_response(result)

async def reload_all_plugins_endpoint(request):
    """Reload all plugins"""
    if not server.plugin_api:
        return web.json_response({'error': 'Plugin API not ready'}, status=503)
        
    result = await server.plugin_api.reload_all_plugins()
    return web.json_response(result)

async def create_plugin_endpoint(request):
    """Create a new plugin from a template"""
    if not server.plugin_api:
        return web.json_response({'error': 'Plugin API not ready'}, status=503)
    
    data = await request.json()
    plugin_name = data.get('plugin')
    if not plugin_name:
        return web.json_response({'error': 'Plugin name required'}, status=400)
        
    result = await server.plugin_api.create_plugin(plugin_name)
    if 'error' in result:
        return web.json_response(result, status=400)
    return web.json_response(result)

async def delete_plugin_endpoint(request):
    """Delete a plugin"""
    if not server.plugin_api:
        return web.json_response({'error': 'Plugin API not ready'}, status=503)
    
    data = await request.json()
    plugin_name = data.get('plugin')
    if not plugin_name:
        return web.json_response({'error': 'Plugin name required'}, status=400)
        
    result = await server.plugin_api.delete_plugin(plugin_name)
    if 'error' in result:
        return web.json_response(result, status=400)
    return web.json_response(result)


async def toggle_plugin(request):
    """Enable/disable a plugin"""
    try:
        data = await request.json()
        plugin_id = data.get('plugin_id')
        enabled = data.get('enabled', True)
        
        # TODO: Implement actual plugin enable/disable logic
        # For now, just return success
        
        return web.json_response({
            'success': True,
            'plugin_id': plugin_id,
            'enabled': enabled
        })
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def upload_file(request):
    """Handle file uploads"""
    try:
        reader = await request.multipart()
        uploaded_files = []
        
        async for field in reader:
            if field.name == 'file':
                filename = field.filename
                if not filename:
                    continue
                
                # Save file
                filepath = server.upload_dir / filename
                size = 0
                
                async with aiofiles.open(filepath, 'wb') as f:
                    while True:
                        chunk = await field.read_chunk()
                        if not chunk:
                            break
                        size += len(chunk)
                        await f.write(chunk)
                
                uploaded_files.append({
                    'filename': filename,
                    'path': str(filepath),
                    'size': size,
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"📎 Uploaded file: {filename} ({size} bytes)")
        
        return web.json_response({
            'success': True,
            'files': uploaded_files
        })
        
    except Exception as e:
        logger.error(f"File upload error: {e}", exc_info=True)
        return web.json_response({'error': str(e)}, status=500)


async def get_models(request):
    """Get available Ollama models"""
    try:
        # Query Ollama for available models
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:11434/api/tags') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [
                        {
                            'name': model['name'],
                            'size': model.get('size', 0),
                            'modified': model.get('modified_at', '')
                        }
                        for model in data.get('models', [])
                    ]
                    return web.json_response({'models': models})
                else:
                    return web.json_response({'models': []}, status=503)
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        return web.json_response({'error': str(e)}, status=500)


async def save_settings(request):
    """Save user settings"""
    try:
        settings = await request.json()
        
        # Save to config file
        settings_file = Path("jarvis_ui_settings.json")
        async with aiofiles.open(settings_file, 'w') as f:
            await f.write(json.dumps(settings, indent=2))
        
        logger.info("💾 Settings saved")
        return web.json_response({'success': True})
        
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


async def load_settings(request):
    """Load user settings"""
    try:
        settings_file = Path("jarvis_ui_settings.json")
        
        if settings_file.exists():
            async with aiofiles.open(settings_file, 'r') as f:
                content = await f.read()
                settings = json.loads(content)
        else:
            settings = {
                'theme': 'psychopass',
                'model': 'phi3:3.8b',
                'api_keys': {}
            }
        
        return web.json_response(settings)
        
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


# ═══════════════════════════════════════════════════════════════════════════
# CORS Middleware
# ═══════════════════════════════════════════════════════════════════════════

@web.middleware
async def cors_middleware(request, handler):
    """Add CORS headers"""
    if request.method == 'OPTIONS':
        response = web.Response()
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = ex
    
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-control-allow-methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    return response


# ═══════════════════════════════════════════════════════════════════════════
# App Setup
# ═══════════════════════════════════════════════════════════════════════════

async def init_app():
    """Initialize the web application"""
    await server.initialize()
    
    app = web.Application(middlewares=[cors_middleware])
    
    # WebSocket route
    app.router.add_get('/ws', websocket_handler)
    
    # REST API routes
    app.router.add_get('/api/health', health_check)
    app.router.add_get('/api/status', get_system_status)
    
    # Plugin Management
    app.router.add_get('/api/plugins', get_plugins)
    app.router.add_get('/api/plugins/{name}', get_plugin_details)
    app.router.add_post('/api/plugins/toggle', toggle_plugin)
    app.router.add_post('/api/plugins/reload', reload_plugin_endpoint)
    app.router.add_post('/api/plugins/reload-all', reload_all_plugins_endpoint)
    app.router.add_post('/api/plugins/create', create_plugin_endpoint)
    app.router.add_post('/api/plugins/delete', delete_plugin_endpoint)

    app.router.add_post('/api/upload', upload_file)
    app.router.add_get('/api/models', get_models)
    app.router.add_post('/api/settings', save_settings)
    app.router.add_get('/api/settings', load_settings)
    
    return app


async def cleanup_app(app):
    """Cleanup on shutdown"""
    await server.cleanup()


# ═══════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Start the API server"""
    app = asyncio.run(init_app())
    
    # Register cleanup
    app.on_cleanup.append(lambda app: asyncio.create_task(cleanup_app(app)))
    
    # Run server
    port = int(os.getenv('JARVIS_API_PORT', '8080'))
    logger.info(f"🚀 JARVIS API Server starting on http://localhost:{port}")
    logger.info(f"📡 WebSocket endpoint: ws://localhost:{port}/ws")
    
    web.run_app(app, host='0.0.0.0', port=port)


if __name__ == "__main__":
    main()
