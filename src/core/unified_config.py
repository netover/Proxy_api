from .config.manager import get_config

from pathlib import Path

class ConfigManager:
    """
    A compatibility layer to provide the 'config_manager' object
    that some parts of the application expect to import.
    """
    def __init__(self):
        self.config_path = Path() # Dummy path

    def load_config(self, force_reload=False):
        """
        Loads the config using the central get_config function.
        """
        return get_config()

config_manager = ConfigManager()
