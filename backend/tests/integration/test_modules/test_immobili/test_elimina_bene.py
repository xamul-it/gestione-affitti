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
