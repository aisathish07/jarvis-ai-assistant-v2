"""
═══════════════════════════════════════════════════════════════════════════════
FILE: jarvis_vram_manager.py
DESCRIPTION: Advanced VRAM management for RTX 3050 4GB
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import subprocess
import logging
from typing import Dict, List
import psutil

logger = logging.getLogger("Jarvis.VRAM")

class AdvancedVRAMManager:
    """Advanced VRAM management for RTX 3050 4GB"""
    
    def __init__(self):
        self.vram_limit = 3.8  # Leave 200MB buffer for system
        self.model_sizes = {
            "gemma:2b": 1.6,
            "phi3:3.8b": 2.1,
            "deepseek-coder:6.7b": 3.9,
            "llama3.1:8b": 4.2,
            "mistral:7b": 4.1,
            "dolphin-llama3:8b": 4.2
        }
        self._has_nvidia = self._check_nvidia()
    
    def _check_nvidia(self) -> bool:
        """Check if nvidia-smi is available"""
        try:
            subprocess.run(["nvidia-smi", "--version"], capture_output=True, timeout=2)
            return True
        except Exception:
            logger.warning("nvidia-smi not found - VRAM monitoring disabled")
            return False
    
    def get_vram_usage(self) -> Dict[str, float]:
        """Get current VRAM usage in GB"""
        if not self._has_nvidia:
            return {"used": 0.0, "total": 4.0, "free": 4.0}
        
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.used,memory.total,memory.free",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                used, total, free = map(float, result.stdout.strip().split(","))
                return {
                    "used": used / 1024,   # Convert MB to GB
                    "total": total / 1024,
                    "free": free / 1024
                }
        except Exception as e:
            logger.error(f"VRAM monitoring error: {e}")
        
        return {"used": 0.0, "total": 4.0, "free": 4.0}
    
    def can_load_model(self, model: str) -> bool:
        """Check if model can be loaded without exceeding VRAM"""
        model_size = self.model_sizes.get(model, 3.0)
        vram = self.get_vram_usage()
        available_vram = vram["free"]
        
        # Check if we have enough space with 300MB buffer
        return available_vram >= (model_size + 0.3)
    
    async def emergency_cleanup(self):
        """Emergency VRAM cleanup when running low"""
        logger.warning("⚠️ Performing emergency VRAM cleanup")
        vram = self.get_vram_usage()
        
        if vram["used"] > 3.5:  # Critical level
            # Try to free system memory first
            import gc
            gc.collect()
            
            # Clear CUDA cache if available
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            
            logger.info("✅ Emergency VRAM cleanup completed")
    
    def get_optimal_model(self, task_type: str, text_length: int) -> str:
        """Get optimal model based on task and text length"""
        if text_length <= 100:  # Short queries
            return "gemma:2b"
        elif "code" in task_type.lower() or "programming" in task_type.lower():
            return "deepseek-coder:6.7b"
        elif text_length > 500:  # Long context
            return "phi3:3.8b"
        else:  # Balanced choice
            return "phi3:3.8b"
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        vram = self.get_vram_usage()
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "vram": vram,
            "ram": {
                "used": memory.used / (1024**3),
                "total": memory.total / (1024**3),
                "percent": memory.percent
            },
            "cpu": cpu_percent,
            "load_recommendation": self.get_load_recommendation()
        }
    
    def get_load_recommendation(self) -> str:
        """Get recommendation for model loading"""
        vram = self.get_vram_usage()
        
        if vram["used"] > 3.5:
            return "CRITICAL: Avoid loading new models"
        elif vram["used"] > 3.0:
            return "HIGH: Load only small models"
        elif vram["used"] > 2.0:
            return "MEDIUM: Can load medium models"
        else:
            return "LOW: Can load any model"