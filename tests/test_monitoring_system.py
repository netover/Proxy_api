#!/usr/bin/env python3
"""
Test script for the monitoring and alerting system.

This script tests the comprehensive monitoring system by:
1. Simulating various system conditions
2. Testing alert triggers
3. Verifying metrics collection
4. Testing the monitoring dashboard
"""

import asyncio
import json
import time
from pathlib import Path

import httpx

from src.core.alerting import alert_manager
from src.core.metrics import metrics_collector


async def test_basic_metrics_collection():
    """Test basic metrics collection functionality"""
    print("🧪 Testing basic metrics collection...")

    # Record some test requests
    metrics_collector.record_request("test_provider", True, 0.5, tokens=100, model_name="test-model")
    metrics_collector.record_request("test_provider", False, 1.2, error_type="timeout", model_name="test-model")
    metrics_collector.record_request("another_provider", True, 0.8, tokens=50, model_name="another-model")

    # Get stats
    stats = metrics_collector.get_all_stats()
    print(f"✅ Recorded {stats['total_requests']} requests")
    print(f"✅ Success rate: {stats['overall_success_rate']:.1%}")

    return True


async def test_alert_system():
    """Test the alerting system"""
    print("\n🔔 Testing alerting system...")

    # Create a test alert rule
    from src.core.alerting import AlertRule, AlertSeverity, NotificationChannel

    test_rule = AlertRule(
        name="test_high_error_rate",
        description="Test alert for high error rate",
        metric_path="error_rates.error_rate_percent",
        condition=">",
        threshold=5.0,
        severity=AlertSeverity.WARNING,
        channels=[NotificationChannel.LOG]
    )

    alert_manager.add_rule(test_rule)
    print("✅ Added test alert rule")

    # Simulate high error rate
    for i in range(20):
        metrics_collector.record_request("test_provider", False, 0.5, error_type="test_error")

    # Wait for alert monitoring to trigger
    await asyncio.sleep(35)  # Wait longer than check interval

    # Check for active alerts
    active_alerts = alert_manager.get_active_alerts()
    triggered_alerts = [a for a in active_alerts if a["rule_name"] == "test_high_error_rate"]

    if triggered_alerts:
        print(f"✅ Alert triggered: {triggered_alerts[0]['message']}")
        return True
    else:
        print("❌ Alert not triggered")
        return False


