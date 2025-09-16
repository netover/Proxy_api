import asyncio
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


def safe_background_task(func):
    """Wrapper for background tasks with proper exception handling"""

    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except asyncio.CancelledError:
            logger.info(f"Background task {func.__name__} was cancelled")
        except Exception as e:
            logger.error(
                f"Background task {func.__name__} failed: {e}", exc_info=True
            )

    return wrapper
