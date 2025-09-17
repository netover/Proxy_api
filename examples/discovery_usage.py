"""Example usage of the new provider discovery capabilities."""

import asyncio
import os
from src.core.provider_factory import ProviderFactory, ProviderConfig, ProviderType
from src.models.model_info import ModelInfo


async def demonstrate_discovery():
    """Demonstrate the new model discovery capabilities."""
    
    # Setup test environment
    os.environ['OPENAI_API_KEY'] = 'your-api-key-here'
    
    # Create provider factory
    factory = ProviderFactory()
    
    # Configure OpenAI provider
    openai_config = ProviderConfig(
        name="openai-discovery",
        type=ProviderType.OPENAI,
        base_url="https://api.openai.com",
        api_key_env="OPENAI_API_KEY",
        models=["gpt-4", "gpt-3.5-turbo"],  # Initial models
        priority=1,
        enabled=True
    )
    
    try:
        # Initialize provider
        provider = await factory.create_provider(openai_config)
        factory._providers[openai_config.name] = provider
        
        print("=== Provider Discovery Demo ===")
        print(f"Provider: {provider.name}")
        print(f"Discovery enabled: {factory.is_discovery_enabled(provider.name)}")
        
        # Get discovery-enabled providers
        discovery_providers = await factory.get_discovery_enabled_providers()
        print(f"Discovery-enabled providers: {discovery_providers}")
        
        # Example 1: List all available models
        print("\n--- Example 1: List All Models ---")
        try:
            models = await provider.list_models()
            print(f"Found {len(models)} models:")
            for model in models[:5]:  # Show first 5
                print(f"  - {model.id} (by {model.owned_by}, created: {model.created_datetime})")
        except Exception as e:
            print(f"Could not list models: {e}")
        
        # Example 2: Retrieve specific model
        print("\n--- Example 2: Retrieve Specific Model ---")
        try:
            model_info = await provider.retrieve_model("gpt-4")
            if model_info:
                print("GPT-4 details:")
                print(f"  ID: {model_info.id}")
                print(f"  Owner: {model_info.owned_by}")
                print(f"  Created: {model_info.created_datetime}")
            else:
                print("GPT-4 not found")
        except Exception as e:
            print(f"Could not retrieve model: {e}")
        
        # Example 3: Validate model
        print("\n--- Example 3: Validate Model ---")
        try:
            is_valid = await provider.validate_model("gpt-3.5-turbo")
            print(f"GPT-3.5-turbo is valid: {is_valid}")
        except Exception as e:
            print(f"Could not validate model: {e}")
        
        # Example 4: Search models
        print("\n--- Example 4: Search Models ---")
        try:
            gpt_models = await provider.search_models("gpt")
            print(f"Found {len(gpt_models)} GPT models:")
            for model in gpt_models:
                print(f"  - {model.id}")
        except Exception as e:
            print(f"Could not search models: {e}")
        
        # Example 5: Get models by owner
        print("\n--- Example 5: Models by Owner ---")
        try:
            openai_models = await provider.get_models_by_owner("openai")
            print(f"Found {len(openai_models)} OpenAI models")
        except Exception as e:
            print(f"Could not get models by owner: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await factory.shutdown()


if __name__ == "__main__":
    asyncio.run(demonstrate_discovery())