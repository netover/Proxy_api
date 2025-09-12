#!/bin/bash

# Test script for deployment and rollback procedures
# This script validates the deployment setup without actually deploying

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test functions
test_script_syntax() {
    local script="$1"
    local script_name="$2"

    echo -n "Testing $script_name syntax... "

    if bash -n "$script" 2>/dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

test_file_exists() {
    local file="$1"
    local file_name="$2"

    echo -n "Checking $file_name exists... "

    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

test_file_executable() {
    local file="$1"
    local file_name="$2"

    echo -n "Checking $file_name is executable... "

    if [[ -x "$file" ]]; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

test_docker_compose() {
    echo -n "Testing docker-compose configuration... "

    if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
        if docker-compose config --quiet 2>/dev/null; then
            echo -e "${GREEN}✓ PASS${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ WARN${NC} (docker-compose not available or config invalid)"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠ SKIP${NC} (Docker not available)"
        return 0
    fi
}

test_dockerfile() {
    echo -n "Testing Dockerfile syntax... "

    if [[ -f "Dockerfile" ]]; then
        # Basic syntax check - look for common issues
        if grep -q "FROM " Dockerfile && grep -q "CMD " Dockerfile; then
            echo -e "${GREEN}✓ PASS${NC}"
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (missing FROM or CMD)"
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Dockerfile not found)"
        return 1
    fi
}

test_github_workflow() {
    echo -n "Testing GitHub Actions workflow... "

    if [[ -f ".github/workflows/deploy.yml" ]]; then
        # Check for required sections
        if grep -q "jobs:" .github/workflows/deploy.yml && grep -q "runs-on:" .github/workflows/deploy.yml; then
            echo -e "${GREEN}✓ PASS${NC}"
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (missing required sections)"
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (workflow file not found)"
        return 1
    fi
}

test_configuration_files() {
    echo -n "Testing configuration files... "

    local config_ok=true

    # Check if config.yaml exists
    if [[ ! -f "config.yaml" ]]; then
        echo -e "${YELLOW}⚠ WARN${NC} (config.yaml not found)"
        config_ok=false
    fi

    # Check if .env.example exists
    if [[ ! -f ".env.example" ]]; then
        echo -e "${YELLOW}⚠ WARN${NC} (.env.example not found)"
        config_ok=false
    fi

    # Check if requirements.txt exists
    if [[ ! -f "requirements.txt" ]]; then
        echo -e "${YELLOW}⚠ WARN${NC} (requirements.txt not found)"
        config_ok=false
    fi

    if [[ "$config_ok" == "true" ]]; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        return 1
    fi
}

test_systemd_services() {
    echo -n "Testing systemd service files... "

    if [[ -d "systemd-services" ]]; then
        local service_count=$(find systemd-services -name "*.service" | wc -l)
        if [[ $service_count -gt 0 ]]; then
            echo -e "${GREEN}✓ PASS${NC} ($service_count service files found)"
            return 0
        else
            echo -e "${YELLOW}⚠ WARN${NC} (no service files found)"
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (systemd-services directory not found)"
        return 1
    fi
}

show_summary() {
    echo
    echo "=========================================="
    echo "🏁 DEPLOYMENT TEST SUMMARY"
    echo "=========================================="
    echo "✅ PASSED: $PASSED"
    echo "❌ FAILED: $FAILED"
    echo "⚠️  WARNINGS: $WARNINGS"
    echo "⏭️  SKIPPED: $SKIPPED"
    echo "=========================================="

    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}🎉 All critical tests passed!${NC}"
        echo "Your deployment setup appears to be ready."
    else
        echo -e "${RED}⚠️  Some tests failed. Please review the issues above.${NC}"
    fi

    echo
    echo "📖 Next steps:"
    echo "1. Fix any FAILED tests"
    echo "2. Address WARNINGS if applicable"
    echo "3. Test deployment on a staging environment"
    echo "4. Review DEPLOYMENT_GUIDE.md for detailed instructions"
}

# Main test execution
main() {
    echo "🚀 Testing LLM Proxy API Deployment Setup"
    echo "=========================================="
    echo

    PASSED=0
    FAILED=0
    WARNINGS=0
    SKIPPED=0

    # Test script files
    test_file_exists "deploy.sh" "deploy.sh" && ((PASSED++)) || ((FAILED++))
    test_file_exists "rollback.sh" "rollback.sh" && ((PASSED++)) || ((FAILED++))
    test_file_executable "deploy.sh" "deploy.sh" && ((PASSED++)) || ((FAILED++))
    test_file_executable "rollback.sh" "rollback.sh" && ((PASSED++)) || ((FAILED++))
    test_script_syntax "deploy.sh" "deploy.sh" && ((PASSED++)) || ((FAILED++))
    test_script_syntax "rollback.sh" "rollback.sh" && ((PASSED++)) || ((FAILED++))

    # Test Docker setup
    test_file_exists "Dockerfile" "Dockerfile" && ((PASSED++)) || ((FAILED++))
    test_file_exists "docker-compose.yml" "docker-compose.yml" && ((PASSED++)) || ((FAILED++))
    test_dockerfile && ((PASSED++)) || ((FAILED++))
    test_docker_compose && ((PASSED++)) || ((WARNINGS++))

    # Test CI/CD setup
    test_github_workflow && ((PASSED++)) || ((FAILED++))

    # Test configuration
    test_configuration_files && ((PASSED++)) || ((WARNINGS++))

    # Test systemd services
    test_systemd_services && ((PASSED++)) || ((WARNINGS++))

    # Show summary
    show_summary
}

# Run main function
main "$@"