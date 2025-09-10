import yaml
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, field_validator, Field, HttpUrl

def get_config_paths() -> Tuple[Path, Path]:
    """Returns paths for bundled and external config files"""
    if getattr(sys, 'frozen', False):
        # Executable: config bundled (read-only) + config external (writable)
        bundle_path = Path(sys._MEIPASS) / "config.yaml"
        external_path = Path(sys.executable).parent / "config.yaml"
    else:
        # Development: both point to the same file
        bundle_path = external_path = Path(__file__).parent.parent.parent / "config.yaml"
    
    return bundle_path, external_path

def create_default_config(config_path: Path) -> Dict[str, Any]:
    """Create and return default configuration"""
    default_config = {
        "providers": [
            {
                "name": "openai",
                "type": "openai",
                "base_url": "https://api.openai.com/v1",
                "api_key_env": "OPENAI_API_KEY",
                "models": ["gpt-3.5-turbo", "gpt-4"],
                "enabled": True,
                "priority": 1,
                "timeout": 30,
                "rate_limit": 1000,
                "retry_attempts": 3,
                "retry_delay": 1.0
            }
        ]
    }

    try:
        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the config file
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(default_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Created default config file: {config_path}")
    except Exception as e:
        print(f"❌ Failed to create default config file: {e}")
    
    return default_config

class ProviderConfig(BaseModel):
    """Configuration for a single provider"""
    name: str = Field(..., description="Unique name for the provider")
    type: str = Field(..., description="Provider type (openai, anthropic, etc.)")
    base_url: HttpUrl = Field(..., description="Base URL for the provider API")
    api_key_env: str = Field(..., description="Environment variable name for API key")
    models: List[str] = Field(..., min_length=1, description="List of supported models")
    enabled: bool = Field(True, description="Whether this provider is enabled")
    priority: int = Field(100, ge=1, le=1000, description="Provider priority (lower = higher priority)")
    timeout: int = Field(30, ge=1, le=300, description="Request timeout in seconds")
    rate_limit: int = Field(1000, ge=1, description="Rate limit requests per hour")
    retry_attempts: int = Field(3, ge=0, le=10, description="Number of retry attempts")
    retry_delay: float = Field(1.0, ge=0.1, le=60.0, description="Delay between retries in seconds")
    headers: Optional[Dict[str, str]] = Field(None, description="Additional headers to send")

    @field_validator('type')
    @classmethod
    def validate_provider_type(cls, v):
        supported_types = ['openai', 'anthropic', 'azure_openai', 'cohere', 'perplexity', 'grok', 'blackbox', 'openrouter']
        if v.lower() not in supported_types:
            raise ValueError(f'Provider type must be one of: {supported_types}')
        return v.lower()

    @field_validator('models')
    @classmethod
    def validate_models(cls, v):
        if not v:
            raise ValueError('At least one model must be specified')
        return list(set(v))  # Remove duplicates


from typing import Dict, Any, Union, Optional, List
from pydantic import BaseModel, Field


class ChatCompletionRequest(BaseModel):
    """Pydantic model for chat completions request"""
    model: str = Field(..., min_length=1)
    messages: List[Dict[str, Any]] = Field(..., min_length=1)
    max_tokens: Optional[int] = Field(None, ge=1)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    n: Optional[int] = Field(1, ge=1)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class CompletionRequest(BaseModel):
    """Pydantic model for completions request"""
    model: str = Field(..., min_length=1)
    prompt: Union[str, List[str]] = Field(..., min_length=1)
    max_tokens: Optional[int] = Field(None, ge=1)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    n: Optional[int] = Field(1, ge=1)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class EmbeddingRequest(BaseModel):
    """Pydantic model for embeddings request"""
    model: str = Field(..., min_length=1)
    input: Union[str, List[str]] = Field(..., min_length=1)
    user: Optional[str] = None


class AppConfig(BaseModel):
    """Main application configuration"""
    providers: List[ProviderConfig] = Field(..., min_length=1)

    @field_validator('providers')
    @classmethod
    def validate_providers(cls, v):
        if not v:
            raise ValueError('At least one provider must be configured')

        # Check for duplicate names
        names = [p.name for p in v]
        if len(names) != len(set(names)):
            raise ValueError('Provider names must be unique')

        # Check for duplicate priorities
        priorities = [p.priority for p in v]
        if len(priorities) != len(set(priorities)):
            raise ValueError('Provider priorities must be unique')

        return v

def load_config() -> AppConfig:
    """Load config with fallback: external -> bundled -> default"""
    bundle_path, external_path = get_config_paths()
    
    # 1st: Try external config (editable by user)
    if external_path.exists():
        try:
            with open(external_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            print(f"✅ Loaded config from: {external_path}")
            return AppConfig(**config_data)
        except Exception as e:
            print(f"⚠️  Error reading external config: {e}")
    
    # 2nd: Try bundled config (read-only)
    if bundle_path.exists():
        try:
            with open(bundle_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            print(f"✅ Loaded bundled config from: {bundle_path}")
            
            # Copy to external for future editing
            try:
                shutil.copy2(bundle_path, external_path)
                print(f"✅ Copied bundled config to: {external_path}")
            except Exception as e:
                print(f"⚠️  Failed to copy config to external location: {e}")
                
            return AppConfig(**config_data)
        except Exception as e:
            print(f"⚠️  Error reading bundled config: {e}")
    
    # 3rd: Create default config
    print("ℹ️  Creating default config...")
    config_data = create_default_config(external_path)
    return AppConfig(**config_data)

def init_config():
    """Initialize config"""
    return load_config()
