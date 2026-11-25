"""Example data of gestione_pec (seed_test_data=True): an inactive mailbox, never polled."""
import pytest
from sqlalchemy import text

from gestione_pec.seeds import seed_tenant
from gestione_pec.services.crypto_service import decrypt_credential

pytestmark = pytest.mark.integration

TABELLE = ("pec_caselle", "pec_messaggi", "pec_utenti_abilitati", "pec_audit_accessi",
           "pec_audit_risposte", "pec_notifiche_log")


def _conta(db):
    return {t: db.execute(text(f"SELECT count(*) FROM {t}")).scalar() for t in TABELLE}


def test_esempi_pec(db_session):
    prima = _conta(db_session)
    seed_tenant(db_session, seed_test_data=True)
    dopo = _conta(db_session)
    assert all(dopo[t] > prima[t] for t in TABELLE), (prima, dopo)
    casella = db_session.execute(text(
        "SELECT is_attiva, username_enc, imap_host FROM pec_caselle WHERE indirizzo_pec = 'esempio@pec.esempio.invalid'")).one()
    assert casella.is_attiva is False and casella.imap_host.endswith(".invalid")
    assert decrypt_credential(casella.username_enc) == "esempio@pec.esempio.invalid"
    seed_tenant(db_session, seed_test_data=True)
    assert _conta(db_session) == dopo


def test_senza_esempi(db_session):
    prima = _conta(db_session)
    seed_tenant(db_session)
    assert _conta(db_session) == prima
