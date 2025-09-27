import asyncio
import os
from src.core.unified_config import config_manager
from src.core.providers.factory import provider_factory

async def test_health_checks():
    try:
        config_manager.load_config("config.yaml")
        config = config_manager.get_config()

        print('🩺 TESTANDO HEALTH CHECKS REAIS:')

        # Set dummy API keys for testing
        os.environ['OPENAI_API_KEY'] = 'dummy_key_for_testing'
        os.environ['ANTHROPIC_API_KEY'] = 'dummy_key_for_testing'
        os.environ['AZURE_OPENAI_KEY'] = 'dummy_key_for_testing'

        # Initialize providers
        providers = await provider_factory.initialize(config)

        if not providers:
            print('❌ Nenhum provider foi inicializado - verifique as configurações e chaves de API')
            return

        for name, provider in providers.items():
            print(f'🔍 Testando {name}...')
            try:
                health = await provider.health_check()
                status = '✅' if health.get('healthy', False) else '❌'
                response_time = health.get('response_time', 0)
                print(f'{status} {name}: {health.get("status", "unknown")} ({response_time:.2f}ms)')

                if not health.get('healthy', False):
                    print(f'   Error: {health.get("error", "Unknown error")}')
                    print(f'   Error Type: {health.get("error_type", "Unknown")}')
                else:
                    print(f'   Models: {health.get("models_count", 0)}')
                    print(f'   Model used: {health.get("model_used", "unknown")}')
                    if 'details' in health:
                        print(f'   Details: {health["details"]}')

            except Exception as e:
                print(f'❌ {name}: Exception - {e}')

    except Exception as e:
        print(f'❌ Test failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_health_checks())
