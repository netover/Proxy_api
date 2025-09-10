from fastapi import Request
from typing import List
import hashlib
import time
from src.providers.base import get_provider
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

async def condense_context(request: Request, chunks: List[str], max_tokens: int = 512) -> str:
    """
    Usa o provider de maior prioridade para resumir mensagens longas.
    """
    cache = request.app.state.cache
    condensation_config = request.app.state.condensation_config
    
    # Compute adaptive max_tokens
    original_size = sum(len(c) for c in chunks)
    adaptive_max_tokens = min(original_size * condensation_config.adaptive_factor, condensation_config.max_tokens_default)
    use_max_tokens = adaptive_max_tokens  # Override passed max_tokens with adaptive
    
    # Cache key
    chunk_hash = hashlib.md5(''.join(chunks).encode()).hexdigest()
    
    # Check cache
    if chunk_hash in cache:
        summary, timestamp = cache[chunk_hash]
        if time.time() - timestamp < condensation_config.cache_ttl:
            return summary
    
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
                f"limitando a {use_max_tokens} tokens."
            },
            {"role": "user", "content": content}
        ],
        "max_tokens": use_max_tokens
    }

    # Chama provider with timeout
    try:
        async with asyncio.timeout(top_cfg.timeout):
            resp = await provider.create_completion(request_body)
    except asyncio.TimeoutError:
        raise ValueError("Condensation timed out")
    except Exception:
        raise ValueError("Condensation failed")
    
    summary = resp["choices"][0]["message"]["content"]
    
    # Store in cache
    cache[chunk_hash] = (summary, time.time())
    
    return summary