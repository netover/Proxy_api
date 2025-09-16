#!/usr/bin/env python3
"""
Security Test Runner

Comprehensive security testing framework for the LLM Proxy API.
Runs vulnerability scanning, authentication tests, input validation tests,
and penetration testing capabilities.
"""

import argparse
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
import subprocess
import concurrent.futures
from typing import Dict, List, Any
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("security_test_results.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class SecurityTestRunner:
    """Main security test runner class"""

    def __init__(
        self, base_url: str = "http://localhost:8000", verbose: bool = False
    ):
        self.base_url = base_url
        self.verbose = verbose
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "target": base_url,
            "tests_run": [],
            "vulnerabilities_found": [],
            "summary": {},
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all security tests"""
        logger.info("Starting comprehensive security testing...")

        test_suites = [
            self.run_vulnerability_scanning,
            self.run_authentication_tests,
            self.run_input_validation_tests,
            self.run_penetration_tests,
            self.run_dependency_scanning,
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(test_suite) for test_suite in test_suites
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    self.results["tests_run"].append(result)
                except Exception as e:
                    logger.error(f"Test suite failed: {e}")
                    self.results["tests_run"].append(
                        {
                            "name": "unknown",
                            "status": "failed",
                            "error": str(e),
                        }
                    )

        self._generate_summary()
        return self.results

    def run_vulnerability_scanning(self) -> Dict[str, Any]:
        """Run vulnerability scanning tests"""
        logger.info("Running vulnerability scanning...")

        result = {
            "name": "vulnerability_scanning",
            "status": "running",
            "start_time": time.time(),
            "findings": [],
        }

        try:
            # Run bandit
            bandit_result = self._run_bandit_scan()
            result["findings"].extend(bandit_result)

            # Run safety (dependency scanning)
            safety_result = self._run_safety_scan()
            result["findings"].extend(safety_result)

            result["status"] = "completed"

        except Exception as e:
            logger.error(f"Vulnerability scanning failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)

        result["end_time"] = time.time()
        result["duration"] = result["end_time"] - result["start_time"]
        return result

    def run_authentication_tests(self) -> Dict[str, Any]:
        """Run authentication security tests"""
        logger.info("Running authentication security tests...")

        result = {
            "name": "authentication_tests",
            "status": "running",
            "start_time": time.time(),
            "findings": [],
        }

        try:
            # Run pytest on authentication tests
            auth_test_result = self._run_pytest_suite(
                "tests/security/test_authentication_security.py"
            )
            result["findings"].extend(auth_test_result)

            result["status"] = "completed"

        except Exception as e:
            logger.error(f"Authentication tests failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)

        result["end_time"] = time.time()
        result["duration"] = result["end_time"] - result["start_time"]
        return result

    def run_input_validation_tests(self) -> Dict[str, Any]:
        """Run input validation security tests"""
        logger.info("Running input validation security tests...")

        result = {
            "name": "input_validation_tests",
            "status": "running",
            "start_time": time.time(),
            "findings": [],
        }

        try:
            # Run pytest on input validation tests
            validation_test_result = self._run_pytest_suite(
                "tests/security/test_input_validation_security.py"
            )
            result["findings"].extend(validation_test_result)

            result["status"] = "completed"

        except Exception as e:
            logger.error(f"Input validation tests failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)

        result["end_time"] = time.time()
        result["duration"] = result["end_time"] - result["start_time"]
        return result

    def run_penetration_tests(self) -> Dict[str, Any]:
        """Run penetration testing"""
        logger.info("Running penetration tests...")

        result = {
            "name": "penetration_tests",
            "status": "running",
            "start_time": time.time(),
            "findings": [],
        }

        try:
            # Run pytest on penetration tests
            pentest_result = self._run_pytest_suite(
                "tests/security/test_penetration_testing.py"
            )
            result["findings"].extend(pentest_result)

            result["status"] = "completed"

        except Exception as e:
            logger.error(f"Penetration tests failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)

        result["end_time"] = time.time()
        result["duration"] = result["end_time"] - result["start_time"]
        return result

    def run_dependency_scanning(self) -> Dict[str, Any]:
        """Run dependency vulnerability scanning"""
        logger.info("Running dependency scanning...")

        result = {
            "name": "dependency_scanning",
            "status": "running",
            "start_time": time.time(),
            "findings": [],
        }

        try:
            # Run safety check
            safety_result = self._run_safety_scan()
            result["findings"].extend(safety_result)

            result["status"] = "completed"

        except Exception as e:
            logger.error(f"Dependency scanning failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)

        result["end_time"] = time.time()
        result["duration"] = result["end_time"] - result["start_time"]
        return result

    def _run_bandit_scan(self) -> List[Dict[str, Any]]:
        """Run Bandit security scanner"""
        findings = []

        try:
            cmd = ["bandit", "-r", "src/", "-f", "json"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent,
            )

            if result.returncode == 0:
                bandit_data = json.loads(result.stdout)
                for issue in bandit_data.get("results", []):
                    findings.append(
                        {
                            "tool": "bandit",
                            "severity": issue.get("issue_severity", "UNKNOWN"),
                            "type": "code_vulnerability",
                            "description": issue.get("issue_text", ""),
                            "file": issue.get("filename", ""),
                            "line": issue.get("line_number", 0),
                            "confidence": issue.get(
                                "issue_confidence", "UNKNOWN"
                            ),
                        }
                    )
            else:
                logger.warning(f"Bandit scan failed: {result.stderr}")

        except FileNotFoundError:
            logger.warning("Bandit not installed, skipping vulnerability scan")
        except Exception as e:
            logger.error(f"Bandit scan error: {e}")

        return findings

    def _run_safety_scan(self) -> List[Dict[str, Any]]:
        """Run Safety dependency scanner"""
        findings = []

        try:
            cmd = ["safety", "check", "--json"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent,
            )

            if result.returncode == 0:
                safety_data = json.loads(result.stdout)
                for vuln in safety_data:
                    findings.append(
                        {
                            "tool": "safety",
                            "severity": "HIGH",  # Safety reports critical vulnerabilities
                            "type": "dependency_vulnerability",
                            "description": vuln.get("advisory", ""),
                            "package": vuln.get("package", ""),
                            "version": vuln.get("vulnerable_version", ""),
                            "cve": vuln.get("cve", ""),
                        }
                    )
            else:
                logger.warning(f"Safety scan failed: {result.stderr}")

        except FileNotFoundError:
            logger.warning("Safety not installed, skipping dependency scan")
        except Exception as e:
            logger.error(f"Safety scan error: {e}")

        return findings

    def _run_pytest_suite(self, test_file: str) -> List[Dict[str, Any]]:
        """Run pytest on a specific test file"""
        findings = []

        try:
            cmd = [
                "python",
                "-m",
                "pytest",
                test_file,
                "-v",
                "--tb=short",
                "--json-report",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent,
            )

            # Parse pytest JSON output if available
            if result.returncode != 0:
                findings.append(
                    {
                        "tool": "pytest",
                        "severity": "MEDIUM",
                        "type": "test_failure",
                        "description": f"Test suite failed: {test_file}",
                        "output": result.stderr[:500],  # Truncate long output
                    }
                )

        except Exception as e:
            logger.error(f"Pytest execution error: {e}")
            findings.append(
                {
                    "tool": "pytest",
                    "severity": "HIGH",
                    "type": "execution_error",
                    "description": f"Failed to run test suite: {test_file}",
                    "error": str(e),
                }
            )

        return findings

    def _generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.results["tests_run"])
        completed_tests = sum(
            1
            for test in self.results["tests_run"]
            if test["status"] == "completed"
        )
        failed_tests = sum(
            1
            for test in self.results["tests_run"]
            if test["status"] == "failed"
        )

        # Count vulnerabilities by severity
        severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "UNKNOWN": 0,
        }

        for test in self.results["tests_run"]:
            for finding in test.get("findings", []):
                severity = finding.get("severity", "UNKNOWN")
                if severity in severity_counts:
                    severity_counts[severity] += 1
                else:
                    severity_counts["UNKNOWN"] += 1

        self.results["summary"] = {
            "total_test_suites": total_tests,
            "completed_test_suites": completed_tests,
            "failed_test_suites": failed_tests,
            "vulnerability_counts": severity_counts,
            "total_vulnerabilities": sum(severity_counts.values()),
            "scan_duration": sum(
                test.get("duration", 0) for test in self.results["tests_run"]
            ),
        }

    def save_report(self, output_file: str = None):
        """Save test results to file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"security_test_report_{timestamp}.json"

        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Security test report saved to: {output_file}")
        return output_file

    def print_summary(self):
        """Print test summary to console"""
        summary = self.results["summary"]

        print("\n" + "=" * 60)
        print("SECURITY TEST SUMMARY")
        print("=" * 60)
        print(f"Target: {self.results['target']}")
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Test Suites Run: {summary['total_test_suites']}")
        print(f"Completed: {summary['completed_test_suites']}")
        print(f"Failed: {summary['failed_test_suites']}")
        print(f"Total Duration: {summary['scan_duration']:.2f} seconds")
        print("\nVULNERABILITIES FOUND:")
        print("-" * 30)

        vuln_counts = summary["vulnerability_counts"]
        for severity, count in vuln_counts.items():
            if count > 0:
                print(f"{severity}: {count}")

        total_vulns = summary["total_vulnerabilities"]
        if total_vulns == 0:
            print("\n🎉 No vulnerabilities detected!")
        else:
            print(f"\n⚠️  Total vulnerabilities: {total_vulns}")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="LLM Proxy API Security Test Runner"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Target URL to test (default: http://localhost:8000)",
    )
    parser.add_argument("--output", "-o", help="Output file for test results")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--test-type",
        choices=["all", "vuln", "auth", "input", "pentest", "deps"],
        default="all",
        help="Type of tests to run",
    )

    args = parser.parse_args()

    # Check if required tools are installed
    missing_tools = []
    for tool in ["bandit", "safety"]:
        try:
            subprocess.run([tool, "--help"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)

    if missing_tools:
        logger.warning(f"Missing security tools: {', '.join(missing_tools)}")
        logger.warning("Install with: pip install bandit safety")
        logger.warning("Continuing with available tools...")

    # Run security tests
    runner = SecurityTestRunner(args.url, args.verbose)

    if args.test_type == "all":
        results = runner.run_all_tests()
    elif args.test_type == "vuln":
        results = runner.run_vulnerability_scanning()
    elif args.test_type == "auth":
        results = runner.run_authentication_tests()
    elif args.test_type == "input":
        results = runner.run_input_validation_tests()
    elif args.test_type == "pentest":
        results = runner.run_penetration_tests()
    elif args.test_type == "deps":
        results = runner.run_dependency_scanning()

    # Save and display results
    output_file = runner.save_report(args.output)
    runner.print_summary()

    # Exit with appropriate code
    if runner.results["summary"]["failed_test_suites"] > 0:
        sys.exit(1)
    elif runner.results["summary"]["vulnerability_counts"]["CRITICAL"] > 0:
        sys.exit(1)
    elif runner.results["summary"]["vulnerability_counts"]["HIGH"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
