"""
Test unitari per ComplianceScheduler — verificano solo che lo start/stop
non blocchi e non sollevi eccezioni (l'esecuzione multi-tenant reale è
testata in test_compliance_scadenze_service.py). Nessuna chiamata di rete/DB
reale qui: get_active_tenant_schemas è mockata.

Shadows conftest.py's autouse `override_get_db(db_session)` — see
test_notifica_model.py for why db_session/SQLite is broken here (Tenant
declares __table_args__ = {'schema': 'public'}, and conftest.py's fixture
chain unconditionally registers Tenant on Base.metadata for every test
session, which SQLite's create_all() cannot handle). Without this shadow
both tests below ERROR at setup even though they never touch the DB.
"""
from unittest.mock import patch

import pytest

from affitti_brevi.services.compliance_scheduler import ComplianceScheduler


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only."""
    yield


def test_start_non_blocca_e_marca_is_running():
    scheduler = ComplianceScheduler(interval_hours=1)
    with patch("affitti_brevi.services.compliance_scheduler.get_active_tenant_schemas", return_value=[]):
        scheduler.start()
        try:
            assert scheduler.is_running is True
        finally:
            scheduler.stop()
    assert scheduler.is_running is False


def test_start_due_volte_non_solleva():
    scheduler = ComplianceScheduler(interval_hours=1)
    with patch("affitti_brevi.services.compliance_scheduler.get_active_tenant_schemas", return_value=[]):
        scheduler.start()
        try:
            scheduler.start()  # no-op, solo un warning loggato
            assert scheduler.is_running is True
        finally:
            scheduler.stop()
