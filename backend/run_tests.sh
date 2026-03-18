#!/bin/bash
#
# Comprehensive test runner for backend
#
# Usage:
#   ./run_tests.sh                    # All tests
#   ./run_tests.sh unit               # Only unit tests
#   ./run_tests.sh integration        # Only integration tests
#   ./run_tests.sh module anagrafica  # Module-specific tests
#   ./run_tests.sh coverage           # With coverage report
#   ./run_tests.sh ci                 # CI mode (fast, strict)
#   ./run_tests.sh watch              # Watch mode

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest non trovato. Installazione dipendenze...${NC}"
    pip install -r requirements-test.txt
fi

# Default: all tests
TEST_TARGET="tests/"
PYTEST_ARGS="-v"

# Parse arguments
case "${1:-all}" in
    unit)
        echo -e "${GREEN}Esecuzione unit tests...${NC}"
        TEST_TARGET="tests/unit/"
        PYTEST_ARGS="-v -m unit"
        ;;
    integration|int)
        echo -e "${GREEN}Esecuzione integration tests...${NC}"
        TEST_TARGET="tests/integration/"
        PYTEST_ARGS="-v -m integration"
        ;;
    coverage|cov)
        echo -e "${GREEN}Esecuzione test con coverage...${NC}"
        PYTEST_ARGS="-v --cov=app --cov-report=html --cov-report=term-missing"
        ;;
    tenant)
        echo -e "${GREEN}Esecuzione test tenant isolation...${NC}"
        PYTEST_ARGS="-v -m tenant"
        ;;
    parsing)
        echo -e "${GREEN}Esecuzione test document parsing...${NC}"
        PYTEST_ARGS="-v -m parsing"
        ;;
    module)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Module name required${NC}"
            echo "Usage: $0 module <module_name>"
            echo "Available modules: anagrafica, immobili, affitti_lungo"
            exit 1
        fi
        echo -e "${GREEN}Esecuzione tests per modulo: $2${NC}"
        PYTEST_ARGS="-v -m module_$2"
        ;;
    security)
        echo -e "${GREEN}Esecuzione security tests...${NC}"
        PYTEST_ARGS="-v -m security"
        ;;
    performance|perf)
        echo -e "${GREEN}Esecuzione performance tests...${NC}"
        PYTEST_ARGS="-v -m performance"
        ;;
    contract)
        echo -e "${GREEN}Esecuzione API contract tests...${NC}"
        PYTEST_ARGS="-v -m contract"
        ;;
    e2e)
        echo -e "${GREEN}Esecuzione E2E tests...${NC}"
        PYTEST_ARGS="-v -m e2e"
        ;;
    fast)
        echo -e "${GREEN}Esecuzione test veloci...${NC}"
        PYTEST_ARGS="-v -m 'not slow and not e2e'"
        ;;
    ci)
        echo -e "${GREEN}Esecuzione CI test suite...${NC}"
        PYTEST_ARGS="-v --cov=app --cov=modules --cov-report=xml --cov-fail-under=80 --maxfail=1"
        ;;
    watch)
        echo -e "${GREEN}Esecuzione test in watch mode...${NC}"
        PYTEST_ARGS="-v -f"
        ;;
    all)
        echo -e "${GREEN}Esecuzione tutti i test...${NC}"
        ;;
    *)
        echo "Usage: $0 {all|unit|integration|e2e|coverage|module|tenant|parsing|security|performance|contract|fast|ci|watch}"
        echo ""
        echo "Examples:"
        echo "  $0 unit                  # Run unit tests only"
        echo "  $0 module anagrafica     # Run anagrafica module tests"
        echo "  $0 coverage              # Run with coverage report"
        echo "  $0 ci                    # Run in CI mode"
        exit 1
        ;;
esac

# Run tests
echo ""
pytest $TEST_TARGET $PYTEST_ARGS

# Show coverage report location if generated
if [[ "${1}" == "coverage" || "${1}" == "cov" ]]; then
    echo ""
    echo -e "${GREEN}Coverage report generato in: htmlcov/index.html${NC}"
    echo "Apri con: open htmlcov/index.html (Mac) o xdg-open htmlcov/index.html (Linux)"
fi

echo ""
echo -e "${GREEN}✓ Test completati!${NC}"
