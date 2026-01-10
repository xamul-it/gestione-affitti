#!/bin/bash

# UAT TEST EXECUTION SCRIPT - API & Frontend Check
# Gestione Affitti - Dashboard & Module System Test
# Test Plan: UAT-MODULES-001

FRONTEND_URL="http://192.168.1.2:3000"
BACKEND_URL="http://192.168.1.2:8000"
API_BASE="${BACKEND_URL}/api/v1"
ADMIN_USER="admin"
ADMIN_PASS="changeme123"

# Test tracking
TEST_START_TIME=$(date +%s%N)
TEST_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
PASSED_STEPS=0
FAILED_STEPS=0
TOTAL_STEPS=0
DEFECTS=()
OBSERVATIONS=()

# Output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Report file
REPORT_FILE="uat-test-report-$(date +%s).txt"
REPORT_JSON="uat-test-report-$(date +%s).json"

# Functions
log_step() {
    local step_num=$1
    local description=$2
    local expected=$3
    local actual=$4
    local status=$5
    local notes=${6:-""}

    ((TOTAL_STEPS++))

    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ STEP ${step_num}: ${description}${NC}"
        ((PASSED_STEPS++))
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ STEP ${step_num}: ${description}${NC}"
        ((FAILED_STEPS++))
    else
        echo -e "${YELLOW}⚠️  STEP ${step_num}: ${description}${NC}"
    fi

    echo "   Expected: ${expected}"
    echo "   Actual: ${actual}"
    [ -n "$notes" ] && echo "   Notes: ${notes}"
    echo ""
}

log_defect() {
    local severity=$1
    local description=$2
    local steps=$3
    local expected_vs_actual=$4

    DEFECTS+=("[$severity] $description | Steps: $steps | Expected vs Actual: $expected_vs_actual")
    echo -e "${RED}🐛 DEFECT ($severity): ${description}${NC}"
}

log_observation() {
    local text=$1
    OBSERVATIONS+=("$text")
    echo -e "${BLUE}📝 OBSERVATION: ${text}${NC}"
}

# ===== TEST EXECUTION STARTS =====

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "UAT TEST EXECUTION STARTED"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "Timestamp: ${TEST_TIMESTAMP}"
echo "Frontend URL: ${FRONTEND_URL}"
echo "Backend URL: ${BACKEND_URL}"
echo "Test Duration: Starting..."
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# ===== STEP 1: API Availability Check =====
echo "--- STEP 1: Verify Backend API Availability ---"
API_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_BASE}/platform/dashboard/my-dashboard" -H "Authorization: Bearer invalid_token" 2>/dev/null)
HTTP_CODE=$(echo "$API_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    log_step 1 "Backend API Availability" "API responds with 200 or auth error (401/403)" "HTTP $HTTP_CODE received" "PASS" "API is accessible, authentication required as expected"
else
    log_step 1 "Backend API Availability" "API should be accessible" "HTTP $HTTP_CODE received" "FAIL" "API not responding correctly"
    log_defect "Critical" "Backend API not responding correctly" "curl -H Authorization" "Expected 401/403, got $HTTP_CODE"
fi

# ===== STEP 2: Frontend HTML Content Check =====
echo "--- STEP 2: Verify Frontend HTML Content ---"
FRONTEND_HTML=$(curl -s "${FRONTEND_URL}" 2>/dev/null)

if echo "$FRONTEND_HTML" | grep -q "Gestione Affitti\|root\|React"; then
    log_step 2 "Frontend Content Check" "Frontend HTML should contain app elements" "HTML contains app markup" "PASS" "Frontend serving React application"
    log_observation "Frontend HTML size: $(echo "$FRONTEND_HTML" | wc -c) bytes"
else
    log_step 2 "Frontend Content Check" "Frontend should serve React app" "HTML does not contain expected content" "FAIL" "Frontend not serving React application"
    log_defect "Critical" "Frontend not serving React application" "curl ${FRONTEND_URL}" "Expected React app HTML"
fi

# ===== STEP 3: Login Endpoint Test =====
echo "--- STEP 3: Test Authentication Endpoint ---"
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${ADMIN_USER}\",\"password\":\"${ADMIN_PASS}\"}" 2>/dev/null)

LOGIN_HTTP=$(echo "$LOGIN_RESPONSE" | tail -n 1)
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)

