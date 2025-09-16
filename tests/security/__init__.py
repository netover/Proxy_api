"""
Security Testing Module for LLM Proxy API

This module provides comprehensive security testing capabilities including:
- Vulnerability scanning with Bandit
- Authentication security testing
- Input validation security testing
- Penetration testing capabilities
- Automated security test runner

Usage:
    # Run all security tests
    python tests/security/run_security_tests.py

    # Run specific test suites
    python -m pytest tests/security/test_vulnerability_scanning.py -v
    python -m pytest tests/security/test_authentication_security.py -v
    python -m pytest tests/security/test_input_validation_security.py -v
    python -m pytest tests/security/test_penetration_testing.py -v
"""

__version__ = "1.0.0"
__author__ = "LLM Proxy API Security Team"

# Import main test classes for easy access
from .test_vulnerability_scanning import (
    TestVulnerabilityScanning,
    TestSecurityConfiguration,
)
from .test_authentication_security import (
    TestAuthenticationSecurity,
    TestAuthorizationSecurity,
)
from .test_input_validation_security import (
    TestInputValidationSecurity,
    TestInputSanitization,
)
from .test_penetration_testing import (
    TestPenetrationTesting,
    TestPenetrationTestingTools,
)

__all__ = [
    "TestVulnerabilityScanning",
    "TestSecurityConfiguration",
    "TestAuthenticationSecurity",
    "TestAuthorizationSecurity",
    "TestInputValidationSecurity",
    "TestInputSanitization",
    "TestPenetrationTesting",
    "TestPenetrationTestingTools",
]
