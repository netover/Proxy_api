"""
Alerting system for performance monitoring and system health.

This module provides configurable alerting capabilities for latency, error rates,
resource usage, and system health metrics with multiple notification channels.
"""

import asyncio
import json
import smtplib
import time
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from .logging import ContextualLogger
from .metrics import metrics_collector

logger = ContextualLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""

    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


class NotificationChannel(Enum):
    """Available notification channels"""

    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    LOG = "log"


@dataclass
class AlertRule:
    """Configuration for an alert rule"""

    name: str
    description: str
    metric_path: str  # Dot-separated path to metric (e.g., "system_health.cpu_percent")
    condition: str  # Comparison operator: ">", "<", ">=", "<=", "==", "!="
    threshold: float
    severity: AlertSeverity
    enabled: bool = True
    cooldown_minutes: int = 5  # Minimum time between alerts
    channels: List[NotificationChannel] = field(
        default_factory=lambda: [NotificationChannel.LOG]
    )
    custom_message: Optional[str] = None

    # Runtime state
    last_triggered: float = 0.0
    active: bool = False


@dataclass
class Alert:
    """An active or resolved alert"""

    id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    value: float
    threshold: float
    timestamp: float
    resolved_timestamp: Optional[float] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[float] = None


class NotificationManager:
    """Handles sending notifications through various channels"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def send_email(self, alert: Alert, rule: AlertRule) -> bool:
        """Send alert via email"""
        try:
            email_config = self.config.get("email", {})
            if not email_config.get("enabled", False):
                return False

            msg = MIMEMultipart()
            msg["From"] = email_config.get("from_address", "alerts@proxy-api.com")
            msg["To"] = ", ".join(email_config.get("recipients", []))
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.rule_name}"

            body = """
Alert Details:
- Rule: {alert.rule_name}
- Severity: {alert.severity.value}
- Status: {alert.status.value}
- Message: {alert.message}
- Current Value: {alert.value}
- Threshold: {alert.threshold}
- Time: {datetime.fromtimestamp(alert.timestamp).isoformat()}

