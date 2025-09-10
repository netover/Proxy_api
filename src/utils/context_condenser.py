from fastapi import Request
from typing import List
from src.providers.base import get_provider
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

async def condense_context(request: Request, chunks: List[str], max_tokens: int = 512) -> str:
    """
    Usa o provider de maior prioridade para resumir mensagens longas.
    """
    # Carrega config e escolhe provider priority=1
    config = request.app.state.config.providers  # Adapted to use app.state
    enabled_providers = [p for p in config if p.enabled]
    if not enabled_providers:
        raise ValueError("No enabled providers available for condensation")
    top_cfg = sorted(enabled_providers, key=lambda p: p.priority)[0]
    provider = await get_provider(top_cfg)

    # Monta prompt de resumo
    content = "\n\n---\n\n".join(chunks)
    request_body = {
        "model": top_cfg.models[0],
        "messages": [
            {"role": "system", "content":
                f"Resuma mantendo entidades e intents, "
                f"limitando a {max_tokens} tokens."
            },
            {"role": "user", "content": content}
        ],
        "max_tokens": max_tokens
    }

    # Chama provider
    resp = await provider.create_completion(request_body)
    return resp["choices"][0]["message"]["content"]