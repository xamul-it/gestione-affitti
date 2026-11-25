"""Example data of affitti_lungo (seed_test_data=True); self-contained: only this module's seed runs."""
import pytest
from sqlalchemy import text

from affitti_lungo.seeds import seed_tenant

pytestmark = pytest.mark.integration

TABELLE = ("affittuari", "contratti", "incassi", "spese", "ripartizioni_spese", "tecnici")


def _conta(db):
    return {t: db.execute(text(f"SELECT count(*) FROM {t}")).scalar() for t in TABELLE}


def test_esempi_affitti_lungo(db_session):
    prima = _conta(db_session)
    seed_tenant(db_session, seed_test_data=True)
    dopo = _conta(db_session)
    assert all(dopo[t] > prima[t] for t in TABELLE), (prima, dopo)
    contratto = db_session.execute(text(
        "SELECT c.stato, b.codice FROM contratti c JOIN immo_beni b ON b.id = c.unita_immobiliare_id "
        "WHERE c.numero_contratto = 'CTR-ESEMPIO-001'")).one()
    assert contratto.stato == "ATTIVO" and contratto.codice == "AL-ESEMPIO-2"
    seed_tenant(db_session, seed_test_data=True)
    assert _conta(db_session) == dopo


def test_senza_seed_test_data_non_crea_nulla(db_session):
    prima = _conta(db_session)
    seed_tenant(db_session)
    assert _conta(db_session) == prima
