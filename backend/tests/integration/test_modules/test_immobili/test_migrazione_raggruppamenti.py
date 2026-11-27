"""
Migration 2026112502_raggruppamenti (phase 4a): the raggruppamenti table, the
bene column and the conversion of PARTE_DI_FONDO links into FONDO rami.
Everything runs inside the rolled-back test transaction, on a temporary schema.
"""
import importlib.util
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import text

MIGRATION = (
    Path(__file__).resolve().parents[4]
    / "modules" / "immobili" / "migrations" / "2026112502_raggruppamenti.py"
)
SCHEMA = "tenant_pytest_raggruppamenti"


@pytest.fixture(scope="module")
def migrazione():
    spec = importlib.util.spec_from_file_location("migrazione_raggruppamenti", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _schema(conn):
    conn.execute(text(f"CREATE SCHEMA {SCHEMA}"))
    conn.execute(text(f"SET search_path TO {SCHEMA}, public"))
    conn.execute(text("CREATE TABLE immo_beni (id SERIAL PRIMARY KEY, codice VARCHAR(50) NOT NULL)"))
    conn.execute(text("""
        CREATE TABLE immo_beni_collegamenti (
            id SERIAL PRIMARY KEY,
            bene_id INTEGER NOT NULL REFERENCES immo_beni(id) ON DELETE CASCADE,
            bene_collegato_id INTEGER NOT NULL REFERENCES immo_beni(id) ON DELETE CASCADE,
            tipo VARCHAR(30) NOT NULL, data_inizio DATE, data_fine DATE, note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ)
    """))


def _bene(conn, codice):
    return conn.execute(text("INSERT INTO immo_beni (codice) VALUES (:c) RETURNING id"), {"c": codice}).scalar()


def _collega(conn, principale, collegato, tipo="PARTE_DI_FONDO", fine=None):
    return conn.execute(text(
        "INSERT INTO immo_beni_collegamenti (bene_id, bene_collegato_id, tipo, data_fine) "
        "VALUES (:p, :c, :t, :f) RETURNING id"), {"p": principale, "c": collegato, "t": tipo, "f": fine}).scalar()


def _colonne(conn, tabella):
    return {r[0] for r in conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = :t"), {"t": tabella})}


def test_schema_creato(db_session, migrazione):
    conn = db_session.connection()
    _schema(conn)
    migrazione.crea_schema(conn)
    assert {"id", "tipo", "nome", "padre_id", "descrizione", "note", "attivo",
            "created_at", "updated_at"} <= _colonne(conn, "immo_raggruppamenti")
    assert "raggruppamento_id" in _colonne(conn, "immo_beni")
    vincoli = {r[0] for r in conn.execute(text(
        "SELECT conname FROM pg_constraint WHERE connamespace = CAST(:s AS regnamespace)"), {"s": SCHEMA})}
    assert "immo_raggruppamenti_non_se_stesso" in vincoli
    assert "immo_beni_raggruppamento_id_fkey" in vincoli
    with pytest.raises(Exception):
        with conn.begin_nested():
            conn.execute(text(
                "INSERT INTO immo_raggruppamenti (id, tipo, nome, padre_id) VALUES (999, 'ALTRO', 'x', 999)"))


def test_crea_schema_idempotente(db_session, migrazione):
    conn = db_session.connection()
    _schema(conn)
    migrazione.crea_schema(conn)
    migrazione.crea_schema(conn)
    assert "raggruppamento_id" in _colonne(conn, "immo_beni")


def _rami(conn):
    return conn.execute(text("SELECT id, tipo, nome FROM immo_raggruppamenti ORDER BY id")).all()


def _ramo_di(conn, bene):
    return conn.execute(text("SELECT raggruppamento_id FROM immo_beni WHERE id = :b"), {"b": bene}).scalar()


def test_fondo_da_parte_di_fondo(db_session, migrazione):
    conn = db_session.connection()
    _schema(conn)
    t1, t2, t3, u, box = (_bene(conn, c) for c in ("T1", "T2", "T3", "U", "BOX"))
    for c in (t2, t3):
        _collega(conn, t1, c)
    _collega(conn, u, box, "PERTINENZA")
    _collega(conn, t1, u, "FABBRICATO_SU_PARTICELLA")
    migrazione.crea_schema(conn)
    assert migrazione.converti(conn) == {"fondi_creati": 1, "terreni_spostati": 3, "collegamenti_rimossi": 2}
    ((ramo, tipo, nome),) = _rami(conn)
    assert (tipo, nome) == ("FONDO", "T1")
    assert [_ramo_di(conn, b) for b in (t1, t2, t3, u)] == [ramo, ramo, ramo, None]
    rimasti = {r[0] for r in conn.execute(text("SELECT tipo FROM immo_beni_collegamenti"))}
    assert rimasti == {"PERTINENZA", "FABBRICATO_SU_PARTICELLA"}


def test_ferma_se_chiusi(db_session, migrazione):
    conn = db_session.connection()
    _schema(conn)
    t1, t2 = _bene(conn, "T1"), _bene(conn, "T2")
    cid = _collega(conn, t1, t2, fine=date(2024, 1, 1))
    migrazione.crea_schema(conn)
    with pytest.raises(RuntimeError, match=str(cid)):
        migrazione.converti(conn)
    assert _rami(conn) == []


def test_ferma_particella_in_due_fondi(db_session, migrazione):
    conn = db_session.connection()
    _schema(conn)
    t1, t2, t3 = _bene(conn, "T1"), _bene(conn, "T2"), _bene(conn, "TX")
    _collega(conn, t1, t3)
    _collega(conn, t2, t3)
    migrazione.crea_schema(conn)
    with pytest.raises(RuntimeError, match="TX"):
        migrazione.converti(conn)
    assert _rami(conn) == []


def test_ferma_principale_anche_collegato(db_session, migrazione):
    conn = db_session.connection()
    _schema(conn)
    t1, t2, t3 = _bene(conn, "T1"), _bene(conn, "T2"), _bene(conn, "T3")
    _collega(conn, t1, t2)
    _collega(conn, t2, t3)
    migrazione.crea_schema(conn)
    with pytest.raises(RuntimeError, match="T2"):
        migrazione.converti(conn)
    assert _rami(conn) == []


def test_converti_senza_dati(db_session, migrazione):
    conn = db_session.connection()
    _schema(conn)
    migrazione.crea_schema(conn)
    assert migrazione.converti(conn) == {"fondi_creati": 0, "terreni_spostati": 0, "collegamenti_rimossi": 0}
