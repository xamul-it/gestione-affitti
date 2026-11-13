"""
Migration 2026111301_terreni_beni: land parcels become beni with portions
(phase 2a of docs/superpowers/specs/2026-11-10-beni-catastali-design.md).

converti() runs inside the rolled-back test transaction, on a temporary
schema built with the old layout.
"""
import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import text

MIGRATION = (
    Path(__file__).resolve().parents[4]
    / "modules" / "immobili" / "migrations" / "2026111301_terreni_beni.py"
)

SCHEMA = "tenant_pytest_terreni"


@pytest.fixture(scope="module")
def migrazione():
    spec = importlib.util.spec_from_file_location("migrazione_terreni", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _schema_vecchio(conn):
    conn.execute(text(f"CREATE SCHEMA {SCHEMA}"))
    conn.execute(text(f"SET search_path TO {SCHEMA}, public"))
    conn.execute(text("""
        CREATE TABLE immo_beni (
            id SERIAL PRIMARY KEY,
            tipo_bene VARCHAR(10) NOT NULL CHECK (tipo_bene IN ('UNITA', 'TERRENO')),
            codice VARCHAR(50) NOT NULL UNIQUE,
            comune_codice VARCHAR(4), comune VARCHAR(100), provincia VARCHAR(2),
            indirizzo VARCHAR(255), cap VARCHAR(10), sezione VARCHAR(20),
            foglio VARCHAR(20), particella VARCHAR(20), denominatore VARCHAR(20),
            subalterno VARCHAR(20), partita VARCHAR(20), descrizione TEXT, note TEXT,
            attivo BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ
        )
    """))
    conn.execute(text("""
        CREATE TABLE immo_terreni (
            id SERIAL PRIMARY KEY,
            codice VARCHAR(50) NOT NULL UNIQUE,
            nome VARCHAR(255) NOT NULL,
            descrizione TEXT,
            tipologia_id INTEGER REFERENCES public.immo_tipologie_terreno(id) ON DELETE SET NULL,
            indirizzo VARCHAR(255), comune VARCHAR(100) NOT NULL, cap VARCHAR(10),
            provincia VARCHAR(2) NOT NULL, nazione VARCHAR(100),
            superficie FLOAT NOT NULL, unita_misura_superficie VARCHAR(10),
            sezione_catastale VARCHAR(20), foglio VARCHAR(20), particella VARCHAR(20),
            subalterno VARCHAR(20), qualita_coltura VARCHAR(100), classe_catastale VARCHAR(10),
            reddito_dominicale NUMERIC(12,2), reddito_agrario NUMERIC(12,2),
            note TEXT, attivo BOOLEAN, created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ
        )
    """))


def _colonne(conn, tabella):
    return {r[0] for r in conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = :t"
    ), {"t": tabella})}


def test_converte_terreno_vecchio_layout(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    # A unit already holds the code of the second land parcel.
    conn.execute(text("INSERT INTO immo_beni (tipo_bene, codice) VALUES ('UNITA', 'TER-2')"))
    conn.execute(text("""
        INSERT INTO immo_terreni (codice, nome, comune, provincia, superficie,
            unita_misura_superficie, sezione_catastale, foglio, particella,
            qualita_coltura, classe_catastale, reddito_dominicale, reddito_agrario, attivo)
        VALUES ('TER-1', 'Campo', 'Forlì', 'FC', 1.5, 'ha', 'A', '40', '154',
                'SEMINATIVO', '2', 10.50, 8.25, true),
               ('TER-2', 'Orto', 'Forlì', 'FC', 536, 'mq', NULL, '40', '155',
                NULL, NULL, NULL, NULL, false)
    """))

    assert migrazione.converti(conn) == 2

    beni = conn.execute(text(
        "SELECT codice, sezione, foglio, particella, attivo FROM immo_beni "
        "WHERE tipo_bene = 'TERRENO' ORDER BY codice")).all()
    assert [b.codice for b in beni] == ["TER-1", "TER-2-T"]
    assert (beni[0].sezione, beni[0].foglio, beni[0].particella, beni[0].attivo) == ("A", "40", "154", True)
    assert beni[1].attivo is False
    porzioni = conn.execute(text(
        "SELECT b.codice, p.qualita, p.classe, p.superficie_mq, p.reddito_dominicale "
        "FROM immo_terreni_porzioni p JOIN immo_beni b ON b.id = p.terreno_id ORDER BY b.codice")).all()
    assert [(p.qualita, p.superficie_mq) for p in porzioni] == [("SEMINATIVO", 15000), ("NON INDICATA", 536)]
    assert porzioni[0].classe == "2" and float(porzioni[0].reddito_dominicale) == 10.50
    terreni = conn.execute(text(
        "SELECT t.nome, t.superficie_mq FROM immo_terreni t JOIN immo_beni b ON b.id = t.id "
        "ORDER BY b.codice")).all()
    assert [(t.nome, t.superficie_mq) for t in terreni] == [("Campo", 15000), ("Orto", 536)]
    assert "comune" not in _colonne(conn, "immo_terreni")
    assert conn.execute(text("SELECT to_regclass('immo_terreni_vecchi')")).scalar() is None
    # New land parcels take their id from immo_beni, the table has no sequence of its own.
    assert conn.execute(text(
        "SELECT column_default FROM information_schema.columns WHERE table_schema = current_schema() "
        "AND table_name = 'immo_terreni' AND column_name = 'id'")).scalar() is None


def test_converti_su_layout_nuovo_non_fa_nulla(db_session, migrazione):
    assert migrazione.converti(db_session.connection()) == 0
    assert "superficie_mq" in _colonne(db_session.connection(), "immo_terreni")


def test_crea_porzioni_idempotente(db_session, migrazione):
    conn = db_session.connection()
    migrazione.crea_porzioni(conn)
    migrazione.crea_porzioni(conn)
    assert {"terreno_id", "qualita", "superficie_mq", "deduzioni"} <= _colonne(conn, "immo_terreni_porzioni")
