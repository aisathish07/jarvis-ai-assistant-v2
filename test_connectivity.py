# test_connectivity.py
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_connectivity():
    from jarvis_core_optimized import JarvisOptimizedCore
    
    print("🧪 Testing JARVIS Connectivity...")
    
    # Initialize
    jarvis = JarvisOptimizedCore(enable_voice=False)
    await jarvis.initialize()
    
    print("✅ All systems initialized")
    
    # Test queries that should route to different systems
    test_cases = [
        ("ping", "Should go to test skill"),
        ("open notepad", "Should go to app control"), 
        ("system status", "Should go to system skill"),
        ("what's the weather", "Should go to weather skill"),
        ("remind me to test", "Should go to scheduler"),
        ("write a poem", "Should go to AI/turbo")
    ]
    
    for query, expected in test_cases:
        print(f"\n🔍 Testing: '{query}'")
        print(f"   Expected: {expected}")
        
        try:
            response = await jarvis.process_query(query, speak=False)
            print(f"   ✅ Response: {response[:80]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Print final status
    print("\n📊 Final System Status:")
    jarvis.print_status()
    
    await jarvis.cleanup()

if __name__ == "__main__":
    asyncio.run(test_connectivity())