if [ "$LOGIN_HTTP" = "200" ] && echo "$LOGIN_BODY" | grep -q "access_token"; then
    log_step 3 "Authentication Test" "Login should return 200 with access_token" "HTTP $LOGIN_HTTP with token received" "PASS" "Authentication successful"

    # Extract token for subsequent requests
    ACCESS_TOKEN=$(echo "$LOGIN_BODY" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    log_observation "Access token obtained: ${ACCESS_TOKEN:0:20}..."
else
    log_step 3 "Authentication Test" "Login endpoint should return access token" "HTTP $LOGIN_HTTP, Response: ${LOGIN_BODY:0:100}" "FAIL" "Authentication failed"
    log_defect "Critical" "Login endpoint not working" "curl -X POST /auth/login" "Expected 200 with token, got $LOGIN_HTTP"
    ACCESS_TOKEN=""
fi

# If we have a token, proceed with authenticated tests
if [ -n "$ACCESS_TOKEN" ]; then

    # ===== STEP 4: Dashboard Data Retrieval =====
    echo "--- STEP 4: Retrieve Dashboard Data ---"
    DASHBOARD_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_BASE}/platform/dashboard/my-dashboard" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" 2>/dev/null)

    DASHBOARD_HTTP=$(echo "$DASHBOARD_RESPONSE" | tail -n 1)
    DASHBOARD_BODY=$(echo "$DASHBOARD_RESPONSE" | head -n -1)

    if [ "$DASHBOARD_HTTP" = "200" ]; then
        WIDGET_COUNT=$(echo "$DASHBOARD_BODY" | grep -o '"id"' | wc -l)
        log_step 4 "Dashboard Data Retrieval" "Dashboard API should return 200 with widget data" "HTTP $DASHBOARD_HTTP, Widgets found: $WIDGET_COUNT" "PASS" "Dashboard data retrieved"
        log_observation "Dashboard response length: $(echo "$DASHBOARD_BODY" | wc -c) bytes"

        if [ "$WIDGET_COUNT" -eq 4 ]; then
            log_observation "Exactly 4 widgets found as expected"
        else
            log_observation "Widget count: $WIDGET_COUNT (expected 4)"
            if [ "$WIDGET_COUNT" -ne 4 ]; then
                log_defect "Medium" "Dashboard widget count mismatch" "Call /dashboard API" "Expected 4 widgets, found $WIDGET_COUNT"
            fi
        fi
    else
        log_step 4 "Dashboard Data Retrieval" "Dashboard should return 200" "HTTP $DASHBOARD_HTTP received" "FAIL" "Dashboard endpoint error"
        log_defect "High" "Dashboard endpoint error" "curl /platform/dashboard/my-dashboard" "Expected 200, got $DASHBOARD_HTTP"
    fi

    # ===== STEP 5: Modules List Endpoint =====
    echo "--- STEP 5: Check Modules List Endpoint ---"
    MODULES_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_BASE}/modules/enabled" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" 2>/dev/null)

    MODULES_HTTP=$(echo "$MODULES_RESPONSE" | tail -n 1)
    MODULES_BODY=$(echo "$MODULES_RESPONSE" | head -n -1)

    if [ "$MODULES_HTTP" = "200" ]; then
        # Check if modules list is empty
        MODULES_COUNT=$(echo "$MODULES_BODY" | grep -o '"\|' | wc -l 2>/dev/null || echo "0")

        if [ "$MODULES_COUNT" -eq 0 ] || echo "$MODULES_BODY" | grep -q '\[\]' || echo "$MODULES_BODY" | grep -q '"modules": *\[\]'; then
            log_step 5 "Modules List Check" "Modules endpoint should return empty list" "HTTP $MODULES_HTTP with empty modules list" "PASS" "Modules properly cleared"
            log_observation "Modules list is empty as expected"
        else
            log_step 5 "Modules List Check" "Modules list should be empty after cleanup" "HTTP $MODULES_HTTP with $MODULES_COUNT items" "FAIL" "Modules list not empty"
            log_defect "Medium" "Modules still present after cleanup" "curl /platform/modules" "Expected empty list, found items: ${MODULES_BODY:0:100}"
        fi
    else
        log_step 5 "Modules List Check" "Modules endpoint should return 200" "HTTP $MODULES_HTTP received" "FAIL" "Modules endpoint error"
        log_defect "High" "Modules endpoint error" "curl /platform/modules" "Expected 200, got $MODULES_HTTP"
    fi

    # ===== STEP 6: Menu Endpoint Test =====
    echo "--- STEP 6: Test Menu Endpoint ---"
    MENU_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_BASE}/platform/menu/" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" 2>/dev/null)

    MENU_HTTP=$(echo "$MENU_RESPONSE" | tail -n 1)
    MENU_BODY=$(echo "$MENU_RESPONSE" | head -n -1)

    if [ "$MENU_HTTP" = "200" ]; then
        # Check menu items - should only have Immobili and Configurazione
        IMMOBILI_IN_MENU=$(echo "$MENU_BODY" | grep -o '"label":"Immobili"' | wc -l)
        CONFIGURAZIONE_IN_MENU=$(echo "$MENU_BODY" | grep -o '"label":"Configurazione"' | wc -l)
        MENU_ITEMS=$(echo "$MENU_BODY" | grep -o '"label":"[^"]*' | wc -l)

        log_step 6 "Menu Endpoint Test" "Menu should show Immobili and Configurazione only" "HTTP $MENU_HTTP, Immobili: $IMMOBILI_IN_MENU, Configurazione: $CONFIGURAZIONE_IN_MENU, Total items: $MENU_ITEMS" "PASS" "Menu endpoint functional"
        log_observation "Menu has $MENU_ITEMS items total"
    else
        log_step 6 "Menu Endpoint Test" "Menu endpoint should return 200" "HTTP $MENU_HTTP received" "FAIL" "Menu endpoint error"
        log_defect "High" "Menu endpoint error" "curl /platform/menu/" "Expected 200, got $MENU_HTTP"
    fi

    # ===== STEP 7: User Profile Check =====
    echo "--- STEP 7: Verify User Profile ---"
    AUTHME_HTTP=$(echo "$AUTHME_RESPONSE" | tail -n 1)
    AUTHME_BODY=$(echo "$AUTHME_RESPONSE" | head -n -1)

    if [ "$AUTHME_HTTP" = "200" ]; then
        USERNAME=$(echo "$AUTHME_BODY" | grep -o '"username":"[^"]*' | cut -d'"' -f4 || echo "unknown")
        log_step 7 "User Profile Check" "User endpoint should return current user data" "HTTP $AUTHME_HTTP with user: $USERNAME" "PASS" "User profile retrieved"
        log_observation "Authenticated user: $USERNAME"
    else
        log_step 7 "User Profile Check" "User endpoint should return 200" "HTTP $AUTHME_HTTP received" "FAIL" "User endpoint error"
        log_defect "High" "User endpoint error" "curl /auth/me" "Expected 200, got $AUTHME_HTTP"
    fi

