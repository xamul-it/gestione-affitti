"""
Migration 2026111201_beni: data reset + immo_beni structure (phase 1 of
docs/superpowers/specs/2026-11-10-beni-catastali-design.md).

Structure checks run on tenant_qa_test after the migration was applied;
azzera() runs inside the rolled-back test transaction.
"""
import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import text

MIGRATION = (
    Path(__file__).resolve().parents[4]
    / "modules" / "immobili" / "migrations" / "2026111201_beni.py"
)


@pytest.fixture(scope="module")
def migrazione():
    spec = importlib.util.spec_from_file_location("migrazione_beni", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _colonne(db, tabella):
    return {
        r[0] for r in db.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = :t"
        ), {"t": tabella})
    }


def _conta(db, sql, **params):
    return db.execute(text(sql), params).scalar()


def test_struttura_beni(db_session):
    assert "tipo_bene" in _colonne(db_session, "immo_beni")
    unita = _colonne(db_session, "immo_unita_immobiliari")
    assert not unita & {"indirizzo", "citta", "codice", "created_at"}
    for tabella in (
        "immo_diritti_immobile", "immo_assegnazioni_conduttore",
        "immo_variazioni_catastali", "immo_spese_ricorrenti",
    ):
        colonne = _colonne(db_session, tabella)
        assert "bene_id" in colonne, tabella
        assert "unita_immobiliare_id" not in colonne, tabella
    fk = db_session.execute(text(
        "SELECT confrelid::regclass::text FROM pg_constraint "
        "WHERE conrelid = 'immo_unita_immobiliari'::regclass AND contype = 'f' "
        "AND conkey = ARRAY[(SELECT attnum FROM pg_attribute "
        "  WHERE attrelid = 'immo_unita_immobiliari'::regclass AND attname = 'id')]::smallint[]"
    )).scalar()
    assert fk is not None and fk.endswith("immo_beni")


def test_azzera_svuota_beni_e_lascia_anagrafica(db_session, migrazione):
    soggetto_id = _conta(db_session,
        "INSERT INTO anag_soggetti_anagrafici (tipo_soggetto, nome, cognome) "
        "VALUES ('PERSONA_FISICA', 'Test', 'Azzeramento') RETURNING id")
    bene_id = _conta(db_session,
        "INSERT INTO immo_beni (tipo_bene, codice, indirizzo, comune) "
        "VALUES ('UNITA', 'AZZ-1', 'Via A 1', 'Forlì') RETURNING id")
    db_session.execute(text(
        "INSERT INTO immo_unita_immobiliari (id, tipo) VALUES (:id, 'Appartamento')"), {"id": bene_id})
    proprietario_id = _conta(db_session,
        "INSERT INTO immo_proprietari (soggetto_id) VALUES (:s) RETURNING id", s=soggetto_id)
    db_session.execute(text(
        "INSERT INTO immo_diritti_immobile (bene_id, proprietario_id, tipo_diritto) "
        "VALUES (:b, :p, 'PROPRIETARIO')"), {"b": bene_id, "p": proprietario_id})
    for entity_type, entity_id in (("IMMOBILE", bene_id), ("SOGGETTO_ANAGRAFICO", soggetto_id)):
        db_session.execute(text(
            "INSERT INTO core_documenti (entity_type, entity_id, tipo_documento) "
            "VALUES (:t, :i, 'ALTRO')"), {"t": entity_type, "i": entity_id})

    risultato = migrazione.azzera(db_session.connection())

    assert risultato["immo_unita_immobiliari"] >= 1
    assert _conta(db_session, "SELECT count(*) FROM immo_unita_immobiliari") == 0
    assert _conta(db_session, "SELECT count(*) FROM immo_diritti_immobile") == 0
    assert _conta(db_session,
        "SELECT count(*) FROM core_documenti WHERE entity_type = 'IMMOBILE'") == 0
    assert _conta(db_session,
        "SELECT count(*) FROM anag_soggetti_anagrafici WHERE id = :s", s=soggetto_id) == 1
    assert _conta(db_session,
        "SELECT count(*) FROM core_documenti WHERE entity_type = 'SOGGETTO_ANAGRAFICO' "
        "AND entity_id = :s", s=soggetto_id) == 1


def test_azzera_salta_tabelle_assenti(db_session, migrazione):
    db_session.execute(text("DROP TABLE ab_ospiti_soggiorni"))
    risultato = migrazione.azzera(db_session.connection())
    assert "ab_ospiti_soggiorni" not in risultato
    assert "immo_unita_immobiliari" in risultato
