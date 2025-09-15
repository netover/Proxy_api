import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file before any tests run
load_dotenv()

# Set a default test API key if it's not already set.
# pydantic-settings expects a JSON-formatted string for list types.
if "PROXY_API_KEYS" not in os.environ:
    os.environ["PROXY_API_KEYS"] = json.dumps(["test-key-from-conftest"])