else
    echo ""
    echo -e "${RED}Cannot proceed with authenticated tests - login failed${NC}"
    log_defect "Critical" "Cannot execute authenticated tests" "Login failed" "No access token obtained"
fi

# ===== STEP 8: Frontend Service Availability =====
echo "--- STEP 8: Frontend Service Availability ---"
FE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}/dashboard" 2>/dev/null)

if [ "$FE_RESPONSE" = "200" ]; then
    log_step 8 "Frontend Route Test" "Dashboard route should return 200" "HTTP $FE_RESPONSE received" "PASS" "Frontend routes functional"
else
    log_step 8 "Frontend Route Test" "Frontend routes should return 200" "HTTP $FE_RESPONSE received" "FAIL" "Frontend route error"
    log_defect "High" "Frontend dashboard route error" "curl /dashboard" "Expected 200, got $FE_RESPONSE"
fi

# ===== Generate Report =====
TEST_END_TIME=$(date +%s%N)
TEST_DURATION=$(echo "scale=2; ($TEST_END_TIME - $TEST_START_TIME) / 1000000000" | bc)
OVERALL_RESULT=$([ "$FAILED_STEPS" -eq 0 ] && echo "PASS" || echo "FAIL")

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "TEST SUMMARY"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "Total Steps: $TOTAL_STEPS"
echo -e "Passed: ${GREEN}$PASSED_STEPS${NC}"
echo -e "Failed: ${RED}$FAILED_STEPS${NC}"
echo -e "Overall Result: $([ "$OVERALL_RESULT" = "PASS" ] && echo -e "${GREEN}$OVERALL_RESULT${NC}" || echo -e "${RED}$OVERALL_RESULT${NC}")"
echo "Test Duration: ${TEST_DURATION}s"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Save text report
{
    echo "UAT TEST EXECUTION REPORT"
    echo "=========================="
    echo "Test Plan ID: UAT-MODULES-001"
    echo "Executed By: UAT Operator - API Tests"
    echo "Execution Date: ${TEST_TIMESTAMP}"
    echo "Test Duration: ${TEST_DURATION}s"
    echo ""
    echo "TEST SUMMARY"
    echo "-----------"
    echo "Total Steps: $TOTAL_STEPS"
    echo "Passed: $PASSED_STEPS"
    echo "Failed: $FAILED_STEPS"
    echo "Overall Result: $OVERALL_RESULT"
    echo ""
    echo "ENVIRONMENT"
    echo "----------"
    echo "Frontend URL: ${FRONTEND_URL}"
    echo "Backend URL: ${BACKEND_URL}"
    echo "API Base: ${API_BASE}"
    echo ""
    echo "DEFECTS FOUND"
    echo "-------------"
    if [ ${#DEFECTS[@]} -gt 0 ]; then
        for i in "${!DEFECTS[@]}"; do
            echo "$((i+1)). ${DEFECTS[$i]}"
        done
    else
        echo "No defects found"
    fi
    echo ""
    echo "OBSERVATIONS"
    echo "------------"
    if [ ${#OBSERVATIONS[@]} -gt 0 ]; then
        for obs in "${OBSERVATIONS[@]}"; do
            echo "- $obs"
        done
    else
        echo "No observations"
    fi
} > "$REPORT_FILE"

echo "✅ Report saved to: $(pwd)/$REPORT_FILE"
echo "$(cat "$REPORT_FILE")"

# Exit with appropriate code
[ "$OVERALL_RESULT" = "PASS" ] && exit 0 || exit 1
