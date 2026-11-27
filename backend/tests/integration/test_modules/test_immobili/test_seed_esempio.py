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


def _relazioni(db, codice_bene, tipo):
    return db.execute(text(
        "SELECT count(*) FROM core_relazioni r JOIN core_ruoli_disponibili t ON t.id = r.ruolo_id "
        "WHERE r.entity_type = 'IMMOBILE' AND r.entity_id = :b AND t.codice = :t AND t.modulo_id = 'immobili'"
    ), {"b": _id(db, codice_bene), "t": tipo}).scalar()


def test_dati_di_esempio_dei_beni(db_session):
    seed_tenant_data(db_session, tenant_id=0, tenant_schema=None, seed_test_data=True)
    db = db_session
    collegamenti = {tuple(r) for r in db.execute(text(
        "SELECT p.codice, c.codice, k.tipo FROM immo_beni_collegamenti k "
        "JOIN immo_beni p ON p.id = k.bene_id JOIN immo_beni c ON c.id = k.bene_collegato_id"))}
    assert ("UNITA-001", "BOX-001", "PERTINENZA") in collegamenti
    assert ("TER-002", "FAB-001", "FABBRICATO_SU_PARTICELLA") in collegamenti

    ruoli = ruoli_alla_data(db, _id(db, "TER-001"), date(2026, 6, 1))
    assert [s.ruolo for s in ruoli.titolari_godimento] == ["usufrutto"]
    assert [s.ruolo for s in ruoli.proprietari] == ["nuda_proprieta"]
    assert len(ruoli.conduttori) == 1 and ruoli.avvisi == []

    assert _relazioni(db, "UNITA-002", "conduttore") == 1
    assert _relazioni(db, "UNITA-001", "proprieta") == 2   # 1/2 + 1/2
    assert _relazioni(db, "BOX-001", "proprieta") == 1
    assert _relazioni(db, "TER-001", "nuda_proprieta") == 1 and _relazioni(db, "TER-001", "usufrutto") == 1
    quote = {tuple(r) for r in db.execute(text(
        "SELECT r.quota_numeratore, r.quota_denominatore FROM core_relazioni r "
        "JOIN core_ruoli_disponibili t ON t.id = r.ruolo_id "
        "WHERE r.entity_id = :b AND t.codice = 'proprieta'"), {"b": _id(db, "UNITA-001")})}
    assert quote == {(1, 2)}
    assert db.execute(text(
        "SELECT count(*) FROM immo_spese_ricorrenti WHERE bene_id = :b"), {"b": _id(db, "UNITA-001")}).scalar() >= 1


def test_dati_di_esempio_idempotenti(db_session):
    seed_tenant_data(db_session, tenant_id=0, tenant_schema=None, seed_test_data=True)
    conta = lambda t: db_session.execute(text(f"SELECT count(*) FROM {t}")).scalar()
    prima = (conta("immo_beni_collegamenti"), conta("core_relazioni"))
    seed_tenant_data(db_session, tenant_id=0, tenant_schema=None, seed_test_data=True)
    assert (conta("immo_beni_collegamenti"), conta("core_relazioni")) == prima


def test_dati_di_esempio_durante_l_installazione_del_modulo(db_session, monkeypatch):
    """The install hook runs before the tenant's TenantModule row of immobili is enabled:
    the example relations must still be created (the module gate stays on for the API)."""
    from app.core.platform_services import relazioni_moduli
    from tests.integration.conftest import TEST_TENANT

    # Real behaviour for a known tenant whose module is not enabled yet: empty set.
    monkeypatch.setattr(relazioni_moduli, "moduli_attivi", lambda db, schema: set() if schema else None)
    seed_tenant_data(db_session, tenant_id=0, tenant_schema=TEST_TENANT, seed_test_data=True)
    assert _relazioni(db_session, "UNITA-001", "proprieta") == 2
    assert _relazioni(db_session, "UNITA-002", "conduttore") == 1


def _complesso(db):
    return db.execute(text(
        "SELECT c.id, e.id FROM immo_raggruppamenti c JOIN immo_raggruppamenti e ON e.padre_id = c.id "
        "WHERE c.nome = 'Complesso di esempio' AND c.tipo = 'COMPLESSO' "
        "AND e.nome = 'Edificio A' AND e.tipo = 'EDIFICIO'")).all()


def test_seed_complesso_idempotente(db_session):
    db = db_session
    for _ in range(2):
        seed_tenant_data(db, tenant_id=0, tenant_schema=None, seed_test_data=True)
    ((_, edificio),) = _complesso(db)
    unita = db.execute(text("SELECT codice FROM immo_beni WHERE raggruppamento_id = :e ORDER BY codice"),
                       {"e": edificio}).scalars().all()
    assert unita == ["UNITA-001", "UNITA-002"]
    manutentori = db.execute(text(
        "SELECT count(*) FROM core_relazioni r JOIN core_ruoli_disponibili t ON t.id = r.ruolo_id "
        "WHERE r.entity_type = 'RAGGRUPPAMENTO' AND r.entity_id = :e AND t.codice = 'manutentore'"),
        {"e": edificio}).scalar()
    assert manutentori == 1
