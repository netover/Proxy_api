from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class NotificationChannel(str, Enum):
    LOG = "log"
    EMAIL = "email"
    WEBHOOK = "webhook"

class Alert(BaseModel):
    """
    A placeholder model for an Alert.
    The fields are guesses based on common alert properties.
    """
    id: str
    message: str
    severity: str = "info"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    rule_name: Optional[str] = None
    status: str = "active"

class AlertRule(BaseModel):
    """
    A placeholder model for an Alert Rule.
    """
    name: str
    description: Optional[str] = None
    metric: str
    condition: str
    threshold: float
    severity: str = "warning"
    enabled: bool = True
