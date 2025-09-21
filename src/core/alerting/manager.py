import logging
from typing import Any

logger = logging.getLogger(__name__)

class AlertManager:
    """
    A placeholder for the Alerting module.
    This is a mock implementation to allow the application to start.
    """
    def __init__(self):
        logger.warning("AlertManager is a placeholder. Alerting is not functional.")

    async def start_monitoring(self):
        """
        Accepts configuration but does nothing.
        """
        logger.info("AlertManager.start_monitoring() called (placeholder).")
        pass

    async def stop_monitoring(self):
        """
        Accepts configuration but does nothing.
        """
        logger.info("AlertManager.stop_monitoring() called (placeholder).")
        pass

# Create a single global instance
alert_manager = AlertManager()
