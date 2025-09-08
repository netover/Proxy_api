#!/usr/bin/env python3
"""
Test script to verify dynamic provider loading
"""

import asyncio
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.provider_loader import instantiate_providers

async def test_provider_loading():
    """Test that providers can be loaded dynamically"""
    print("Testing dynamic provider loading...")
    
    try:
        providers = instantiate_providers()
        print(f"Successfully loaded {len(providers)} providers:")
        
        for provider in providers:
            print(f"  - {provider.name} (priority: {provider.priority})")
            print(f"    Models: {provider.models}")
            
        return True
    except Exception as e:
        print(f"Error loading providers: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_provider_loading())
    if result:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
