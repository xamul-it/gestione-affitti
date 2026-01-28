# Backend Tests

Test suite per il sistema di gestione documentale di Gestione Affitti.

## Struttura

```
tests/
├── unit/                           # Unit tests (veloci, isolati)
│   ├── test_file_storage_tenant_aware.py
│   └── test_document_type_registry.py
│
├── integration/                    # Integration tests (richiedono DB)
│   ├── test_document_parsing_e2e.py
│   └── test_tenant_isolation.py
│
├── conftest.py                     # Fixture condivise
└── README.md                       # Questo file
```

## Setup

### Installare dipendenze

```bash
cd backend
pip install -r requirements-test.txt
```

### Configurare database di test

I test usano SQLite in-memory per default (vedi `conftest.py`).

## Esecuzione Tests

### Tutti i test

```bash
pytest
```

### Solo unit tests

```bash
pytest tests/unit/ -m unit
```

### Solo integration tests

```bash
pytest tests/integration/ -m integration
```

### Test specifico

```bash
pytest tests/unit/test_file_storage_tenant_aware.py
```

### Con coverage

```bash
pytest --cov=app --cov-report=html
# Report in htmlcov/index.html
```

### Verbose output

```bash
pytest -v -s
```

## Markers

I test sono marcati per categoria:

- `@pytest.mark.unit` - Unit tests veloci
- `@pytest.mark.integration` - Integration tests con DB
- `@pytest.mark.tenant` - Test isolamento tenant
- `@pytest.mark.parsing` - Test parsing documenti
- `@pytest.mark.security` - Test sicurezza

Esempio:

```bash
# Solo test di sicurezza
pytest -m security

# Escludere test lenti
pytest -m "not slow"
```

## Test Coverage

### Unit Tests - File Storage Tenant-Aware

- ✅ Validazione tenant schema
- ✅ Isolamento file tra tenant
- ✅ Prevenzione directory traversal
- ✅ Operazioni su file temporanei (save_temp_file, move_from_temp)
- ✅ Validazione sicurezza path
- ✅ Operazioni base (save, delete, get_size)

### Unit Tests - Document Type Registry

- ✅ Registrazione da manifest
- ✅ Lookup per full key, codice, modulo
- ✅ Indicizzazione per categoria e parsing service
- ✅ Ereditarietà tra moduli
- ✅ Gestione errori e casi edge

### Integration Tests - Document Parsing E2E

- ✅ Upload e creazione job
- ✅ Gestione callback (success, failure, retry)
- ✅ Creazione notifiche (Scadenza)
- ✅ Priorità notifica basata su confidence
- ✅ Workflow completo end-to-end
- ✅ Isolamento tenant nei job
- ✅ Filtri e query

### Integration Tests - Tenant Isolation

- ✅ Isolamento directory file per tenant
- ✅ Isolamento job DocumentJob per tenant
- ✅ Callback rispettano tenant boundaries
- ✅ Prevenzione data leakage tra tenant
- ✅ Validazione cross-tenant access

## CI/CD

I test possono essere eseguiti in CI/CD:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-test.txt
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Troubleshooting

### Import errors

Se vedi errori di import:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Database errors

I test usano SQLite in-memory. Se hai errori, verifica:

```bash
python -c "import sqlite3; print(sqlite3.version)"
```

### Fixture not found

Controlla che `conftest.py` sia nella root di `tests/`.

## Aggiungere Nuovi Test

### Unit Test

```python
# tests/unit/test_my_component.py
import pytest
from app.my_module import MyComponent

@pytest.mark.unit
def test_my_function():
    component = MyComponent()
    result = component.my_function()
    assert result == expected
```

### Integration Test

```python
# tests/integration/test_my_workflow.py
import pytest

@pytest.mark.integration
def test_workflow(db_session, test_user):
    # Test con database e user
    pass
```

## Best Practices

1. **Nomenclatura**: `test_*.py`, `Test*`, `test_*`
2. **Isolamento**: Ogni test deve essere indipendente
3. **Markers**: Usa marker appropriati
4. **Fixtures**: Riutilizza fixture da `conftest.py`
5. **Mock**: Mocka servizi esterni (MRZ, HTTP calls)
6. **Assertions**: Usa assert descrittivi
7. **Cleanup**: Le fixture gestiscono il cleanup automatico

## Metriche Target

- **Coverage**: >= 80%
- **Unit tests**: < 1s per test
- **Integration tests**: < 5s per test
- **Pass rate**: 100%
