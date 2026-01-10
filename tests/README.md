# Tests

Questa cartella contiene i test e i report di analisi del progetto Gestione Affitti.

## Struttura

```
tests/
├── uat/                    # Test User Acceptance Testing
│   ├── uat-test.mjs        # Script test UAT principale (Node.js)
│   ├── uat-test-api.sh     # Script test API (Bash)
│   ├── run-affitti-test.sh # Runner test affitti
│   └── UAT_*.json/md       # Report e risultati UAT
│
├── import-automatismi/     # Test sistema import automatico
│   ├── test_*.py           # Script Python per test import
│   ├── test_*.csv          # Dataset di test
│   └── REPORT_*.md         # Report analisi
│
└── reports/                # Report di analisi generale
    ├── COMUNI_ANALYSIS_REPORT.md
    └── IMMOBILI_MODULE_TEST_REPORT.md
```

## Test UAT

I test UAT (User Acceptance Testing) verificano le funzionalità dal punto di vista dell'utente finale.

### Esecuzione

```bash
# Prerequisiti: backend in esecuzione su localhost:8000

# Test con Node.js
node tests/uat/uat-test.mjs

# Test con Bash
chmod +x tests/uat/uat-test-api.sh
./tests/uat/uat-test-api.sh

# Test affitti con Playwright
chmod +x tests/uat/run-affitti-test.sh
./tests/uat/run-affitti-test.sh
```

## Test Import Automatismi

Test per il sistema di import automatico di dati immobiliari.

```bash
cd tests/import-automatismi

# Esegui test Python
python test_import_api.py
python test_smart_parser.py
```

## Test E2E Frontend

I test end-to-end Playwright sono nella cartella `frontend/e2e/`:

```bash
cd frontend
npx playwright test
```

## Note

Questi test sono stati usati durante lo sviluppo per validare le funzionalità.
Per test automatizzati in CI/CD, considerare framework come:
- **Backend:** pytest
- **Frontend:** Vitest + React Testing Library, Playwright
