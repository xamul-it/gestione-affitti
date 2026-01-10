const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const FRONTEND_URL = 'http://192.168.1.2:3000';
const BACKEND_URL = 'http://192.168.1.2:8000';
const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'admin123';

// Test execution timestamp
const testTimestamp = new Date().toISOString();
const testStartTime = Date.now();

// Test results tracking
const testResults = {
  steps: [],
  defects: [],
  observations: [],
  totalSteps: 0,
  passedSteps: 0,
  failedSteps: 0,
  blockedSteps: 0
};

// Logging helper
function logStep(stepNumber, description, expectedResult, actualResult, status, notes = '') {
  const step = {
    number: stepNumber,
    description,
    expectedResult,
    actualResult,
    status,
    notes,
    timestamp: new Date().toISOString()
  };
  testResults.steps.push(step);

  const statusSymbol = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : '⚠️';
  console.log(`\n${statusSymbol} STEP ${stepNumber}: ${description}`);
  console.log(`   Expected: ${expectedResult}`);
  console.log(`   Actual: ${actualResult}`);
  if (notes) console.log(`   Notes: ${notes}`);

  if (status === 'PASS') testResults.passedSteps++;
  else if (status === 'FAIL') testResults.failedSteps++;
  else testResults.blockedSteps++;
}

function logDefect(severity, description, stepsToReproduce, expectedVsActual) {
  const defectId = `DEFECT-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const defect = {
    id: defectId,
    severity,
    description,
    stepsToReproduce,
    expectedVsActual,
    timestamp: new Date().toISOString()
  };
  testResults.defects.push(defect);
  console.log(`\n🐛 ${severity} DEFECT FOUND: ${defectId}`);
  console.log(`   ${description}`);
}

function logObservation(text) {
  testResults.observations.push({
    text,
    timestamp: new Date().toISOString()
  });
  console.log(`\n📝 OBSERVATION: ${text}`);
}

async function captureScreenshot(page, stepNumber, fileName) {
  try {
    const screenshotPath = `./test-screenshots/step-${stepNumber}-${fileName}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`   📸 Screenshot saved: ${screenshotPath}`);
    return screenshotPath;
  } catch (err) {
    console.log(`   ⚠️ Could not capture screenshot: ${err.message}`);
    return null;
  }
}

