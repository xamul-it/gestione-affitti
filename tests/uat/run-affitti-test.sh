#!/bin/bash
# UAT Test Runner for Affitti Lungo Module

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$SCRIPT_DIR"

echo "============================================"
echo "UAT Test Operator #2 - Affitti Lungo Module"
echo "Test Plan: TC-002"
echo "============================================"
echo ""

# Function to check if a service is running
check_service() {
    local port=$1
    local service=$2

    if lsof -i :$port &>/dev/null; then
        echo "✓ $service is running on port $port"
        return 0
    else
        echo "✗ $service is NOT running on port $port"
        return 1
    fi
}

# Check services
echo "Checking required services..."
echo ""

FRONTEND_OK=0
BACKEND_OK=0

if check_service 3000 "Frontend"; then
    FRONTEND_OK=1
elif check_service 5173 "Frontend"; then
    FRONTEND_OK=1
    FRONTEND_PORT=5173
else
    echo ""
    echo "WARNING: Frontend not running on port 3000 or 5173"
    echo "Starting frontend dev server..."
    cd "$FRONTEND_DIR"
    npm run dev -- --port 3000 --host 127.0.0.1 &
    FRONTEND_PID=$!
    sleep 3
    if check_service 3000 "Frontend"; then
        FRONTEND_OK=1
    else
        echo "ERROR: Failed to start frontend"
        exit 1
    fi
fi

echo ""

if check_service 8000 "Backend (FastAPI)"; then
    BACKEND_OK=1
else
    echo ""
    echo "WARNING: Backend not running on port 8000"
    echo "Starting backend..."
    cd "$BACKEND_DIR"

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -q -r requirements.txt
    else
        source venv/bin/activate
    fi

    # Start backend in background
    env -u DATABASE_URL -u BACKEND_CORS_ORIGINS python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
    BACKEND_PID=$!

    sleep 4

    if check_service 8000 "Backend"; then
        BACKEND_OK=1
    else
        echo "ERROR: Failed to start backend"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
fi

echo ""
echo "============================================"
echo "Services Status:"
echo "Frontend: $([ $FRONTEND_OK -eq 1 ] && echo 'OK' || echo 'FAILED')"
echo "Backend: $([ $BACKEND_OK -eq 1 ] && echo 'OK' || echo 'FAILED')"
echo "============================================"
echo ""

if [ $FRONTEND_OK -eq 0 ] || [ $BACKEND_OK -eq 0 ]; then
    echo "ERROR: Not all required services are running"
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "Running UAT Test Suite: TC-002 - Affitti Lungo Regression"
echo "Test Duration: ~3-5 minutes"
echo ""

cd "$FRONTEND_DIR"

# Run Playwright tests
npx playwright test tests/affitti-lungo-regression.spec.js --config=playwright.config.js

TEST_RESULT=$?

echo ""
echo "============================================"
echo "Test Results"
echo "============================================"
echo ""

# Show report if it exists
LATEST_REPORT=$(ls -t test-results/uat-report-affitti-*.json 2>/dev/null | head -1)

if [ -f "$LATEST_REPORT" ]; then
    echo "Report saved to: $LATEST_REPORT"
    echo ""
    echo "Summary:"
    grep -E '"totalSteps"|"passedSteps"|"failedSteps"|"blockedSteps"|"overallResult"' "$LATEST_REPORT" || echo "Could not parse report"
fi

echo ""

# Cleanup
if [ -n "$BACKEND_PID" ]; then
    echo "Stopping backend..."
    kill $BACKEND_PID 2>/dev/null || true
fi

if [ -n "$FRONTEND_PID" ]; then
    echo "Stopping frontend..."
    kill $FRONTEND_PID 2>/dev/null || true
fi

echo ""
echo "Test execution completed. Exit code: $TEST_RESULT"
exit $TEST_RESULT
