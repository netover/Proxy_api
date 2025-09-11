#!/usr/bin/env python3
"""
Test script to verify provider activation/deactivation and "Force this" functionality
"""

import asyncio
import yaml
import tempfile
import os
from pathlib import Path
from src.core.unified_config import config_manager, ProxyConfig, ProviderConfig
from src.core.provider_factory import provider_factory
from src.core.unified_config import ProviderType

async def test_provider_forcing():
    """Test the complete provider forcing functionality"""
    
    print("Testing Provider Activation/Deactivation and Forcing...")
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        test_config = {
            'app_name': 'Test Proxy',
            'api_keys': ['test-key'],
            'providers': [
                {
                    'name': 'openai_test',
                    'type': 'openai',
                    'base_url': 'https://api.openai.com/v1',
                    'api_key_env': 'OPENAI_API_KEY',
                    'models': ['gpt-3.5-turbo'],
                    'enabled': True,
                    'forced': False,
                    'priority': 1
                },
                {
                    'name': 'anthropic_test',
                    'type': 'anthropic',
                    'base_url': 'https://api.anthropic.com',
                    'api_key_env': 'ANTHROPIC_API_KEY',
                    'models': ['claude-3-haiku'],
                    'enabled': True,
                    'forced': False,
                    'priority': 2
                }
            ]
        }
        yaml.dump(test_config, f)
        temp_config_path = f.name
    
    try:
        # Set environment variables for testing
        os.environ['PROXY_API_OPENAI_API_KEY'] = 'test-openai-key'
        os.environ['PROXY_API_ANTHROPIC_API_KEY'] = 'test-anthropic-key'
        
        # Test 1: Load configuration with new fields
        print("\nTest 1: Loading configuration with enabled/forced fields")
        config_manager.config_path = Path(temp_config_path)
        config = config_manager.load_config(force_reload=True)
        
        assert len(config.providers) == 2, "Should have 2 providers"
        assert config.providers[0].enabled == True, "OpenAI should be enabled"
        assert config.providers[0].forced == False, "OpenAI should not be forced"
        assert config.providers[1].enabled == True, "Anthropic should be enabled"
        assert config.providers[1].forced == False, "Anthropic should not be forced"
        print("Configuration loaded successfully")
        
        # Test 2: Set forced provider
        print("Test 2: Setting forced provider")
        config_manager.set_forced_provider('openai_test')
        config = config_manager.load_config(force_reload=True)
        
        forced = config.get_forced_provider()
        assert forced is not None, "Should have a forced provider"
        assert forced.name == 'openai_test', "OpenAI should be forced"
        assert config.providers[1].forced == False, "Anthropic should not be forced"
        print("Forced provider set successfully")
        
        # Test 3: Disable forced provider
        print("Test 3: Disabling forced provider")
        config_manager.toggle_provider_enabled('openai_test', False)
        config = config_manager.load_config(force_reload=True)
        
        forced = config.get_forced_provider()
        assert forced is None, "Should have no forced provider when disabled"
        openai_provider = next(p for p in config.providers if p.name == 'openai_test')
        assert openai_provider.enabled == False, "OpenAI should be disabled"
        assert openai_provider.forced == False, "OpenAI should not be forced when disabled"
        print("Forced provider automatically unset when disabled")
        
        # Test 4: Re-enable and set forced again
        print("Test 4: Re-enabling and setting forced")
        config_manager.toggle_provider_enabled('openai_test', True)
        config_manager.set_forced_provider('openai_test')
        config = config_manager.load_config(force_reload=True)
        
        forced = config.get_forced_provider()
        assert forced.name == 'openai_test', "OpenAI should be forced again"
        print("Provider re-enabled and forced successfully")
        
        # Test 5: Provider selection with forcing
        print("Test 5: Provider selection with forcing")
        
        # Initialize providers
        providers = await provider_factory.initialize_providers(config.providers)
        assert len(providers) == 2, "Should have 2 active providers"
        
        # Test model selection with forcing
        model_providers = await provider_factory.get_providers_for_model('gpt-3.5-turbo')
        assert len(model_providers) == 1, "Should return only forced provider"
        assert model_providers[0].name == 'openai_test', "Should return forced OpenAI provider"
        
        # Test with non-forced model
        model_providers = await provider_factory.get_providers_for_model('claude-3-haiku')
        assert len(model_providers) == 1, "Should return Anthropic for its model"
        assert model_providers[0].name == 'anthropic_test', "Should return Anthropic provider"
        print("Provider selection with forcing works correctly")
        
        # Test 6: Validation - only one forced provider
        print("Test 6: Validation - only one forced provider")
        try:
            # Try to create config with multiple forced providers
            invalid_config = {
                'settings': {'api_keys': ['test']},
                'providers': [
                    {'name': 'p1', 'type': 'openai', 'base_url': 'https://api.openai.com/v1', 'api_key_env': 'KEY1', 'models': ['m1'], 'forced': True},
                    {'name': 'p2', 'type': 'anthropic', 'base_url': 'https://api.anthropic.com', 'api_key_env': 'KEY2', 'models': ['m2'], 'forced': True}
                ]
            }
            ProxyConfig(**invalid_config)
            assert False, "Should have raised validation error"
        except ValueError as e:
            assert "Only one provider can be forced" in str(e)
            print("Validation prevents multiple forced providers")
            
            print("All tests passed! Provider activation/deactivation and forcing functionality is working correctly.")
        
    finally:
        # Cleanup
        os.unlink(temp_config_path)
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        if 'ANTHROPIC_API_KEY' in os.environ:
            del os.environ['ANTHROPIC_API_KEY']

if __name__ == '__main__':
    asyncio.run(test_provider_forcing())