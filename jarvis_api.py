from fastapi import FastAPI, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
from datetime import datetime
import asyncio
import psutil

from jarvis_core_optimized import JarvisOptimizedCore, create_jarvis
from jarvis_turbo_manager import OptimizedTurboManager, TurboProfile
from jarvis_skills import SkillManager

app = FastAPI()

# Enable CORS for the web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global JARVIS instance
jarvis_instance: Optional[JarvisOptimizedCore] = None

@app.on_event("startup")
async def startup_event():
    global jarvis_instance
    jarvis_instance = await create_jarvis(enable_voice=False) # Disable voice for API

@app.on_event("shutdown")
async def shutdown_event():
    global jarvis_instance
    if jarvis_instance:
        await jarvis_instance.cleanup()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/chat")
async def chat(
    message: str = Form(...),
    mode: str = Form("thinking"),
    history: Optional[str] = Form(None),
    files: List[UploadFile] = File(None)
):
    global jarvis_instance
    if not jarvis_instance:
        return {"response": "JARVIS not initialized.", "mode": "error", "timestamp": datetime.now().isoformat()}

    # Parse history if provided
    conversation_history = json.loads(history) if history else []
    
    # Process files if any (currently not integrated with jarvis_core_optimized.process_query)
    uploaded_files = []
    if files:
        for file in files:
            content = await file.read()
            uploaded_files.append({
                "filename": file.filename,
                "content": content
            })
    
    response = await jarvis_instance.process_query(message, speak=False) # Assuming process_query returns a string
    
    return {
        "response": response,
        "mode": mode,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def get_status():
    global jarvis_instance
    if not jarvis_instance or not jarvis_instance.turbo:
        return {
            "gpu_usage": 0.0,
            "vram_usage": 0.0,
            "ram_usage": psutil.virtual_memory().percent,
            "active_model": "N/A",
            "performance_mode": "N/A"
        }
    
    turbo_status = jarvis_instance.turbo.get_status()
    vram_info = turbo_status["system"]["vram"]
    
    return {
        "gpu_usage": vram_info["used"] / vram_info["total"] * 100 if vram_info["total"] > 0 else 0.0,
        "vram_usage": vram_info["used"],
        "ram_usage": psutil.virtual_memory().percent,
        "active_model": turbo_status["cache"]["current_model"] or "None",
        "performance_mode": turbo_status["profile"]["mode"]
    }

@app.get("/plugins")
async def get_plugins():
    global jarvis_instance
    if not jarvis_instance or not jarvis_instance.skill_manager:
        return []
    
    plugins_list = []
    for skill_name, skill_instance in jarvis_instance.skill_manager.skills.items():
        plugins_list.append({
            "id": skill_name,
            "name": skill_name.replace("Skill", "").replace("_", " ").title(),
            "description": getattr(skill_instance, "description", "No description provided."),
            "enabled": True, # Skills are always enabled once loaded
            "version": getattr(skill_instance, "version", "1.0.0")
        })
    return plugins_list

@app.patch("/plugins/{plugin_id}")
async def toggle_plugin(plugin_id: str, enabled: bool):
    global jarvis_instance
    if not jarvis_instance or not jarvis_instance.skill_manager:
        return {"success": False, "message": "Skill manager not available."}
    
    # The current skill manager doesn't support dynamic enabling/disabling after loading
    # For now, we'll just return success if the skill exists, or failure if not.
    if plugin_id in jarvis_instance.skill_manager.skills:
        # In a real scenario, you'd have logic here to enable/disable the skill
        return {"success": True, "message": f"Skill {plugin_id} status set to {enabled} (functionality not fully implemented)."}
    else:
        return {"success": False, "message": f"Skill {plugin_id} not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
