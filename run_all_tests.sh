#!/bin/bash
#
# Master test runner - runs all tests (backend + frontend)
#
# Usage:
#   ./run_all_tests.sh           # All tests
#   ./run_all_tests.sh fast      # Fast tests only
#   ./run_all_tests.sh ci        # CI mode

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

MODE="${1:-all}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Gestione Affitti - Full Test Suite  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Backend tests
echo -e "${YELLOW}[1/2] Running Backend Tests...${NC}"
cd backend
if [ "$MODE" = "fast" ]; then
    ./run_tests.sh fast
elif [ "$MODE" = "ci" ]; then
    ./run_tests.sh ci
else
    ./run_tests.sh coverage
fi
cd ..

# Frontend tests
echo -e "${YELLOW}[2/2] Running Frontend Tests...${NC}"
cd frontend
if [ "$MODE" = "ci" ]; then
    npm run test:coverage
else
    npm run test:run
fi
cd ..

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ All Tests Passed!                 ${NC}"
echo -e "${GREEN}========================================${NC}"