async function runUATest() {
  let browser;
  let page;

  try {
    console.log('═'.repeat(80));
    console.log('UAT TEST EXECUTION STARTED');
    console.log('═'.repeat(80));
    console.log(`Timestamp: ${testTimestamp}`);
    console.log(`Frontend URL: ${FRONTEND_URL}`);
    console.log(`Backend URL: ${BACKEND_URL}`);
    console.log('═'.repeat(80));

    // Create screenshots directory
    if (!fs.existsSync('./test-screenshots')) {
      fs.mkdirSync('./test-screenshots', { recursive: true });
    }

    // Launch browser
    console.log('\n🚀 Launching Chromium browser...');
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 }
    });
    page = await context.newPage();

    // Track console messages
    const consoleLogs = [];
    page.on('console', msg => {
      consoleLogs.push({
        type: msg.type(),
        text: msg.text(),
        timestamp: new Date().toISOString()
      });
    });

    testResults.totalSteps = 8;

    // ========== STEP 1: Navigate to Login Page ==========
    console.log('\n--- STEP 1: Navigate to Login Page ---');
    try {
      await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
      const pageTitle = await page.title();
      const isLoginPage = await page.locator('text=Login').isVisible({ timeout: 5000 }).catch(() => false);

      if (isLoginPage && pageTitle.includes('Gestione Affitti')) {
        logStep(
          1,
          'Navigate to Login Page',
          'Login page should load with title "Gestione Affitti" and login form visible',
          `Page loaded successfully. Title: "${pageTitle}", Login form visible: ${isLoginPage}`,
          'PASS',
          'Initial page navigation successful'
        );
        await captureScreenshot(page, 1, 'login-page');
      } else {
        logStep(
          1,
          'Navigate to Login Page',
          'Login page should load',
          `Page title: ${pageTitle}, Login form visible: ${isLoginPage}`,
          'FAIL',
          'Expected login page not found'
        );
        logDefect('High', 'Login page did not load correctly',
          ['Navigate to ' + FRONTEND_URL],
          `Expected login page, got title: ${pageTitle}`);
      }
    } catch (err) {
      logStep(1, 'Navigate to Login Page', 'Login page should load', err.message, 'FAIL', err.message);
      logDefect('Critical', 'Cannot navigate to login page', ['Navigate to ' + FRONTEND_URL], err.message);
    }

    // ========== STEP 2: Login as Admin ==========
    console.log('\n--- STEP 2: Login as Admin ---');
    try {
      await page.fill('#username', ADMIN_USERNAME);
      await page.fill('#password', ADMIN_PASSWORD);

      logObservation('Simulating realistic user behavior: attempting login with test credentials');

      await page.click('button:has-text("Login")');

      // Wait for redirect or error
      await page.waitForNavigation({ waitUntil: 'networkidle', timeout: 10000 }).catch(() => {});

      const currentUrl = page.url();
      const isDashboard = currentUrl.includes('/dashboard') || currentUrl.includes('/');
      const isStillLogin = currentUrl.includes('/login');

      if (isDashboard && !isStillLogin) {
        logStep(
          2,
          'Login as Admin',
          'Should redirect to dashboard after successful login',
          `Redirected to: ${currentUrl}, Dashboard URL detected: ${isDashboard}`,
          'PASS',
          `Successfully logged in as ${ADMIN_USERNAME}`
        );
        await captureScreenshot(page, 2, 'post-login');
      } else {
        // Check if there was an error message
        const errorMsg = await page.locator('.error-message').textContent().catch(() => 'No error message found');
        logStep(
          2,
          'Login as Admin',
          'Should redirect to dashboard',
          `Current URL: ${currentUrl}, Error: ${errorMsg}`,
          'FAIL',
          'Login did not redirect to dashboard'
        );
        logDefect('High', 'Login failed or did not redirect',
          ['Enter admin/admin123', 'Click Login button'],
          `Expected dashboard URL, got: ${currentUrl}`);
      }
    } catch (err) {
      logStep(2, 'Login as Admin', 'Should login successfully', err.message, 'FAIL', err.message);
      logDefect('Critical', 'Login step failed', ['Fill username', 'Fill password', 'Click login'], err.message);
    }

    // ========== STEP 3: Verify Dashboard Loads ==========
    console.log('\n--- STEP 3: Verify Dashboard Loads ---');
    try {
      // Navigate to dashboard explicitly
      await page.goto(`${FRONTEND_URL}/dashboard`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000); // Wait for dashboard to fully load

      const dashboardTitle = await page.locator('h1').first().textContent().catch(() => '');
      const hasDashboardContent = await page.locator('.dashboard-page').isVisible({ timeout: 5000 }).catch(() => false);

      if (dashboardTitle.includes('Dashboard') && hasDashboardContent) {
        logStep(
          3,
          'Verify Dashboard Loads',
          'Dashboard should load with correct title and layout',
          `Dashboard page visible. Title: "${dashboardTitle}", Dashboard content present: ${hasDashboardContent}`,
          'PASS',
          'Dashboard loaded successfully'
        );
        await captureScreenshot(page, 3, 'dashboard-loaded');
      } else {
        logStep(
          3,
          'Verify Dashboard Loads',
          'Dashboard page should display',
          `Title: "${dashboardTitle}", Content visible: ${hasDashboardContent}`,
          'FAIL',
          'Dashboard page not properly displayed'
        );
        logDefect('High', 'Dashboard did not load properly',
          ['Login successfully', 'Navigate to /dashboard'],
          `Expected dashboard title and content, got title: "${dashboardTitle}"`);
      }
    } catch (err) {
      logStep(3, 'Verify Dashboard Loads', 'Dashboard should load', err.message, 'FAIL', err.message);
      logDefect('High', 'Dashboard load failed', ['Navigate to /dashboard'], err.message);
    }

    // ========== STEP 4: Verify Dashboard Widgets ==========
    console.log('\n--- STEP 4: Verify Dashboard Widgets ---');
    try {
      const widgets = await page.locator('.widget-container').count();
      const widgetTitles = await page.locator('.widget-header h3').allTextContents();

      logObservation(`Dashboard contains ${widgets} widget(s): ${widgetTitles.join(', ')}`);

      if (widgets === 4) {
        logStep(
          4,
          'Verify Dashboard Widgets',
          'Dashboard should display 4 widgets',
          `Found exactly ${widgets} widgets. Titles: ${widgetTitles.join(', ')}`,
          'PASS',
          'All expected widgets present'
        );
      } else if (widgets > 0) {
        logStep(
          4,
          'Verify Dashboard Widgets',
          'Dashboard should display 4 widgets',
          `Found ${widgets} widgets (expected 4). Titles: ${widgetTitles.join(', ')}`,
          'FAIL',
          `Expected 4 widgets but found ${widgets}`
        );
        logDefect('Medium', 'Dashboard widget count mismatch',
          ['Navigate to /dashboard', 'Wait for widgets to load'],
          `Expected 4 widgets, found ${widgets}`);
      } else {
        logStep(
          4,
          'Verify Dashboard Widgets',
          'Dashboard should display widgets',
          `Found ${widgets} widgets`,
          'FAIL',
          'No widgets found on dashboard'
        );
        logDefect('High', 'No dashboard widgets found',
          ['Navigate to /dashboard'], 'Dashboard has no widgets');
      }

      await captureScreenshot(page, 4, 'dashboard-widgets');
    } catch (err) {
      logStep(4, 'Verify Dashboard Widgets', 'Widgets should be visible', err.message, 'FAIL', err.message);
      logDefect('High', 'Could not verify dashboard widgets', ['Navigate to /dashboard'], err.message);
    }

    // ========== STEP 5: Verify Menu Items ==========
    console.log('\n--- STEP 5: Verify Menu Shows Only "Immobili" and "Configurazione" ---');
    try {
      const menuItems = await page.locator('.navbar-menu .navbar-item:not(.user-menu)').count();
      const menuTexts = await page.locator('.navbar-menu .navbar-link').allTextContents();

      logObservation(`Found ${menuItems} menu items. Menu texts: ${menuTexts.join(', ')}`);

      // Filter out dashboard and user menu for core menu items
      const coreMenuItems = menuTexts.filter(text =>
        !text.includes('👤') &&
        !text.includes('Logout') &&
        !text.toLowerCase().includes('logout')
      );

      logObservation(`Core menu items (filtered): ${coreMenuItems.join(', ')}`);

      // Check if only Immobili and Configurazione are present
      const hasImmobili = coreMenuItems.some(item => item.includes('Immobili'));
      const hasConfigurazione = coreMenuItems.some(item => item.includes('Configurazione'));

      if (hasImmobili && hasConfigurazione && coreMenuItems.length <= 3) {
        logStep(
          5,
          'Verify Menu Items',
          'Menu should show only "Immobili" and "Configurazione" (plus Dashboard)',
          `Menu verified. Core items: ${coreMenuItems.join(', ')}`,
          'PASS',
          'Core menu items correct'
        );
      } else {
        logStep(
          5,
          'Verify Menu Items',
          'Menu should show only "Immobili" and "Configurazione"',
          `Found items: ${coreMenuItems.join(', ')}. Has Immobili: ${hasImmobili}, Has Configurazione: ${hasConfigurazione}`,
          'FAIL',
          `Expected 2 core menu items, found ${coreMenuItems.length}: ${coreMenuItems.join(', ')}`
        );

        if (coreMenuItems.length > 2) {
          logDefect('Medium', 'Menu shows extra items beyond Immobili and Configurazione',
            ['Check navbar after login'],
            `Expected 2 core items (Immobili, Configurazione), found ${coreMenuItems.length}: ${coreMenuItems.join(', ')}`);
        }
      }

      await captureScreenshot(page, 5, 'menu-verification');
    } catch (err) {
      logStep(5, 'Verify Menu Items', 'Menu should show specific items', err.message, 'FAIL', err.message);
      logDefect('High', 'Could not verify menu items', ['Check navbar'], err.message);
    }

    // ========== STEP 6: Navigate to Admin Modules Page ==========
    console.log('\n--- STEP 6: Navigate to /admin/modules ---');
    try {
      await page.goto(`${FRONTEND_URL}/admin/modules`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(1500);

      const modulesPageVisible = await page.locator('.modules-admin').isVisible({ timeout: 5000 }).catch(() => false);
      const pageTitle = await page.locator('h1, h2').first().textContent().catch(() => '');

      if (modulesPageVisible || pageTitle.includes('Moduli') || pageTitle.includes('Module')) {
        logStep(
          6,
          'Navigate to /admin/modules',
          'Modules admin page should load',
          `Page loaded successfully. Title visible: "${pageTitle}", Modules container visible: ${modulesPageVisible}`,
          'PASS',
          'Modules admin page accessible'
        );
        await captureScreenshot(page, 6, 'modules-page');
      } else {
        logStep(
          6,
          'Navigate to /admin/modules',
          'Modules admin page should load',
          `Page URL: ${page.url()}, Page title: "${pageTitle}"`,
          'FAIL',
          'Modules admin page did not load'
        );
        logDefect('Medium', 'Modules admin page not accessible',
          ['Navigate to /admin/modules'],
          `Page did not load as expected. Title: "${pageTitle}"`);
      }
    } catch (err) {
      logStep(6, 'Navigate to /admin/modules', 'Modules page should load', err.message, 'FAIL', err.message);
      logDefect('High', 'Navigation to /admin/modules failed', ['Navigate to /admin/modules'], err.message);
    }

    // ========== STEP 7: Verify "Nessun modulo disponibile" Message ==========
    console.log('\n--- STEP 7: Verify "Nessun modulo disponibile" Message ---');
    try {
      const noModulesMessage = await page.locator('text=Nessun modulo').isVisible({ timeout: 5000 }).catch(() => false);
      const emptyStateText = await page.locator('.empty-state, .no-modules, [class*="empty"]').textContent().catch(() => '');

      logObservation(`Modules page content: "${emptyStateText}"`);

      if (noModulesMessage || emptyStateText.includes('Nessun')) {
        logStep(
          7,
          'Verify "Nessun modulo disponibile" Message',
          'Modules page should display "Nessun modulo disponibile" message',
          `Message found: "${noModulesMessage ? 'Nessun modulo' : emptyStateText}"`,
          'PASS',
          'Correct empty state message displayed'
        );
      } else {
        logStep(
          7,
          'Verify "Nessun modulo disponibile" Message',
          'Should display "Nessun modulo disponibile"',
          `Page content: "${emptyStateText}"`,
          'FAIL',
          'Expected empty modules message not found'
        );
        logDefect('Medium', 'Modules page does not show empty state message',
          ['Navigate to /admin/modules'],
          'Expected "Nessun modulo disponibile" message, page shows something else');
      }

      await captureScreenshot(page, 7, 'modules-empty-state');
    } catch (err) {
      logStep(7, 'Verify Empty Modules Message', 'Should display empty modules message', err.message, 'FAIL', err.message);
      logDefect('Medium', 'Could not verify modules message', ['Navigate to /admin/modules'], err.message);
    }

    // ========== STEP 8: Navigate to Immobili Page ==========
    console.log('\n--- STEP 8: Navigate to /immobili ---');
    try {
      await page.goto(`${FRONTEND_URL}/immobili`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(1500);

      const immobiliPageVisible = await page.locator('.immobili-home, [class*="immobili"]').isVisible({ timeout: 5000 }).catch(() => false);
      const pageTitle = await page.locator('h1, h2').first().textContent().catch(() => '');
      const currentUrl = page.url();

      if (currentUrl.includes('/immobili') && (immobiliPageVisible || pageTitle.includes('Immobil'))) {
        logStep(
          8,
          'Navigate to /immobili',
          'Immobili page should load successfully',
          `URL: ${currentUrl}, Page loaded with title: "${pageTitle}", Content visible: ${immobiliPageVisible}`,
          'PASS',
          'Immobili page accessible and loaded'
        );
        await captureScreenshot(page, 8, 'immobili-page');
      } else {
        logStep(
          8,
          'Navigate to /immobili',
          'Immobili page should load',
          `URL: ${currentUrl}, Title: "${pageTitle}", Content visible: ${immobiliPageVisible}`,
          'FAIL',
          'Immobili page did not load properly'
        );
        logDefect('High', 'Immobili page did not load',
          ['Navigate to /immobili'],
          `Expected /immobili page, got URL: ${currentUrl}, Title: "${pageTitle}"`);
      }
    } catch (err) {
      logStep(8, 'Navigate to /immobili', 'Immobili page should load', err.message, 'FAIL', err.message);
      logDefect('High', 'Navigation to /immobili failed', ['Navigate to /immobili'], err.message);
    }

    // ========== CONSOLE ERROR CHECK ==========
    console.log('\n--- Checking for JavaScript Console Errors ---');
    const errorLogs = consoleLogs.filter(log => log.type === 'error' || log.type === 'warning');
    if (errorLogs.length > 0) {
      logObservation(`Found ${errorLogs.length} console error(s)/warning(s):`);
      errorLogs.forEach(log => {
        console.log(`   [${log.type.toUpperCase()}] ${log.text}`);
        if (log.type === 'error') {
          logDefect('High', 'JavaScript console error detected',
            ['Execute all steps above'],
            `Console error: ${log.text}`);
        }
      });
    } else {
      logObservation('No JavaScript errors or critical warnings found in console');
    }

    console.log(`\n📝 Total console logs: ${consoleLogs.length}`);

    // ========== GENERATE REPORT ==========
    const testDuration = ((Date.now() - testStartTime) / 1000).toFixed(2);
    const overallResult = testResults.failedSteps === 0 && testResults.blockedSteps === 0 ? 'PASS' : 'FAIL';

    console.log('\n' + '═'.repeat(80));
    console.log('TEST SUMMARY');
    console.log('═'.repeat(80));
    console.log(`Total Steps: ${testResults.totalSteps}`);
    console.log(`Passed: ${testResults.passedSteps} ✅`);
    console.log(`Failed: ${testResults.failedSteps} ❌`);
    console.log(`Blocked: ${testResults.blockedSteps} ⚠️`);
    console.log(`Overall Result: ${overallResult}`);
    console.log(`Test Duration: ${testDuration}s`);
    console.log('═'.repeat(80));

    // Save report to file
    const report = {
      testPlanId: 'UAT-MODULES-001',
      executedBy: 'UAT Operator - Automated',
      executionDate: testTimestamp,
      testDuration: `${testDuration}s`,
      summary: {
        totalSteps: testResults.totalSteps,
        passed: testResults.passedSteps,
        failed: testResults.failedSteps,
        blocked: testResults.blockedSteps,
        overallResult
      },
      detailedLog: testResults.steps,
      defects: testResults.defects,
      observations: testResults.observations,
      consoleLogs: consoleLogs.slice(0, 100)
    };

    const reportPath = './test-report-' + Date.now() + '.json';
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`\n✅ Detailed report saved to: ${reportPath}`);

    // Also save as formatted text
    const textReportPath = './test-report-' + Date.now() + '.txt';
    let textReport = `UAT TEST EXECUTION REPORT
========================
Test Plan ID: UAT-MODULES-001
Executed By: UAT Operator - Automated
Execution Date: ${testTimestamp}
Test Duration: ${testDuration}s

TEST SUMMARY
-----------
Total Steps: ${testResults.totalSteps}
Passed: ${testResults.passedSteps}
Failed: ${testResults.failedSteps}
Blocked: ${testResults.blockedSteps}
Overall Result: ${overallResult}

DETAILED EXECUTION LOG
---------------------
`;

    testResults.steps.forEach(step => {
      textReport += `
Step ${step.number}: ${step.description}
Expected Result: ${step.expectedResult}
Actual Result: ${step.actualResult}
Status: ${step.status}
${step.notes ? `Notes: ${step.notes}` : ''}
`;
    });

    if (testResults.defects.length > 0) {
      textReport += `

DEFECTS FOUND
------------
`;
      testResults.defects.forEach(defect => {
        textReport += `
Defect ID: ${defect.id}
Severity: ${defect.severity}
Description: ${defect.description}
Steps to Reproduce: ${defect.stepsToReproduce.join(' -> ')}
Expected vs Actual: ${defect.expectedVsActual}
`;
      });
    }

    textReport += `

OBSERVATIONS
-----------
`;
    testResults.observations.forEach(obs => {
      textReport += `- ${obs.text}\n`;
    });

    fs.writeFileSync(textReportPath, textReport);
    console.log(`✅ Text report saved to: ${textReportPath}`);

  } catch (err) {
    console.error('❌ FATAL ERROR:', err);
    logDefect('Critical', 'Test execution failed', ['Unknown'], err.message);
  } finally {
    // Cleanup
    if (page) await page.close().catch(() => {});
    if (browser) await browser.close().catch(() => {});

    console.log('\n🏁 Test execution completed');
    process.exit(testResults.failedSteps > 0 ? 1 : 0);
  }
}

// Run the test
runUATest().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
