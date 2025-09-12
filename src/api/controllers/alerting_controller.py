"""
Alerting controller for managing alerts and alert rules.

This module provides REST API endpoints for:
- Viewing active alerts
- Managing alert rules
- Acknowledging alerts
- Configuring notification channels
"""

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src.core.alerting import AlertSeverity, AlertStatus, NotificationChannel, alert_manager
from src.core.auth import verify_api_key
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class AlertRuleCreate(BaseModel):
    """Model for creating alert rules"""
    name: str = Field(..., description="Unique name for the alert rule")
    description: str = Field(..., description="Description of what this alert monitors")
    metric_path: str = Field(..., description="Dot-separated path to metric (e.g., 'system_health.cpu_percent')")
    condition: str = Field(..., description="Comparison operator: >, <, >=, <=, ==, !=")
    threshold: float = Field(..., description="Threshold value for the alert")
    severity: str = Field(..., description="Alert severity: info, warning, error, critical")
    enabled: bool = Field(True, description="Whether the rule is enabled")
    cooldown_minutes: int = Field(5, description="Minimum time between alerts in minutes")
    channels: List[str] = Field(["log"], description="Notification channels to use")
    custom_message: Optional[str] = Field(None, description="Custom alert message")


class AlertRuleUpdate(BaseModel):
    """Model for updating alert rules"""
    description: Optional[str] = None
    metric_path: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None
    enabled: Optional[bool] = None
    cooldown_minutes: Optional[int] = None
    channels: Optional[List[str]] = None
    custom_message: Optional[str] = None


class NotificationConfig(BaseModel):
    """Model for notification configuration"""
    email: Optional[Dict[str, Any]] = None
    webhook: Optional[Dict[str, Any]] = None
    slack: Optional[Dict[str, Any]] = None


