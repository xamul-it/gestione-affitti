"""Example data of affitti_brevi (seed_test_data=True), on top of the immobili ones."""
import pytest
from sqlalchemy import text

from affitti_brevi import install
from anagrafica_italiana.seeds.seed_tenant import seed_tenant as seed_anagrafica
from immobili.seeds.seed_tenant import seed_tenant_data as seed_immobili

pytestmark = pytest.mark.integration

TABELLE = (
    "ab_calendari_canali", "ab_prenotazioni", "ab_soggiorni", "ab_ospiti_soggiorni",
    "ab_tasse_soggiorno_config", "ab_tasse_soggiorno_scaglioni", "ab_tasse_soggiorni",
    "ab_comunicazioni", "ab_blocchi_calendario",
)


def _conta(db):
    return {t: db.execute(text(f"SELECT count(*) FROM {t}")).scalar() for t in TABELLE}


def test_esempi_affitti_brevi(db_session):
    seed_anagrafica(db_session, seed_test_data=True)
    seed_immobili(db_session, tenant_id=0, tenant_schema=None, seed_test_data=True)
    prima = _conta(db_session)
    install(db_session, seed_test_data=True)
    dopo = _conta(db_session)
    assert all(dopo[t] > prima[t] for t in TABELLE), (prima, dopo)
    # No real channel sync for example calendars.
    assert db_session.execute(text(
        "SELECT count(*) FROM ab_calendari_canali WHERE codice_esterno = 'ESEMPIO' AND sync_attiva")).scalar() == 0
    install(db_session, seed_test_data=True)
    assert _conta(db_session) == dopo


def test_install_senza_esempi(db_session):
    prima = _conta(db_session)
    install(db_session)
    assert _conta(db_session) == prima
