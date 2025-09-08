from pydantic import BaseModel, HttpUrl, Field
from typing import List

class ProviderConfig(BaseModel):
    name: str
    module: str
    class_: str = Field(alias='class')
    api_key_env: str
    base_url: HttpUrl
    models: List[str]
    priority: int
