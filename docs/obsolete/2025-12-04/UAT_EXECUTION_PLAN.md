# UAT TEST EXECUTION PLAN - Dashboard & Module System
**Test Plan ID**: UAT-MODULES-001
**Execution Date**: 2025-12-02
**UAT Operator**: Automated Test Suite
**Application**: Gestione Affitti

## Objective
Verify functionality of dashboard, menu system, and module management after system module cleanup.

## Test Environment
- Frontend URL: http://192.168.1.2:3000
- Backend URL: http://192.168.1.2:8000
- Database: PostgreSQL on port 5433
- Test User: admin / admin123

## Expected Behavior
- Dashboard should load with 4 widgets (even if components don't exist)
- Menu should show only 2 main items: "Immobili" and "Configurazione"
- Modules admin page should display "Nessun modulo disponibile"
- Properties page (/immobili) should function correctly
- No critical JavaScript errors in browser console

## Test Execution Steps

### STEP 1: Login Page Accessibility
**Step**: Navigate to login page
**URL**: http://192.168.1.2:3000
**Expected**: Login form displays with title "Gestione Affitti"
**Actions**: Load frontend homepage

### STEP 2: Admin Authentication
**Step**: Login with admin credentials
**URL**: http://192.168.1.2:3000/login
**Credentials**: admin / admin123
**Expected**: Redirect to dashboard or home page
**Actions**: Enter credentials and submit login form

### STEP 3: Dashboard Verification
**Step**: Navigate to dashboard
**URL**: http://192.168.1.2:3000/dashboard
**Expected**: Dashboard page loads with proper header and content area
**Actions**: Verify page loads successfully

### STEP 4: Dashboard Widgets Check
**Step**: Verify widget count and content
**Expected**: 4 widgets displayed in dashboard grid
**Actions**: Count visible widgets and capture titles
**Check**: Widget containers, titles, and placeholders

### STEP 5: Menu System Verification
**Step**: Check navigation menu
**Expected**: Menu shows only "Immobili" and "Configurazione" (plus Dashboard link)
**Actions**: Inspect navbar items
**Note**: "Affitti", "Condominio", "Servizi" should NOT be visible

### STEP 6: Modules Admin Page
**Step**: Navigate to modules admin page
**URL**: http://192.168.1.2:3000/admin/modules
**Expected**: Modules page loads successfully
**Actions**: Navigate to admin modules section

### STEP 7: Empty Modules Verification
**Step**: Verify empty state message
**Expected**: Display "Nessun modulo disponibile"
**Actions**: Check for empty state content and message text

### STEP 8: Properties Page Navigation
**Step**: Navigate to properties listing
**URL**: http://192.168.1.2:3000/immobili
**Expected**: Properties page loads successfully
**Actions**: Navigate to immobili section

### STEP 9: Console Error Check
**Step**: Verify no critical JavaScript errors
**Expected**: No error or warning messages in browser console
**Actions**: Monitor console throughout test execution

## Test Report Structure

Each test step will include:
- Step number and description
- Expected result
- Actual result
- Pass/Fail/Blocked status
- Screenshots at key points
- Defects found with severity
- User experience observations

## Defect Classification

| Severity | Description |
|----------|------------|
| Critical | Application crashes, unable to login, core functionality broken |
| High | Major feature not working, incorrect behavior affecting user tasks |
| Medium | Feature partially working, minor UI issues, workarounds available |
| Low | Cosmetic issues, minor improvements, no functional impact |

## Realistic User Behavior Simulation

This test operator will simulate natural user actions including:
- Normal navigation patterns
- Form field interactions
- Waiting for page loads
- Monitoring error states
- Checking UI consistency

## Test Success Criteria

- All 8 core steps must PASS
- No BLOCKED steps (unless permission issues documented)
- Dashboard loads with 4 widgets
- Menu shows correct items only
- Modules page shows empty state correctly
- Immobili page loads successfully
- No critical JavaScript console errors

**Overall Test Result**: PASS if all criteria met, FAIL if any critical failures occur
