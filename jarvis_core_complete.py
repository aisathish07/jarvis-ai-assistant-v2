"""
Temporary compatibility file - Use jarvis_core_optimized instead
"""

from jarvis_core_optimized import JarvisOptimizedCore

# For compatibility with old imports
JarvisIntegrated = JarvisOptimizedCore

def interactive_mode():
    from jarvis_core_optimized import interactive_mode as optimized_interactive
    return optimized_interactive()

def demo_mode():
    from jarvis_core_optimized import demo_mode as optimized_demo
    return optimized_demo()

def quick_query_mode(query):
    from jarvis_core_optimized import quick_query_mode as optimized_query
    return optimized_query(query)