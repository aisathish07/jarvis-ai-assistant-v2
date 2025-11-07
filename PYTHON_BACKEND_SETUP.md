# JARVIS Python Backend Setup

## Overview
This document explains how to set up your Python JARVIS backend to work with the web frontend.

## Required API Endpoints

Your Python backend needs to expose the following endpoints on `http://localhost:8000`:

### 1. Health Check
```python
@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

### 2. Chat Endpoint
```python
@app.post("/chat")
async def chat(
    message: str = Form(...),
    mode: str = Form("thinking"),
    history: Optional[str] = Form(None),
    files: List[UploadFile] = File(None)
):
    # Parse history if provided
    conversation_history = json.loads(history) if history else []
    
    # Process files if any
    uploaded_files = []
    if files:
        for file in files:
            content = await file.read()
            uploaded_files.append({
                "filename": file.filename,
                "content": content
            })
    
    # Your JARVIS logic here
    response = your_jarvis_function(message, mode, conversation_history, uploaded_files)
    
    return {
        "response": response,
        "mode": mode,
        "timestamp": datetime.now().isoformat()
    }
```

### 3. System Status Endpoint
```python
@app.get("/status")
async def get_status():
    return {
        "gpu_usage": get_gpu_usage(),  # Your GPU monitoring code
        "vram_usage": get_vram_usage(),
        "ram_usage": get_ram_usage(),
        "active_model": "Your Model Name",
        "performance_mode": "turbo"  # or "normal", "eco"
    }
```

### 4. Plugins Endpoint
```python
@app.get("/plugins")
async def get_plugins():
    return [
        {
            "id": "plugin1",
            "name": "Plugin Name",
            "description": "Plugin description",
            "enabled": True,
            "version": "1.0.0"
        }
    ]

@app.patch("/plugins/{plugin_id}")
async def toggle_plugin(plugin_id: str, enabled: bool):
    # Your plugin toggle logic
    return {"success": True}
```

## Quick Start with FastAPI

1. Install FastAPI:
```bash
pip install fastapi uvicorn python-multipart
```

2. Create a basic server (jarvis_api.py):
```python
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
from datetime import datetime

app = FastAPI()

# Enable CORS for the web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/chat")
async def chat(
    message: str = Form(...),
    mode: str = Form("thinking"),
    history: Optional[str] = Form(None),
):
    # Import your JARVIS logic here
    # from jarvis_core_optimized import process_message
    
    # For now, echo back
    response = f"JARVIS received: {message}"
    
    return {
        "response": response,
        "mode": mode,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def get_status():
    return {
        "gpu_usage": 45.2,
        "vram_usage": 6.8,
        "ram_usage": 8.4,
        "active_model": "Gemini-Flash",
        "performance_mode": "turbo"
    }

@app.get("/plugins")
async def get_plugins():
    return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

3. Run the server:
```bash
python jarvis_api.py
```

## Integration with Your Existing Code

Look at your uploaded files and integrate:
- `jarvis_core_optimized.py` - Your main JARVIS logic
- `model_router.py` - Model routing
- `jarvis_turbo_manager.py` - Performance management

Wrap these in the FastAPI endpoints above.

## Testing the Connection

1. Start your Python backend: `python jarvis_api.py`
2. The web frontend will automatically detect the connection
3. You'll see "Connected" badge in the top right
4. Start chatting!

## Offline Operation

Once set up:
- Install the PWA on Windows (browser menu → Install JARVIS)
- Run Python backend locally
- Everything works offline, no internet needed
- The web app caches all assets for offline use

## Troubleshooting

**Frontend shows "Offline":**
- Check if Python backend is running on port 8000
- Verify no firewall blocking localhost:8000
- Check browser console for CORS errors

**Messages not working:**
- Ensure `/chat` endpoint returns proper JSON format
- Check Python backend console for errors
- Verify FastAPI is handling multipart/form-data correctly
