#!/bin/bash

# Comprehensive test script for LLM Proxy API
# Usage: ./scripts/test_all.sh [unit|integration|all]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🧪 Starting LLM Proxy API Test Suite${NC}"

# Check if Redis is available
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is available${NC}"
    REDIS_AVAILABLE=true
else
    echo -e "${YELLOW}⚠️  Redis not available - some tests will be skipped${NC}"
    REDIS_AVAILABLE=false
fi

# Function to run test category
run_tests() {
    local category=$1
    local marker=$2

    echo -e "\n${YELLOW}🔄 Running $category tests...${NC}"

    if [ "$marker" = "redis" ] && [ "$REDIS_AVAILABLE" = "false" ]; then
        echo -e "${YELLOW}⏭️  Skipping $category tests (Redis not available)${NC}"
        return 0
    fi

    if pytest -m "$marker" --tb=short -q; then
        echo -e "${GREEN}✅ $category tests passed${NC}"
    else
        echo -e "${RED}❌ $category tests failed${NC}"
        return 1
    fi
}

# Run tests based on argument
case "${1:-all}" in
    "unit")
        echo -e "${YELLOW}🏃 Running unit tests only...${NC}"
        run_tests "Unit" "unit"
        ;;
    "integration")
        echo -e "${YELLOW}🔗 Running integration tests only...${NC}"
        run_tests "Integration" "integration"
        ;;
    "chaos")
        echo -e "${YELLOW}🐒 Running chaos engineering tests only...${NC}"
        run_tests "Chaos" "chaos"
        ;;
    "all")
        echo -e "${YELLOW}🚀 Running all tests...${NC}"

        # Unit tests
        run_tests "Unit" "unit" || exit 1

        # Integration tests
        run_tests "Integration" "integration" || exit 1

        # Chaos tests
        run_tests "Chaos" "chaos" || exit 1

        # Redis tests (if available)
        if [ "$REDIS_AVAILABLE" = "true" ]; then
            run_tests "Redis" "redis" || exit 1
        fi

        echo -e "\n${GREEN}🎉 All tests passed!${NC}"
        ;;
    *)
        echo -e "${RED}❌ Invalid argument: $1${NC}"
        echo "Usage: $0 [unit|integration|chaos|all]"
        exit 1
        ;;
esac

echo -e "\n${GREEN}✅ Test execution completed${NC}"
