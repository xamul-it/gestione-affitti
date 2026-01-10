#!/usr/bin/env node

/**
 * UAT Test Operator #2 - Affitti Lungo Module Regression Test
 * Test Plan: TC-002
 *
 * This script performs comprehensive regression testing on the Affitti Lungo module:
 * - Validates all component files exist and have correct imports
 * - Tests cross-module dependencies (immobili module)
 * - Verifies CSS cross-imports
 * - Checks API endpoint accessibility
 * - Generates detailed UAT report
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import axios from 'axios';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const FRONTEND_ROOT = __dirname;
const MODULES_DIR = path.join(FRONTEND_ROOT, 'src/modules');
const AFFITTI_LUNGO_DIR = path.join(MODULES_DIR, 'affitti_lungo');
const IMMOBILI_DIR = path.join(MODULES_DIR, 'immobili');
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Test Report
const report = {
  testPlanId: 'TC-002',
  title: 'Affitti Lungo Module Non-Regression Test',
  executedBy: 'UAT Operator #2',
  executionDate: new Date().toISOString(),
  startTime: Date.now(),
  totalSteps: 0,
  passedSteps: 0,
  failedSteps: 0,
  blockedSteps: 0,
  detailedLog: [],
  defects: [],
  crossModuleTests: [],
  structureValidation: [],
  apiTests: [],
};

// Utility functions
function logStep(stepNumber, description, status, notes = '', evidence = null) {
  report.totalSteps++;
  const step = {
    stepNumber,
    description,
    status,
    timestamp: new Date().toISOString(),
    notes,
    evidence,
  };
  report.detailedLog.push(step);

  if (status === 'PASS') report.passedSteps++;
  else if (status === 'FAIL') report.failedSteps++;
  else if (status === 'BLOCKED') report.blockedSteps++;

  const icon = status === 'PASS' ? '✓' : status === 'FAIL' ? '✗' : '⊗';
  console.log(`${icon} Step ${stepNumber}: ${description} [${status}]${notes ? ' - ' + notes : ''}`);
}

function logDefect(severity, description, stepsToReproduce, expectedVsActual, relatedStep = null) {
  const defectId = `DEF-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const defect = {
    defectId,
    severity,
    description,
    stepsToReproduce,
    expectedVsActual,
    timestamp: new Date().toISOString(),
    relatedStep,
  };
  report.defects.push(defect);
  console.error(`  [${severity}] Defect ${defectId}: ${description}`);
}

function logCrossModuleTest(testName, result, details = {}) {
  const test = {
    test: testName,
    result,
    ...details,
  };
  report.crossModuleTests.push(test);
}

// Test 1: Verify all 6 component directories exist
async function testComponentDirectories() {
  console.log('\n=== Test 1: Component Directory Structure ===\n');

  const components = [
    { name: 'Affittuari', path: 'components/Affittuari' },
    { name: 'Contratti', path: 'components/Contratti' },
    { name: 'Incassi', path: 'components/Incassi' },
    { name: 'Spese', path: 'components/Spese' },
    { name: 'Tecnici', path: 'components/Tecnici' },
    { name: 'Documenti', path: 'components/Documenti' },
  ];

  let allExist = true;

  for (const comp of components) {
    const compPath = path.join(AFFITTI_LUNGO_DIR, comp.path);
    const exists = fs.existsSync(compPath);

    if (exists) {
      const files = fs.readdirSync(compPath);
      logStep(
        report.totalSteps + 1,
        `Component directory exists: ${comp.name}`,
        'PASS',
        `${files.length} files found`
      );
    } else {
      logStep(
        report.totalSteps + 1,
        `Component directory exists: ${comp.name}`,
        'FAIL',
        `Directory not found: ${compPath}`
      );
      logDefect(
        'CRITICAL',
        `Component directory missing: ${comp.name}`,
        ['Check modules/affitti_lungo/components directory'],
        `Expected: Directory exists | Actual: Directory not found`
      );
      allExist = false;
    }
  }

  if (allExist) {
    report.structureValidation.push({
      test: 'All 6 component directories exist',
      result: 'PASS',
      components: components.map((c) => c.name),
    });
  }

  return allExist;
}

// Test 2: Verify component files and imports
async function testComponentFiles() {
  console.log('\n=== Test 2: Component Files and Imports ===\n');

  const componentFiles = {
    'Affittuari/AffittuariList.jsx': {
      shouldContain: ['import.*affittuariAPI'],
      crossModule: false,
    },
    'Affittuari/AffittuarioForm.jsx': {
      shouldContain: ['affittuariAPI'],
      crossModule: false,
    },
    'Contratti/ContrattiList.jsx': {
      shouldContain: ['contrattiAPI', 'unitaImmobiliariAPI'],
      crossModule: true,
    },
    'Contratti/ContrattoForm.jsx': {
      shouldContain: ['contrattiAPI'],
      crossModule: false,
    },
    'Incassi/IncassiList.jsx': {
      shouldContain: ['incassiAPI'],
      crossModule: false,
    },
    'Incassi/IncassoForm.jsx': {
      shouldContain: ['incassiAPI'],
      crossModule: false,
    },
    'Spese/SpeseList.jsx': {
      shouldContain: ['speseAPI', 'unitaImmobiliariAPI'],
      crossModule: true,
    },
    'Spese/SpesaForm.jsx': {
      shouldContain: ['speseAPI'],
      crossModule: false,
    },
    'Tecnici/TecniciList.jsx': {
      shouldContain: ['tecniciAPI'],
      crossModule: false,
    },
    'Tecnici/TecnicoForm.jsx': {
      shouldContain: ['tecniciAPI'],
      crossModule: false,
    },
    'Documenti/DocumentiSection.jsx': {
      shouldContain: ['documentiAPI'],
      crossModule: false,
    },
    'Documenti/DocumentoUpload.jsx': {
      shouldContain: ['documentiAPI'],
      crossModule: false,
    },
  };

  let allFilesValid = true;

  for (const [filePath, config] of Object.entries(componentFiles)) {
    const fullPath = path.join(AFFITTI_LUNGO_DIR, 'components', filePath);

    if (!fs.existsSync(fullPath)) {
      logStep(
        report.totalSteps + 1,
        `File exists: ${filePath}`,
        'FAIL',
        `File not found`
      );
      allFilesValid = false;
      continue;
    }

    const content = fs.readFileSync(fullPath, 'utf8');
    let importsValid = true;
    const missingImports = [];

    for (const pattern of config.shouldContain) {
      if (!content.match(new RegExp(pattern, 'i'))) {
        importsValid = false;
        missingImports.push(pattern);
      }
    }

    if (importsValid) {
      const crossModuleNote = config.crossModule ? '(cross-module)' : '';
      logStep(
        report.totalSteps + 1,
        `File imports valid: ${filePath} ${crossModuleNote}`,
        'PASS',
        `All required imports found`
      );
    } else {
      logStep(
        report.totalSteps + 1,
        `File imports valid: ${filePath}`,
        'FAIL',
        `Missing imports: ${missingImports.join(', ')}`
      );
      logDefect(
        'HIGH',
        `File has missing imports: ${filePath}`,
        [`Check file: ${fullPath}`],
        `Expected: Contains ${config.shouldContain.join(', ')} | Actual: Missing ${missingImports.join(', ')}`
      );
      allFilesValid = false;
    }
  }

  return allFilesValid;
}

// Test 3: Verify API service file
async function testAPIService() {
  console.log('\n=== Test 3: API Service File ===\n');

  const apiPath = path.join(AFFITTI_LUNGO_DIR, 'services', 'affittiAPI.js');

  if (!fs.existsSync(apiPath)) {
    logStep(
      report.totalSteps + 1,
      'API service file exists',
      'FAIL',
      `File not found: ${apiPath}`
    );
    logDefect(
      'CRITICAL',
      'affittiAPI.js service file not found',
      ['Check modules/affitti_lungo/services/'],
      `Expected: affittiAPI.js exists | Actual: File not found`
    );
    return false;
  }

  const content = fs.readFileSync(apiPath, 'utf8');
  const expectedExports = [
    'affittuariAPI',
    'contrattiAPI',
    'speseAPI',
    'incassiAPI',
    'tecniciAPI',
    'documentiAPI',
  ];

  let allExported = true;
  for (const exported of expectedExports) {
    if (!content.includes(`export const ${exported}`)) {
      allExported = false;
      logStep(
        report.totalSteps + 1,
        `API export exists: ${exported}`,
        'FAIL'
      );
    }
  }

  if (allExported) {
    logStep(
      report.totalSteps + 1,
      'API service file structure',
      'PASS',
      `All ${expectedExports.length} API objects exported`
    );
  }

  return allExported;
}

// Test 4: Verify cross-module imports in Contratti and Spese
async function testCrossModuleImports() {
  console.log('\n=== Test 4: Cross-Module Imports (immobili module) ===\n');

  const crossModuleChecks = [
    {
      file: 'components/Contratti/ContrattiList.jsx',
      shouldImport: 'unitaImmobiliariAPI',
      from: '../../../../services/api',
      description: 'ContrattiList imports unitaImmobiliariAPI from immobili module',
    },
    {
      file: 'components/Spese/SpeseList.jsx',
      shouldImport: 'unitaImmobiliariAPI',
      from: '../../../../services/api',
      description: 'SpeseList imports unitaImmobiliariAPI from immobili module',
    },
  ];

  let allImportsValid = true;

  for (const check of crossModuleChecks) {
    const fullPath = path.join(AFFITTI_LUNGO_DIR, check.file);

    if (!fs.existsSync(fullPath)) {
      logStep(
        report.totalSteps + 1,
        check.description,
        'BLOCKED',
        `File not found: ${check.file}`
      );
      allImportsValid = false;
      continue;
    }

    const content = fs.readFileSync(fullPath, 'utf8');

    // Check for the import statement
    const importPattern = new RegExp(
      `import\\s*\\{[^}]*${check.shouldImport}[^}]*\\}\\s*from\\s*['"]${check.from.replace(/\//g, '\\/')}['"]`
    );

    if (importPattern.test(content)) {
      logStep(
        report.totalSteps + 1,
        check.description,
        'PASS',
        `Cross-module import verified`
      );
      logCrossModuleTest(check.description, 'PASS', {
        file: check.file,
        import: check.shouldImport,
        source: check.from,
      });
    } else {
      // Try simpler check
      if (content.includes(check.shouldImport) && content.includes(check.from)) {
        logStep(
          report.totalSteps + 1,
          check.description,
          'PASS',
          `Cross-module import found (pattern variation)`
        );
        logCrossModuleTest(check.description, 'PASS', {
          file: check.file,
          import: check.shouldImport,
          note: 'Pattern variation detected',
        });
      } else {
        logStep(
          report.totalSteps + 1,
          check.description,
          'FAIL',
          `Cross-module import not found`
        );
        logDefect(
          'HIGH',
          `Missing cross-module import: ${check.shouldImport}`,
          [`Check file: ${check.file}`],
          `Expected: Import ${check.shouldImport} from ${check.from} | Actual: Not found`,
          report.totalSteps
        );
        logCrossModuleTest(check.description, 'FAIL', {
          file: check.file,
          import: check.shouldImport,
          error: 'Import not found',
        });
        allImportsValid = false;
      }
    }
  }

  return allImportsValid;
}

// Test 5: Verify CSS cross-imports
async function testCSSCrossImports() {
  console.log('\n=== Test 5: CSS Cross-Imports ===\n');

  const tecniciCSSPath = path.join(AFFITTI_LUNGO_DIR, 'components/Tecnici/Tecnici.css');
  const immobiliCSSPath = path.join(IMMOBILI_DIR, 'components/UnitaImmobiliari/UnitaImmobiliari.css');

  if (!fs.existsSync(tecniciCSSPath)) {
    logStep(
      report.totalSteps + 1,
      'CSS cross-import (Tecnici.css)',
      'BLOCKED',
      `File not found: ${tecniciCSSPath}`
    );
    return false;
  }

  const tecniciContent = fs.readFileSync(tecniciCSSPath, 'utf8');

  if (!fs.existsSync(immobiliCSSPath)) {
    logStep(
      report.totalSteps + 1,
      'CSS cross-import (UnitaImmobiliari.css)',
      'BLOCKED',
      `Imported file not found: ${immobiliCSSPath}`
    );
    logDefect(
      'HIGH',
      'Cross-imported CSS file missing',
      ['Check modules/immobili/components/UnitaImmobiliari/'],
      `Expected: UnitaImmobiliari.css exists | Actual: File not found`
    );
    return false;
  }

  // Check if Tecnici.css imports from immobili
  const cssImportPattern = /@import\s+['"].*UnitaImmobiliari\.css['"]/;

  if (cssImportPattern.test(tecniciContent)) {
    logStep(
      report.totalSteps + 1,
      'CSS cross-import (Tecnici imports UnitaImmobiliari)',
      'PASS',
      `CSS import found in Tecnici.css`
    );
    logCrossModuleTest('Tecnici.css imports UnitaImmobiliari.css', 'PASS', {
      source: 'Tecnici.css',
      target: 'UnitaImmobiliari.css',
      moduleFrom: 'immobili',
    });
    return true;
  } else {
    logStep(
      report.totalSteps + 1,
      'CSS cross-import (Tecnici imports UnitaImmobiliari)',
      'FAIL',
      `CSS import not found`
    );
    logDefect(
      'MEDIUM',
      'CSS cross-import missing',
      ['Check Tecnici.css'],
      `Expected: @import '...UnitaImmobiliari.css' | Actual: Not found`,
      report.totalSteps
    );
    logCrossModuleTest('Tecnici.css imports UnitaImmobiliari.css', 'FAIL', {
      error: 'Import statement not found',
    });
    return false;
  }
}

// Test 6: Check manifest file
async function testManifest() {
  console.log('\n=== Test 6: Module Manifest ===\n');

  const manifestPath = path.join(AFFITTI_LUNGO_DIR, 'manifest.js');

  if (!fs.existsSync(manifestPath)) {
    logStep(
      report.totalSteps + 1,
      'Manifest file exists',
      'FAIL',
      `File not found: ${manifestPath}`
    );
    return false;
  }

  const content = fs.readFileSync(manifestPath, 'utf8');

  const requiredFields = [
    'id',
    'name',
    'version',
    'dependencies',
    'routes',
    'permissions',
  ];

  let allFieldsPresent = true;
  for (const field of requiredFields) {
    if (!content.includes(`${field}:`)) {
      allFieldsPresent = false;
      logStep(
        report.totalSteps + 1,
        `Manifest field present: ${field}`,
        'FAIL'
      );
    }
  }

  if (allFieldsPresent) {
    logStep(
      report.totalSteps + 1,
      'Manifest file structure',
      'PASS',
      `All required fields present`
    );

    // Check dependencies
    if (content.includes("'immobili'") && content.includes("'anagrafica_italiana'")) {
      logStep(
        report.totalSteps + 1,
        'Manifest dependencies',
        'PASS',
        `Dependencies: immobili, anagrafica_italiana`
      );
    }
  }

  return allFieldsPresent;
}

// Test 7: Test API endpoints
async function testAPIEndpoints() {
  console.log('\n=== Test 7: API Endpoint Accessibility ===\n');

  const endpoints = [
    { path: '/affittuari/', name: 'Affittuari' },
    { path: '/contratti/', name: 'Contratti' },
    { path: '/incassi/', name: 'Incassi' },
    { path: 'path: /spese/', name: 'Spese' },
    { path: '/tecnici/', name: 'Tecnici' },
    { path: '/documenti/', name: 'Documenti (requires params)' },
    { path: '/unita-immobiliari/', name: 'UnitaImmobiliari (cross-module)' },
  ];

  for (const endpoint of endpoints) {
    try {
      const url = `${API_BASE_URL}${endpoint.path}`;
      const response = await axios.get(url, { timeout: 5000 }).catch((e) => ({ status: e.response?.status }));

      if (response.status === 200 || response.status === 401 || response.status === 400) {
        // 400 might be returned if params are required
        logStep(
          report.totalSteps + 1,
          `API endpoint: ${endpoint.name}`,
          'PASS',
          `Status: ${response.status}`
        );
        report.apiTests.push({
          endpoint: endpoint.path,
          name: endpoint.name,
          status: 'PASS',
          httpStatus: response.status,
        });
      } else {
        logStep(
          report.totalSteps + 1,
          `API endpoint: ${endpoint.name}`,
          'FAIL',
          `Status: ${response.status}`
        );
        report.apiTests.push({
          endpoint: endpoint.path,
          name: endpoint.name,
          status: 'FAIL',
          httpStatus: response.status,
        });
      }
    } catch (e) {
      const message = e.code === 'ECONNREFUSED' ? 'Backend not running' : e.message;
      logStep(
        report.totalSteps + 1,
        `API endpoint: ${endpoint.name}`,
        'BLOCKED',
        message
      );
      report.apiTests.push({
        endpoint: endpoint.path,
        name: endpoint.name,
        status: 'BLOCKED',
        error: message,
      });
    }
  }
}

// Test 8: Verify module index file
async function testModuleIndex() {
  console.log('\n=== Test 8: Module Index File ===\n');

  const indexPath = path.join(AFFITTI_LUNGO_DIR, 'index.js');

  if (!fs.existsSync(indexPath)) {
    logStep(
      report.totalSteps + 1,
      'Module index file exists',
      'BLOCKED',
      `File not found: ${indexPath}`
    );
    return false;
  }

  const content = fs.readFileSync(indexPath, 'utf8');

  if (content.includes('manifest') && content.includes('export')) {
    logStep(
      report.totalSteps + 1,
      'Module index exports manifest',
      'PASS'
    );
    return true;
  } else {
    logStep(
      report.totalSteps + 1,
      'Module index exports manifest',
      'FAIL',
      'Manifest export not found'
    );
    return false;
  }
}

// Main execution
async function runTests() {
  console.log(`
=====================================
UAT TEST EXECUTION - AFFITTI LUNGO MODULE
Test Plan: TC-002
Test Operator: #2
Date: ${new Date().toISOString()}
=====================================
`);

  try {
    await testComponentDirectories();
    await testComponentFiles();
    await testAPIService();
    await testCrossModuleImports();
    await testCSSCrossImports();
    await testManifest();
    await testModuleIndex();
    await testAPIEndpoints();

    // Summary
    console.log(`
=====================================
TEST EXECUTION SUMMARY
=====================================
Total Steps: ${report.totalSteps}
Passed: ${report.passedSteps}
Failed: ${report.failedSteps}
Blocked: ${report.blockedSteps}
Overall Result: ${report.failedSteps === 0 ? (report.blockedSteps > 0 ? 'BLOCKED' : 'PASS') : 'FAIL'}
Defects Found: ${report.defects.length}
Cross-Module Tests: ${report.crossModuleTests.length}
=====================================
    `);

    // Save report
    report.endTime = Date.now();
    report.duration = ((report.endTime - report.startTime) / 1000).toFixed(2);
    report.overallResult = report.failedSteps === 0 ? (report.blockedSteps > 0 ? 'BLOCKED' : 'PASS') : 'FAIL';

    const reportsDir = path.join(FRONTEND_ROOT, 'test-results');
    if (!fs.existsSync(reportsDir)) {
      fs.mkdirSync(reportsDir, { recursive: true });
    }

    const reportPath = path.join(reportsDir, `uat-report-affitti-${Date.now()}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    console.log(`\nReport saved to: ${reportPath}`);

    // Print defects
    if (report.defects.length > 0) {
      console.log(`\n=== DEFECTS FOUND (${report.defects.length}) ===`);
      report.defects.forEach((defect) => {
        console.log(`
${defect.defectId} [${defect.severity}]
Description: ${defect.description}
Expected: ${defect.expectedVsActual.split('|')[0].trim()}
Actual: ${defect.expectedVsActual.split('|')[1]?.trim()}
        `);
      });
    }

    // Return exit code
    process.exit(report.failedSteps > 0 ? 1 : 0);
  } catch (e) {
    console.error('Test execution failed:', e);
    process.exit(1);
  }
}

runTests();
