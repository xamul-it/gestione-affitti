#!/bin/bash
#
# Script per eseguire i test del backend
#
# Usage:
#   ./run_tests.sh              # Tutti i test
#   ./run_tests.sh unit         # Solo unit tests
#   ./run_tests.sh integration  # Solo integration tests
#   ./run_tests.sh coverage     # Con coverage report

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
    fast)
        echo -e "${GREEN}Esecuzione test veloci...${NC}"
        PYTEST_ARGS="-v -m 'not slow'"
        ;;
    all)
        echo -e "${GREEN}Esecuzione tutti i test...${NC}"
        ;;
    *)
        echo "Usage: $0 {all|unit|integration|coverage|tenant|parsing|fast}"
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