async def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n🏥 Testing health endpoint...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/v1/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check successful - Status: {health_data['status']}")
                print(f"✅ Health score: {health_data['health_score']}/100")
                return True
            else:
                print(f"❌ Health check failed with status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


async def test_metrics_endpoint():
    """Test the metrics endpoint"""
    print("\n📊 Testing metrics endpoint...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/v1/metrics")
            if response.status_code == 200:
                metrics_data = response.json()
                print("✅ Metrics endpoint accessible")
                print(f"✅ Providers tracked: {len(metrics_data.get('providers', {}))}")
                return True
            else:
                print(f"❌ Metrics endpoint failed with status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Metrics endpoint error: {e}")
        return False


async def test_alerting_endpoint():
    """Test the alerting endpoints"""
    print("\n🚨 Testing alerting endpoints...")

    try:
        async with httpx.AsyncClient() as client:
            # Test alerts endpoint
            response = await client.get("http://localhost:8000/v1/alerts")
            if response.status_code == 200:
                alerts_data = response.json()
                print("✅ Alerts endpoint accessible")
                print(f"✅ Active alerts: {len(alerts_data.get('alerts', []))}")

                # Test rules endpoint
                response = await client.get("http://localhost:8000/v1/alerts/rules")
                if response.status_code == 200:
                    rules_data = response.json()
                    print(f"✅ Alert rules: {len(rules_data.get('rules', []))}")
                    return True
                else:
                    print(f"❌ Alert rules endpoint failed with status {response.status_code}")
                    return False
            else:
                print(f"❌ Alerts endpoint failed with status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Alerting endpoint error: {e}")
        return False


async def test_monitoring_dashboard():
    """Test the monitoring dashboard"""
    print("\n📈 Testing monitoring dashboard...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/monitoring")
            if response.status_code == 200:
                print("✅ Monitoring dashboard accessible")
                return True
            else:
                print(f"❌ Monitoring dashboard failed with status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Monitoring dashboard error: {e}")
        return False


async def test_prometheus_metrics():
    """Test Prometheus metrics endpoint"""
    print("\n📈 Testing Prometheus metrics endpoint...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/v1/metrics/prometheus")
            if response.status_code == 200:
                prometheus_data = response.text
                print("✅ Prometheus metrics accessible")
                print(f"✅ Metrics data length: {len(prometheus_data)} characters")

                # Check for some expected metrics
                expected_metrics = [
                    "proxy_api_requests_total",
                    "proxy_api_provider_success_rate",
                    "proxy_api_system_cpu_percent"
                ]

                found_metrics = 0
                for metric in expected_metrics:
                    if metric in prometheus_data:
                        found_metrics += 1

                print(f"✅ Found {found_metrics}/{len(expected_metrics)} expected metrics")
                return found_metrics > 0
            else:
                print(f"❌ Prometheus metrics failed with status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Prometheus metrics error: {e}")
        return False


async def simulate_load_test():
    """Simulate a load test to trigger alerts"""
    print("\n🔥 Running load test simulation...")

    # Simulate high load with errors
    print("📤 Simulating 100 requests with 20% error rate...")

    for i in range(100):
        success = i % 5 != 0  # 20% error rate
        error_type = "simulated_error" if not success else None
        metrics_collector.record_request(
            "load_test_provider",
            success,
            0.1 + (i * 0.01),  # Increasing latency
            tokens=50,
            error_type=error_type,
            model_name="load-test-model"
        )

        if i % 20 == 0:
            print(f"📊 Progress: {i}/100 requests")

    print("✅ Load test simulation completed")

    # Wait for alerts to be processed
    await asyncio.sleep(35)

    # Check for triggered alerts
    active_alerts = alert_manager.get_active_alerts()
    print(f"📊 Active alerts after load test: {len(active_alerts)}")

    for alert in active_alerts:
        print(f"  🚨 {alert['severity'].upper()}: {alert['message']}")

    return True


async def main():
    """Run all monitoring system tests"""
    print("🚀 Starting Monitoring System Tests")
    print("=" * 50)

    # Check if the server is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code != 200:
                print("❌ Server doesn't appear to be running on localhost:8000")
                print("💡 Please start the server first with: python main.py")
                return
    except Exception:
        print("❌ Cannot connect to server on localhost:8000")
        print("💡 Please start the server first with: python main.py")
        return

    tests = [
        ("Basic Metrics Collection", test_basic_metrics_collection),
        ("Alert System", test_alert_system),
        ("Health Endpoint", test_health_endpoint),
        ("Metrics Endpoint", test_metrics_endpoint),
        ("Alerting Endpoints", test_alerting_endpoint),
        ("Monitoring Dashboard", test_monitoring_dashboard),
        ("Prometheus Metrics", test_prometheus_metrics),
        ("Load Test Simulation", simulate_load_test)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 50)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n📊 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Monitoring system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    # Print system status
    print("\n📈 Current System Status:")
    stats = metrics_collector.get_all_stats()
    active_alerts = alert_manager.get_active_alerts()

    print(f"  • Total Requests: {stats['total_requests']}")
    print(f"  • Success Rate: {stats['overall_success_rate']:.1%}")
    print(f"  • Active Alerts: {len(active_alerts)}")
    print(f"  • System Uptime: {stats['uptime']:.0f} seconds")

    if active_alerts:
        print("  • Recent Alerts:")
        for alert in active_alerts[:3]:  # Show first 3
            print(f"    - {alert['severity'].upper()}: {alert['message']}")


if __name__ == "__main__":
    asyncio.run(main())