Description: {rule.description}
"""
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(
                email_config.get("smtp_server", "localhost"),
                email_config.get("smtp_port", 587),
            )
            if email_config.get("use_tls", True):
                server.starttls()
            if email_config.get("username"):
                server.login(email_config["username"], email_config.get("password", ""))

            server.send_message(msg)
            server.quit()

            logger.info("Email alert sent", alert_id=alert.id, rule=alert.rule_name)
            return True

        except Exception as e:
            logger.error("Failed to send email alert", error=str(e), alert_id=alert.id)
            return False

    async def send_webhook(self, alert: Alert, rule: AlertRule) -> bool:
        """Send alert via webhook"""
        try:
            webhook_config = self.config.get("webhook", {})
            if not webhook_config.get("enabled", False):
                return False

            session = await self._get_session()
            payload = {
                "alert_id": alert.id,
                "rule_name": alert.rule_name,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "message": alert.message,
                "value": alert.value,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp,
                "description": rule.description,
            }

            headers = {"Content-Type": "application/json"}
            if webhook_config.get("auth_token"):
                headers["Authorization"] = f"Bearer {webhook_config['auth_token']}"

            async with session.post(
                webhook_config["url"], json=payload, headers=headers
            ) as response:
                if response.status in (200, 201, 202):
                    logger.info(
                        "Webhook alert sent",
                        alert_id=alert.id,
                        rule=alert.rule_name,
                    )
                    return True
                else:
                    logger.error(
                        "Webhook alert failed",
                        alert_id=alert.id,
                        status=response.status,
                        response=await response.text(),
                    )
                    return False

        except Exception as e:
            logger.error(
                "Failed to send webhook alert", error=str(e), alert_id=alert.id
            )
            return False

    async def send_slack(self, alert: Alert, rule: AlertRule) -> bool:
        """Send alert via Slack webhook"""
        try:
            slack_config = self.config.get("slack", {})
            if not slack_config.get("enabled", False):
                return False

            session = await self._get_session()

            color_map = {
                AlertSeverity.INFO: "good",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.ERROR: "danger",
                AlertSeverity.CRITICAL: "#FF0000",
            }

            payload = {
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "warning"),
                        "title": f"Alert: {alert.rule_name}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value,
                                "short": True,
                            },
                            {
                                "title": "Status",
                                "value": alert.status.value,
                                "short": True,
                            },
                            {
                                "title": "Current Value",
                                "value": f"{alert.value:.2f}",
                                "short": True,
                            },
                            {
                                "title": "Threshold",
                                "value": f"{alert.threshold:.2f}",
                                "short": True,
                            },
                            {
                                "title": "Time",
                                "value": datetime.fromtimestamp(
                                    alert.timestamp
                                ).strftime("%Y-%m-%d %H:%M:%S"),
                                "short": False,
                            },
                        ],
                        "footer": rule.description,
                    }
                ]
            }

            async with session.post(
                slack_config["webhook_url"], json=payload
            ) as response:
                if response.status in (200, 201, 202):
                    logger.info(
                        "Slack alert sent",
                        alert_id=alert.id,
                        rule=alert.rule_name,
                    )
                    return True
                else:
                    logger.error(
                        "Slack alert failed",
                        alert_id=alert.id,
                        status=response.status,
                        response=await response.text(),
                    )
                    return False

        except Exception as e:
            logger.error("Failed to send Slack alert", error=str(e), alert_id=alert.id)
            return False

    async def send_log(self, alert: Alert, rule: AlertRule) -> bool:
        """Send alert to log (always succeeds)"""
        log_data = {
            "alert_id": alert.id,
            "rule_name": alert.rule_name,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "message": alert.message,
            "value": alert.value,
            "threshold": alert.threshold,
            "timestamp": alert.timestamp,
        }

        if alert.severity == AlertSeverity.CRITICAL:
            logger.critical("ALERT TRIGGERED", **log_data)
        elif alert.severity == AlertSeverity.ERROR:
            logger.error("ALERT TRIGGERED", **log_data)
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning("ALERT TRIGGERED", **log_data)
        else:
            logger.info("ALERT TRIGGERED", **log_data)

        return True

    async def notify(self, alert: Alert, rule: AlertRule) -> Dict[str, bool]:
        """Send alert through all configured channels"""
        results = {}

        for channel in rule.channels:
            if channel == NotificationChannel.EMAIL:
                results["email"] = await self.send_email(alert, rule)
            elif channel == NotificationChannel.WEBHOOK:
                results["webhook"] = await self.send_webhook(alert, rule)
            elif channel == NotificationChannel.SLACK:
                results["slack"] = await self.send_slack(alert, rule)
            elif channel == NotificationChannel.LOG:
                results["log"] = await self.send_log(alert, rule)

        return results

    async def close(self):
        """Close the notification manager"""
        if self._session and not self._session.closed:
            await self._session.close()


class AlertManager:
    """Main alerting system manager"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = (
            Path(config_path) if config_path else Path("alert_config.json")
        )
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.notification_manager: Optional[NotificationManager] = None
        self._check_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        # Load configuration
        self.load_config()

        # Initialize notification manager
        self.notification_manager = NotificationManager(
            self.config.get("notifications", {})
        )

        # Default alert rules
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Set up default alert rules for common monitoring scenarios"""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                description="CPU usage is above threshold",
                metric_path="system_health.cpu_percent",
                condition=">",
                threshold=85.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=10,
                channels=[NotificationChannel.LOG, NotificationChannel.EMAIL],
            ),
            AlertRule(
                name="high_memory_usage",
                description="Memory usage is above threshold",
                metric_path="system_health.memory_percent",
                condition=">",
                threshold=90.0,
                severity=AlertSeverity.ERROR,
                cooldown_minutes=5,
                channels=[NotificationChannel.LOG, NotificationChannel.EMAIL],
            ),
            AlertRule(
                name="low_disk_space",
                description="Disk usage is above threshold",
                metric_path="system_health.disk_percent",
                condition=">",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=15,
                channels=[
                    NotificationChannel.LOG,
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                ],
            ),
            AlertRule(
                name="high_error_rate",
                description="Overall error rate is above threshold",
                metric_path="error_rates.error_rate_percent",
                condition=">",
                threshold=10.0,
                severity=AlertSeverity.ERROR,
                cooldown_minutes=5,
                channels=[NotificationChannel.LOG, NotificationChannel.EMAIL],
            ),
            AlertRule(
                name="cache_high_miss_rate",
                description="Cache miss rate is above threshold",
                metric_path="cache_performance.hit_rate",
                condition="<",
                threshold=70.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=10,
                channels=[NotificationChannel.LOG],
            ),
            AlertRule(
                name="connection_pool_exhausted",
                description="Connection pool utilization is high",
                metric_path="connection_pool.active_connections",
                condition=">",
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=5,
                channels=[NotificationChannel.LOG],
            ),
        ]

        # Only add default rules if they don't already exist
        for rule in default_rules:
            if rule.name not in self.rules:
                self.rules[rule.name] = rule

    def load_config(self):
        """Load alert configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config = data.get("config", {})
                    # Load custom rules
                    for rule_data in data.get("rules", []):
                        rule = AlertRule(**rule_data)
                        self.rules[rule.name] = rule
            else:
                self.config = {
                    "notifications": {
                        "email": {"enabled": False},
                        "webhook": {"enabled": False},
                        "slack": {"enabled": False},
                    },
                    "check_interval_seconds": 30,
                    "max_alert_history_days": 7,
                }
        except Exception as e:
            logger.error("Failed to load alert configuration", error=str(e))
            self.config = {}

    def save_config(self):
        """Save alert configuration to file"""
        try:
            data = {
                "config": self.config,
                "rules": [rule.__dict__ for rule in self.rules.values()],
            }
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save alert configuration", error=str(e))

    def add_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.rules[rule.name] = rule
        self.save_config()
        logger.info("Alert rule added", rule_name=rule.name)

    def remove_rule(self, rule_name: str):
        """Remove an alert rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            self.save_config()
            logger.info("Alert rule removed", rule_name=rule_name)

    def update_rule(self, rule: AlertRule):
        """Update an existing alert rule"""
        if rule.name in self.rules:
            self.rules[rule.name] = rule
            self.save_config()
            logger.info("Alert rule updated", rule_name=rule.name)

    def _get_metric_value(self, metric_path: str) -> Optional[float]:
        """Extract metric value from metrics collector using dot notation"""
        try:
            stats = metrics_collector.get_all_stats()
            keys = metric_path.split(".")
            value = stats

            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None

            return float(value) if value is not None else None
        except Exception as e:
            logger.debug(
                "Failed to get metric value",
                metric_path=metric_path,
                error=str(e),
            )
            return None

    def _evaluate_condition(
        self, value: float, condition: str, threshold: float
    ) -> bool:
        """Evaluate alert condition"""
        if condition == ">":
            return value > threshold
        elif condition == "<":
            return value < threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return abs(value - threshold) < 0.001  # Float comparison
        elif condition == "!=":
            return abs(value - threshold) >= 0.001
        else:
            logger.warning("Unknown condition operator", condition=condition)
            return False

    async def _check_alerts(self):
        """Check all alert rules and trigger alerts as needed"""
        try:
            current_time = time.time()

            for rule in self.rules.values():
                if not rule.enabled:
                    continue

                # Check cooldown period
                if current_time - rule.last_triggered < (rule.cooldown_minutes * 60):
                    continue

                # Get metric value
                value = self._get_metric_value(rule.metric_path)
                if value is None:
                    continue

                # Evaluate condition
                condition_met = self._evaluate_condition(
                    value, rule.condition, rule.threshold
                )

                alert_key = f"{rule.name}_{rule.metric_path}"

                if condition_met:
                    # Create or update alert
                    if alert_key not in self.active_alerts:
                        # New alert
                        alert = Alert(
                            id=f"{rule.name}_{int(current_time)}",
                            rule_name=rule.name,
                            severity=rule.severity,
                            status=AlertStatus.ACTIVE,
                            message=rule.custom_message
                            or f"{rule.description}: {value:.2f} {rule.condition} {rule.threshold}",
                            value=value,
                            threshold=rule.threshold,
                            timestamp=current_time,
                        )
                        self.active_alerts[alert_key] = alert

                        # Send notifications
                        if self.notification_manager:
                            await self.notification_manager.notify(alert, rule)

                        logger.info(
                            "Alert triggered",
                            alert_id=alert.id,
                            rule=rule.name,
                            value=value,
                        )

                    rule.last_triggered = current_time
                    rule.active = True

                else:
                    # Check if we need to resolve an active alert
                    if alert_key in self.active_alerts:
                        alert = self.active_alerts[alert_key]
                        if alert.status == AlertStatus.ACTIVE:
                            alert.status = AlertStatus.RESOLVED
                            alert.resolved_timestamp = current_time

                            # Send resolution notification
                            if self.notification_manager:
                                await self.notification_manager.notify(alert, rule)

                            logger.info(
                                "Alert resolved",
                                alert_id=alert.id,
                                rule=rule.name,
                            )

                        # Keep resolved alerts for a short time, then remove
                        if (
                            current_time - (alert.resolved_timestamp or alert.timestamp)
                            > 3600
                        ):  # 1 hour
                            del self.active_alerts[alert_key]
                            rule.active = False

        except Exception as e:
            logger.error("Error during alert checking", error=str(e))

    async def start_monitoring(self):
        """Start the alert monitoring loop"""
        if self._check_task and not self._check_task.done():
            logger.warning("Alert monitoring already running")
            return

        check_interval = self.config.get("check_interval_seconds", 30)

        logger.info("Starting alert monitoring", interval_seconds=check_interval)

        self._check_task = asyncio.create_task(self._monitoring_loop(check_interval))

    async def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""
        while not self._shutdown_event.is_set():
            try:
                await self._check_alerts()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error("Error in alert monitoring loop", error=str(e))
                await asyncio.sleep(5)  # Brief pause before retry

    async def stop_monitoring(self):
        """Stop the alert monitoring"""
        logger.info("Stopping alert monitoring")

        self._shutdown_event.set()

        if self._check_task and not self._check_task.done():
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass

        if self.notification_manager:
            await self.notification_manager.close()

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts"""
        return [
            {
                "id": alert.id,
                "rule_name": alert.rule_name,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "message": alert.message,
                "value": alert.value,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp,
                "resolved_timestamp": alert.resolved_timestamp,
                "acknowledged_by": alert.acknowledged_by,
                "acknowledged_at": alert.acknowledged_at,
            }
            for alert in self.active_alerts.values()
        ]

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert"""
        for alert in self.active_alerts.values():
            if alert.id == alert_id:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = time.time()
                logger.info("Alert acknowledged", alert_id=alert_id, by=acknowledged_by)
                break

    def get_alert_rules(self) -> List[Dict[str, Any]]:
        """Get list of alert rules"""
        return [
            {
                "name": rule.name,
                "description": rule.description,
                "metric_path": rule.metric_path,
                "condition": rule.condition,
                "threshold": rule.threshold,
                "severity": rule.severity.value,
                "enabled": rule.enabled,
                "cooldown_minutes": rule.cooldown_minutes,
                "channels": [c.value for c in rule.channels],
                "custom_message": rule.custom_message,
                "last_triggered": rule.last_triggered,
                "active": rule.active,
            }
            for rule in self.rules.values()
        ]


# Global alert manager instance
alert_manager = AlertManager()
