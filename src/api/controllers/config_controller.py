"""
Configuration management endpoints for hot reload
"""

import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.core.logging import ContextualLogger
from src.core.rate_limiter import rate_limiter
from src.core.unified_config import config_manager

logger = ContextualLogger(__name__)
router = APIRouter()


class ConfigReloadResponse(BaseModel):
    """Response model for config reload operations"""

    success: bool
    message: str
    reload_time_ms: float
    config_version: Optional[str] = None
    changes_detected: bool = False


class ConfigStatusResponse(BaseModel):
    """Response model for config status"""

    current_config_path: str
    last_modified: Optional[float] = None
    cache_status: Dict[str, Any]
    file_watching_enabled: bool = False


@router.post("/reload", response_model=ConfigReloadResponse)
@rate_limiter.limit(route="/v1/config/reload")
async def reload_configuration(request: Request) -> ConfigReloadResponse:
    """
    Force reload of configuration from disk

    This endpoint triggers a complete reload of the configuration,
    invalidating all caches and reloading from the config file.
    Useful for applying configuration changes without restarting the service.
    """
    start_time = time.time()

    try:
        # Force reload configuration
        old_config = config_manager._config
        new_config = config_manager.load_config(force_reload=True)

        reload_time = (time.time() - start_time) * 1000

        # Check if changes were detected
        changes_detected = old_config != new_config if old_config else True

        # Update app state if available
        if hasattr(request.app.state, "config"):
            request.app.state.config = new_config
            request.app.state.condensation_config = (
                new_config.settings.condensation
            )

        # Update config mtime for dynamic reload tracking
        if hasattr(request.app.state, "config_mtime"):
            import os

            if config_manager.config_path.exists():
                request.app.state.config_mtime = os.path.getmtime(
                    config_manager.config_path
                )

        logger.info(
            "Configuration reloaded successfully",
            reload_time_ms=reload_time,
            changes_detected=changes_detected,
        )

        return ConfigReloadResponse(
            success=True,
            message="Configuration reloaded successfully",
            reload_time_ms=round(reload_time, 2),
            config_version=getattr(
                new_config.settings, "app_version", "unknown"
            ),
            changes_detected=changes_detected,
        )

    except Exception as e:
        reload_time = (time.time() - start_time) * 1000
        logger.error(
            "Configuration reload failed",
            error=str(e),
            reload_time_ms=reload_time,
        )

        raise HTTPException(
            status_code=500, detail=f"Configuration reload failed: {str(e)}"
        )


@router.get("/status", response_model=ConfigStatusResponse)
@rate_limiter.limit(route="/v1/config/status")
async def get_config_status(request: Request) -> ConfigStatusResponse:
    """
    Get current configuration status and cache information
    """
    try:
        # Get file modification time
        last_modified = None
        if config_manager.config_path.exists():
            last_modified = config_manager.config_path.stat().st_mtime

        # Get cache status from optimized loader
        from src.core.optimized_config import config_loader

        cache_stats = config_loader.get_performance_stats()

        # Check if file watching is enabled
        file_watching_enabled = (
            hasattr(config_loader, "observer")
            and config_loader.observer is not None
        )

        return ConfigStatusResponse(
            current_config_path=str(config_manager.config_path),
            last_modified=last_modified,
            cache_status=cache_stats,
            file_watching_enabled=file_watching_enabled,
        )

    except Exception as e:
        logger.error("Failed to get config status", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get config status: {str(e)}"
        )


@router.post("/invalidate-cache")
@rate_limiter.limit(route="/v1/config/invalidate-cache")
async def invalidate_config_cache(request: Request):
    """
    Invalidate configuration cache without reloading

    This forces the next config access to reload from disk,
    but doesn't immediately reload the configuration.
    """
    try:
        from src.core.optimized_config import config_loader

        config_loader.invalidate_cache()

        logger.info("Configuration cache invalidated")

        return {
            "success": True,
            "message": "Configuration cache invalidated successfully",
        }

    except Exception as e:
        logger.error("Failed to invalidate config cache", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate config cache: {str(e)}",
        )
