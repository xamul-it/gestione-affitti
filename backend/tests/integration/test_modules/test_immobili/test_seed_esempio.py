"""
Example data of immobili (seed_test_data=True) cover the beni features, so
the test tenants (scripts/tenant_prova.py) have rows in every table that
matters for migrations.
"""
from datetime import date

import pytest
from sqlalchemy import text

from immobili.seeds.seed_tenant import seed_tenant_data
from immobili.services.ruoli_bene import ruoli_alla_data

pytestmark = pytest.mark.integration


def _id(db, codice):
    return db.execute(text("SELECT id FROM immo_beni WHERE codice = :c"), {"c": codice}).scalar()


def test_dati_di_esempio_dei_beni(db_session):
    seed_tenant_data(db_session, tenant_id=0, tenant_schema=None, seed_test_data=True)
    db = db_session
    collegamenti = {tuple(r) for r in db.execute(text(
        "SELECT p.codice, c.codice, k.tipo FROM immo_beni_collegamenti k "
        "JOIN immo_beni p ON p.id = k.bene_id JOIN immo_beni c ON c.id = k.bene_collegato_id"))}
    assert ("UNITA-001", "BOX-001", "PERTINENZA") in collegamenti
    assert ("TER-002", "FAB-001", "FABBRICATO_SU_PARTICELLA") in collegamenti

    ruoli = ruoli_alla_data(db, _id(db, "TER-001"), date(2026, 6, 1))
    assert [s.ruolo for s in ruoli.titolari_godimento] == ["USUFRUTTUARIO"]
    assert [s.ruolo for s in ruoli.proprietari] == ["NUDA_PROPRIETA"]
    assert len(ruoli.conduttori) == 1 and ruoli.avvisi == []

    assert db.execute(text(
        "SELECT count(*) FROM immo_assegnazioni_conduttore WHERE bene_id = :b"), {"b": _id(db, "UNITA-002")}).scalar() == 1
    assert db.execute(text(
        "SELECT count(*) FROM immo_spese_ricorrenti WHERE bene_id = :b"), {"b": _id(db, "UNITA-001")}).scalar() >= 1


def test_dati_di_esempio_idempotenti(db_session):
    seed_tenant_data(db_session, tenant_id=0, tenant_schema=None, seed_test_data=True)
    prima = db_session.execute(text("SELECT count(*) FROM immo_beni_collegamenti")).scalar()
    seed_tenant_data(db_session, tenant_id=0, tenant_schema=None, seed_test_data=True)
    assert db_session.execute(text("SELECT count(*) FROM immo_beni_collegamenti")).scalar() == prima