@router.get("/alerts")
async def get_active_alerts(
    request: Request,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    _: bool = Depends(verify_api_key)
):
    """Get active alerts with optional filtering"""
    start_time = time.time()
    logger.info("Getting active alerts")

    try:
        alerts = alert_manager.get_active_alerts()

        # Apply filters
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        if status:
            alerts = [a for a in alerts if a["status"] == status]

        response_time = time.time() - start_time
        logger.info("Active alerts retrieved",
                   count=len(alerts),
                   response_time=response_time,
                   filters={"severity": severity, "status": status})

        return {
            "alerts": alerts,
            "count": len(alerts),
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error("Failed to get active alerts", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.get("/alerts/{alert_id}")
async def get_alert_details(
    request: Request,
    alert_id: str,
    _: bool = Depends(verify_api_key)
):
    """Get details of a specific alert"""
    logger.info("Getting alert details", alert_id=alert_id)

    alerts = alert_manager.get_active_alerts()
    alert = next((a for a in alerts if a["id"] == alert_id), None)

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    request: Request,
    alert_id: str,
    acknowledged_by: str = "api",
    _: bool = Depends(verify_api_key)
):
    """Acknowledge an alert"""
    logger.info("Acknowledging alert", alert_id=alert_id, by=acknowledged_by)

    try:
        alert_manager.acknowledge_alert(alert_id, acknowledged_by)
        return {"message": "Alert acknowledged successfully"}
    except Exception as e:
        logger.error("Failed to acknowledge alert", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


@router.get("/rules")
async def get_alert_rules(
    request: Request,
    enabled: Optional[bool] = None,
    _: bool = Depends(verify_api_key)
):
    """Get all alert rules with optional filtering"""
    start_time = time.time()
    logger.info("Getting alert rules")

    try:
        rules = alert_manager.get_alert_rules()

        # Apply filters
        if enabled is not None:
            rules = [r for r in rules if r["enabled"] == enabled]

        response_time = time.time() - start_time
        logger.info("Alert rules retrieved",
                   count=len(rules),
                   response_time=response_time,
                   filters={"enabled": enabled})

        return {
            "rules": rules,
            "count": len(rules),
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error("Failed to get alert rules", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve alert rules")


@router.post("/rules")
async def create_alert_rule(
    request: Request,
    rule_data: AlertRuleCreate,
    _: bool = Depends(verify_api_key)
):
    """Create a new alert rule"""
    logger.info("Creating alert rule", rule_name=rule_data.name)

    try:
        # Validate severity
        try:
            severity = AlertSeverity(rule_data.severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {rule_data.severity}")

        # Validate channels
        channels = []
        for channel_str in rule_data.channels:
            try:
                channels.append(NotificationChannel(channel_str.lower()))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid channel: {channel_str}")

        # Validate condition
        valid_conditions = [">", "<", ">=", "<=", "==", "!="]
        if rule_data.condition not in valid_conditions:
            raise HTTPException(status_code=400, detail=f"Invalid condition: {rule_data.condition}")

        from src.core.alerting import AlertRule
        rule = AlertRule(
            name=rule_data.name,
            description=rule_data.description,
            metric_path=rule_data.metric_path,
            condition=rule_data.condition,
            threshold=rule_data.threshold,
            severity=severity,
            enabled=rule_data.enabled,
            cooldown_minutes=rule_data.cooldown_minutes,
            channels=channels,
            custom_message=rule_data.custom_message
        )

        alert_manager.add_rule(rule)

        logger.info("Alert rule created", rule_name=rule_data.name)
        return {"message": "Alert rule created successfully", "rule": rule_data.dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create alert rule", rule_name=rule_data.name, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create alert rule")


@router.get("/rules/{rule_name}")
async def get_alert_rule(
    request: Request,
    rule_name: str,
    _: bool = Depends(verify_api_key)
):
    """Get details of a specific alert rule"""
    logger.info("Getting alert rule", rule_name=rule_name)

    rules = alert_manager.get_alert_rules()
    rule = next((r for r in rules if r["name"] == rule_name), None)

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    return rule


@router.put("/rules/{rule_name}")
async def update_alert_rule(
    request: Request,
    rule_name: str,
    rule_data: AlertRuleUpdate,
    _: bool = Depends(verify_api_key)
):
    """Update an existing alert rule"""
    logger.info("Updating alert rule", rule_name=rule_name)

    try:
        # Get existing rule
        rules = alert_manager.get_alert_rules()
        existing_rule = next((r for r in rules if r["name"] == rule_name), None)

        if not existing_rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")

        # Validate updates
        updates = rule_data.dict(exclude_unset=True)

        if "severity" in updates:
            try:
                updates["severity"] = AlertSeverity(updates["severity"].lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {updates['severity']}")

        if "channels" in updates:
            channels = []
            for channel_str in updates["channels"]:
                try:
                    channels.append(NotificationChannel(channel_str.lower()))
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid channel: {channel_str}")
            updates["channels"] = channels

        if "condition" in updates:
            valid_conditions = [">", "<", ">=", "<=", "==", "!="]
            if updates["condition"] not in valid_conditions:
                raise HTTPException(status_code=400, detail=f"Invalid condition: {updates['condition']}")

        # Create updated rule
        from src.core.alerting import AlertRule
        updated_rule = AlertRule(
            name=rule_name,
            description=updates.get("description", existing_rule["description"]),
            metric_path=updates.get("metric_path", existing_rule["metric_path"]),
            condition=updates.get("condition", existing_rule["condition"]),
            threshold=updates.get("threshold", existing_rule["threshold"]),
            severity=updates.get("severity", AlertSeverity(existing_rule["severity"])),
            enabled=updates.get("enabled", existing_rule["enabled"]),
            cooldown_minutes=updates.get("cooldown_minutes", existing_rule["cooldown_minutes"]),
            channels=updates.get("channels", [NotificationChannel(c) for c in existing_rule["channels"]]),
            custom_message=updates.get("custom_message", existing_rule["custom_message"])
        )

        alert_manager.update_rule(updated_rule)

        logger.info("Alert rule updated", rule_name=rule_name)
        return {"message": "Alert rule updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update alert rule", rule_name=rule_name, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update alert rule")


@router.delete("/rules/{rule_name}")
async def delete_alert_rule(
    request: Request,
    rule_name: str,
    _: bool = Depends(verify_api_key)
):
    """Delete an alert rule"""
    logger.info("Deleting alert rule", rule_name=rule_name)

    try:
        # Check if rule exists
        rules = alert_manager.get_alert_rules()
        if not next((r for r in rules if r["name"] == rule_name), None):
            raise HTTPException(status_code=404, detail="Alert rule not found")

        alert_manager.remove_rule(rule_name)

        logger.info("Alert rule deleted", rule_name=rule_name)
        return {"message": "Alert rule deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete alert rule", rule_name=rule_name, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete alert rule")


@router.get("/config")
async def get_alerting_config(
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """Get alerting configuration"""
    logger.info("Getting alerting configuration")

    try:
        # Return a safe version of the config (without sensitive data)
        config = alert_manager.config.copy()

        # Remove sensitive information
        if "notifications" in config:
            notifications = config["notifications"]
            if "email" in notifications and "password" in notifications["email"]:
                notifications["email"] = {**notifications["email"]}
                notifications["email"]["password"] = "***"
            if "webhook" in notifications and "auth_token" in notifications["webhook"]:
                notifications["webhook"] = {**notifications["webhook"]}
                notifications["webhook"]["auth_token"] = "***"

        return {
            "config": config,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error("Failed to get alerting configuration", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration")


@router.post("/config")
async def update_alerting_config(
    request: Request,
    config: NotificationConfig,
    _: bool = Depends(verify_api_key)
):
    """Update alerting configuration"""
    logger.info("Updating alerting configuration")

    try:
        # Update configuration
        updates = config.dict(exclude_unset=True)

        for key, value in updates.items():
            if key in alert_manager.config.get("notifications", {}):
                alert_manager.config["notifications"][key].update(value)
            else:
                alert_manager.config["notifications"][key] = value

        alert_manager.save_config()

        logger.info("Alerting configuration updated")
        return {"message": "Alerting configuration updated successfully"}

    except Exception as e:
        logger.error("Failed to update alerting configuration", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update configuration")


@router.post("/test-notification")
async def test_notification(
    request: Request,
    channel: str,
    _: bool = Depends(verify_api_key)
):
    """Test notification channel"""
    logger.info("Testing notification channel", channel=channel)

    try:
        # Create a test alert
        from src.core.alerting import Alert, AlertSeverity, AlertStatus, NotificationChannel
        import uuid

        test_alert = Alert(
            id=f"test_{uuid.uuid4().hex[:8]}",
            rule_name="test_notification",
            severity=AlertSeverity.INFO,
            status=AlertStatus.ACTIVE,
            message="This is a test notification from the Proxy API alerting system",
            value=100.0,
            threshold=50.0,
            timestamp=time.time()
        )

        # Create a test rule
        from src.core.alerting import AlertRule
        test_rule = AlertRule(
            name="test_rule",
            description="Test notification rule",
            metric_path="test.metric",
            condition=">",
            threshold=50.0,
            severity=AlertSeverity.INFO,
            channels=[NotificationChannel(channel.lower())]
        )

        # Send test notification
        if alert_manager.notification_manager:
            results = await alert_manager.notification_manager.notify(test_alert, test_rule)

            success = results.get(channel.lower(), False)
            if success:
                return {"message": f"Test notification sent successfully via {channel}"}
            else:
                raise HTTPException(status_code=500, detail=f"Failed to send test notification via {channel}")
        else:
            raise HTTPException(status_code=500, detail="Notification manager not initialized")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to test notification", channel=channel, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to test {channel} notification")