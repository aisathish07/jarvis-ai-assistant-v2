"""
═══════════════════════════════════════════════════════════════════════════════
FILE: model_router_optimized.py
DESCRIPTION: RTX 3050 optimized model routing
═══════════════════════════════════════════════════════════════════════════════
"""

import re
from typing import Dict
from jarvis_vram_manager import AdvancedVRAMManager

class OptimizedModelRouter:
    """RTX 3050 optimized model router"""
    
    def __init__(self):
        self.vram_manager = AdvancedVRAMManager()
        
        # Model priorities for RTX 3050
        self.model_priorities = {
            "quick": "gemma:2b",      # Fastest, lightest
            "general": "phi3:3.8b",   # Balanced performance
            "coding": "deepseek-coder:6.7b",  # Code-specific
            "creative": "phi3:3.8b",  # Use balanced for creative
            "long": "phi3:3.8b"       # Better for long context
        }
    
    def pick_optimal_model(self, text: str) -> str:
        """Pick optimal model based on content and system status"""
        text_lower = text.lower().strip()
        word_count = len(text_lower.split())
        
        # Get system status
        system_status = self.vram_manager.get_system_status()
        vram_used = system_status["vram"]["used"]
        
        # Force lightweight model if VRAM is critical
        if vram_used > 3.5:
            return "gemma:2b"
        
        # Determine task type
        task_type = self._classify_task(text_lower, word_count)
        
        # Select model based on task type and system status
        return self._select_model(task_type, vram_used)
    
    def _classify_task(self, text: str, word_count: int) -> str:
        """Classify the type of task"""
        
        # Quick responses
        if word_count <= 5 or re.match(r"^(hi|hello|hey|ok|thanks|yes|no)\b", text):
            return "quick"
        
        # Coding tasks
        if any(kw in text for kw in ["code", "python", "function", "def ", "class ", "import "]):
            return "coding"
        
        # Creative tasks
        if any(kw in text for kw in ["write", "story", "poem", "creative", "imagine"]):
            return "creative"
        
        # Long context
        if word_count > 30:
            return "long"
        
        # Default to general
        return "general"
    
    def _select_model(self, task_type: str, vram_used: float) -> str:
        """Select model based on task and system load"""
        
        # Use lighter models when system is under load
        if vram_used > 3.0:
            if task_type in ["quick", "general"]:
                return "gemma:2b"
            else:
                return "phi3:3.8b"
        
        # Normal operation - use task-specific models
        return self.model_priorities.get(task_type, "phi3:3.8b")
    
    def get_routing_info(self, text: str) -> Dict:
        """Get detailed routing information"""
        model = self.pick_optimal_model(text)
        system_status = self.vram_manager.get_system_status()
        
        return {
            "selected_model": model,
            "reasoning": f"Selected {model} based on content analysis",
            "system_status": system_status,
            "vram_used": system_status["vram"]["used"],
            "recommendation": system_status["load_recommendation"]
        }