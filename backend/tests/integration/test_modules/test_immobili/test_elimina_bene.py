"""
Deleting a bene (unit or land parcel) takes its documents, open scadenze and
core relations with it: entity_type IMMOBILE rows have no FK. Files stay in
storage, as in the phase 1 reset.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from app.core.platform_services.scadenze_collegate import apri_o_aggiorna, utente_sistema
from immobili.models import Terreno, TerrenoPorzione, UnitaImmobiliare
from immobili.routes.immobili import delete_unita_immobiliare
from immobili.routes.terreni import delete_terreno
from immobili.services.relazioni_bene import crea_relazione_bene
from tests.integration.conftest import TEST_TENANT

pytestmark = pytest.mark.integration

UTENTE = SimpleNamespace(id=None, is_superuser=True, get_permissions=lambda: set())


def _collega_dati_core(db, bene_id):
    db.execute(text(
        "INSERT INTO core_documenti (entity_type, entity_id, tipo_documento) VALUES ('IMMOBILE', :id, 'ALTRO')"
    ), {"id": bene_id})
    return apri_o_aggiorna(
        db, scadenza_id=None, modulo="immobili", entity_type="IMMOBILE", entity_id=bene_id,
        titolo="CDU in scadenza", descrizione="prova", data=date.today() + timedelta(days=30),
        user_id=utente_sistema(db), nota_creazione="prova",
    )


def _verifica_ripulito(db, bene_id, scadenza_id):
    assert db.execute(text(
        "SELECT count(*) FROM core_documenti WHERE entity_type = 'IMMOBILE' AND entity_id = :id"
    ), {"id": bene_id}).scalar() == 0
    stato = db.execute(text("SELECT stato FROM core_scadenze WHERE id = :id"), {"id": scadenza_id}).scalar()
    assert stato in ("CANCELLATA", "cancellata")


def test_cancellare_terreno_toglie_documenti_e_scadenze(db_session):
    t = Terreno(codice="DEL-T-1", comune="Forlì", provincia="FC",
                porzioni=[TerrenoPorzione(qualita="SEMINATIVO", superficie_mq=10)])
    db_session.add(t)
    db_session.flush()
    scadenza_id = _collega_dati_core(db_session, t.id)

    delete_terreno(t.id, db=db_session, current_user=UTENTE)

    _verifica_ripulito(db_session, t.id, scadenza_id)


def test_cancellare_unita_toglie_documenti_e_scadenze(db_session):
    u = UnitaImmobiliare(codice="DEL-U-1", tipo="Box", indirizzo="Via A 1", citta="Forlì")
    db_session.add(u)
    db_session.flush()
    scadenza_id = _collega_dati_core(db_session, u.id)

    delete_unita_immobiliare(u.id, db=db_session, current_user=UTENTE)

    _verifica_ripulito(db_session, u.id, scadenza_id)


def _soggetto(db, cognome):
    from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto
    s = SoggettoAnagrafico(tipo_soggetto=TipoSoggetto.PERSONA_FISICA, nome="Del", cognome=cognome)
    db.add(s)
    db.flush()
    return s


def _conta_relazioni(db, bene_id):
    return db.execute(text(
        "SELECT count(*) FROM core_relazioni WHERE entity_type = 'IMMOBILE' AND entity_id = :id"
    ), {"id": bene_id}).scalar()


def test_cancellare_unita_toglie_le_sue_relazioni(db_session):
    u = UnitaImmobiliare(codice="DEL-U-2", tipo="Box", indirizzo="Via A 2", citta="Forlì")
    db_session.add(u)
    db_session.flush()
    crea_relazione_bene(db_session, TEST_TENANT, None, u.id, _soggetto(db_session, "Titolare").id,
                        "proprieta", quota="1/1")
    crea_relazione_bene(db_session, TEST_TENANT, None, u.id, _soggetto(db_session, "Inquilino").id,
                        "conduttore", data_inizio=date(2025, 1, 1))
    assert _conta_relazioni(db_session, u.id) == 2

    delete_unita_immobiliare(u.id, db=db_session, current_user=UTENTE)

    assert _conta_relazioni(db_session, u.id) == 0


def test_cancellare_terreno_toglie_le_sue_relazioni(db_session):
    t = Terreno(codice="DEL-T-2", comune="Forlì", provincia="FC",
                porzioni=[TerrenoPorzione(qualita="SEMINATIVO", superficie_mq=10)])
    db_session.add(t)
    db_session.flush()
    crea_relazione_bene(db_session, TEST_TENANT, None, t.id, _soggetto(db_session, "Nudo").id,
                        "nuda_proprieta", quota="1/1")
    assert _conta_relazioni(db_session, t.id) == 1

    delete_terreno(t.id, db=db_session, current_user=UTENTE)

    assert _conta_relazioni(db_session, t.id) == 0
