"""Example data of anagrafica_italiana are created once per tenant (scripts/tenant_prova.py reruns them)."""
import pytest
from sqlalchemy import text

from anagrafica_italiana.seeds.seed_tenant import seed_tenant

pytestmark = pytest.mark.integration


def test_esempi_anagrafica_idempotenti(db_session):
    seed_tenant(db_session, seed_test_data=True)
    prima = db_session.execute(text("SELECT count(*) FROM anag_soggetti_anagrafici")).scalar()
    risultato = seed_tenant(db_session, seed_test_data=True)
    assert db_session.execute(text("SELECT count(*) FROM anag_soggetti_anagrafici")).scalar() == prima
    assert risultato["test_data_seeded"] == 0
