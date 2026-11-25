"""
Migration 2026112501_relazione_unica: rights and tenancies of beni move into
core_relazioni (phase 3). converti() runs inside the rolled-back test
transaction, on a temporary schema with the old layout.
"""
import importlib.util
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path

import pytest
from sqlalchemy import text

MIGRATION = (
    Path(__file__).resolve().parents[4]
    / "modules" / "immobili" / "migrations" / "2026112501_relazione_unica.py"
)
SCHEMA = "tenant_pytest_relazioni"


@pytest.fixture(scope="module")
def migrazione():
    spec = importlib.util.spec_from_file_location("migrazione_relazione_unica", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _schema_nuovo(conn):
    conn.execute(text(f"CREATE SCHEMA {SCHEMA}"))
    conn.execute(text(f"SET search_path TO {SCHEMA}, public"))
    conn.execute(text("""
        CREATE TABLE core_relazioni (
            id SERIAL PRIMARY KEY, soggetto_id INTEGER NOT NULL,
            ruolo_id INTEGER NOT NULL REFERENCES public.core_ruoli_disponibili(id),
            entity_type VARCHAR(50), entity_id INTEGER, sottotipo VARCHAR(100),
            data_inizio DATE, data_fine DATE, data_scadenza DATE, scadenza_id INTEGER,
            note TEXT, dati JSON, quota_numeratore INTEGER, quota_denominatore INTEGER,
            creato_da INTEGER, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE TABLE core_documenti (id SERIAL PRIMARY KEY, entity_type VARCHAR(50), entity_id INTEGER)"))


def _schema_vecchio(conn):
    _schema_nuovo(conn)
    conn.execute(text("CREATE TABLE immo_beni (id SERIAL PRIMARY KEY)"))
    conn.execute(text("INSERT INTO immo_beni DEFAULT VALUES"))
    conn.execute(text("INSERT INTO immo_beni DEFAULT VALUES"))
    conn.execute(text("""
        CREATE TABLE immo_proprietari (
            id SERIAL PRIMARY KEY, soggetto_id INTEGER NOT NULL, note_proprietario VARCHAR(500))
    """))
    conn.execute(text("""
        CREATE TABLE immo_conduttori (
            id SERIAL PRIMARY KEY, soggetto_id INTEGER NOT NULL, note VARCHAR(500))
    """))
    conn.execute(text("""
        CREATE TABLE immo_diritti_immobile (
            id SERIAL PRIMARY KEY, bene_id INTEGER NOT NULL REFERENCES immo_beni(id),
            proprietario_id INTEGER NOT NULL REFERENCES immo_proprietari(id),
            tipo_diritto VARCHAR(30) NOT NULL, quota_percentuale NUMERIC(5,2),
            data_inizio VARCHAR(10), data_fine VARCHAR(10), note VARCHAR(500),
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    conn.execute(text("""
        CREATE TABLE immo_assegnazioni_conduttore (
            id SERIAL PRIMARY KEY, bene_id INTEGER NOT NULL REFERENCES immo_beni(id),
            conduttore_id INTEGER NOT NULL REFERENCES immo_conduttori(id),
            data_inizio DATE, data_fine DATE, note VARCHAR(500),
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """))


def _beni(conn):
    return [r[0] for r in conn.execute(text("SELECT id FROM immo_beni ORDER BY id"))]


def _prop(conn, soggetto, note=None):
    return conn.execute(text(
        "INSERT INTO immo_proprietari (soggetto_id, note_proprietario) VALUES (:s, :n) RETURNING id"),
        {"s": soggetto, "n": note}).scalar()


def _diritto(conn, bene, prop, tipo, quota=None, inizio=None, fine=None, note=None):
    return conn.execute(text(
        "INSERT INTO immo_diritti_immobile (bene_id, proprietario_id, tipo_diritto, quota_percentuale, "
        "data_inizio, data_fine, note) VALUES (:b, :p, :t, :q, :i, :f, :n) RETURNING id"),
        {"b": bene, "p": prop, "t": tipo, "q": quota, "i": inizio, "f": fine, "n": note}).scalar()


def _relazioni(conn):
    return conn.execute(text(
        "SELECT r.*, t.codice FROM core_relazioni r JOIN public.core_ruoli_disponibili t ON t.id = r.ruolo_id "
        "ORDER BY r.id")).all()


def test_diritti_diventano_relazioni(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    b1, _ = _beni(conn)
    p1, p2 = _prop(conn, 101), _prop(conn, 102)
    _diritto(conn, b1, p1, "PROPRIETARIO", 50, "2020-01-01", None, "prima")
    _diritto(conn, b1, p2, "COMPROPRIETARIO", 50, "2020-01-01")
    _diritto(conn, b1, p1, "USUFRUTTUARIO", 100, "2021-05-01", "2030-05-01")
    assert migrazione.converti(conn) == {
        "diritti": 3, "assegnazioni": 0, "documenti_proprietario": 0,
        "proprietari_senza_diritti": 0, "conduttori_senza_assegnazioni": 0}
    rel = _relazioni(conn)
    assert [(r.codice, r.soggetto_id, r.entity_type, r.entity_id) for r in rel] == [
        ("proprieta", 101, "IMMOBILE", b1), ("proprieta", 102, "IMMOBILE", b1),
        ("usufrutto", 101, "IMMOBILE", b1)]
    assert [(r.quota_numeratore, r.quota_denominatore) for r in rel] == [(1, 2), (1, 2), (1, 1)]
    assert rel[0].data_inizio == date(2020, 1, 1) and rel[0].data_fine is None and rel[0].note == "prima"
    assert rel[2].data_fine == date(2030, 5, 1)


@pytest.mark.parametrize("percentuale,atteso", [
    (50.00, (1, 2)), (33.33, (1, 3)), (66.67, (2, 3)), (100, (1, 1)), (12.5, (1, 8)),
    (37.21, (3721, 10000)),
])
def test_quota_percentuale_in_frazione(migrazione, percentuale, atteso):
    num, den, _ = migrazione.quota_in_frazione(percentuale)
    assert (num, den) == atteso
    assert Fraction(num, den) == Fraction(*atteso)


def test_quota_da_ricontrollare_nel_log(db_session, migrazione, capsys):
    conn = db_session.connection()
    _schema_vecchio(conn)
    b1, _ = _beni(conn)
    _diritto(conn, b1, _prop(conn, 101), "PROPRIETARIO", 37.21, "2020-01-01")
    migrazione.converti(conn)
    assert "quota da ricontrollare" in capsys.readouterr().out
    r = _relazioni(conn)[0]
    assert (r.quota_numeratore, r.quota_denominatore) == (3721, 10000)


def test_assegnazioni_diventano_conduttore(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    b1, b2 = _beni(conn)
    c = conn.execute(text("INSERT INTO immo_conduttori (soggetto_id) VALUES (201) RETURNING id")).scalar()
    conn.execute(text(
        "INSERT INTO immo_assegnazioni_conduttore (bene_id, conduttore_id, data_inizio, data_fine, note) "
        "VALUES (:b1, :c, '2022-01-01', '2023-01-01', 'vecchia'), (:b2, :c, '2023-02-01', NULL, NULL)"),
        {"b1": b1, "b2": b2, "c": c})
    out = migrazione.converti(conn)
    assert out["assegnazioni"] == 2 and out["conduttori_senza_assegnazioni"] == 0
    rel = _relazioni(conn)
    assert [(r.codice, r.soggetto_id, r.entity_id) for r in rel] == [
        ("conduttore", 201, b1), ("conduttore", 201, b2)]
    assert rel[0].data_inizio == date(2022, 1, 1) and rel[0].data_fine == date(2023, 1, 1)
    assert rel[0].note == "vecchia" and rel[1].data_fine is None
    assert rel[0].quota_numeratore is None


def test_note_ruolo_in_dati(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    b1, b2 = _beni(conn)
    p = _prop(conn, 101, "usa il garage")
    _diritto(conn, b1, p, "PROPRIETARIO", 100, "2020-01-01")
    _diritto(conn, b2, p, "PROPRIETARIO", 100, "2020-01-01")
    _diritto(conn, b2, _prop(conn, 102), "USO", None, "2020-01-01")
    migrazione.converti(conn)
    rel = _relazioni(conn)
    assert [r.dati for r in rel] == [{"note_ruolo": "usa il garage"}] * 2 + [None]


def test_documenti_proprietario_al_soggetto(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    p = _prop(conn, 777)
    conn.execute(text(
        "INSERT INTO core_documenti (entity_type, entity_id) VALUES ('PROPRIETARIO', :p), ('IMMOBILE', :p)"),
        {"p": p})
    assert migrazione.converti(conn)["documenti_proprietario"] == 1
    assert conn.execute(text("SELECT entity_type, entity_id FROM core_documenti ORDER BY id")).all() == [
        ("SOGGETTO_ANAGRAFICO", 777), ("IMMOBILE", p)]


def test_doppione_ferma(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    b1, _ = _beni(conn)
    p = _prop(conn, 101)
    _diritto(conn, b1, p, "PROPRIETARIO", 50, "2020-01-01")
    _diritto(conn, b1, p, "COMPROPRIETARIO", 50, "2020-01-01")
    with pytest.raises(RuntimeError) as e:
        migrazione.converti(conn)
    assert f"bene {b1}" in str(e.value) and "soggetto 101" in str(e.value)
    assert conn.execute(text("SELECT count(*) FROM core_relazioni")).scalar() == 0


def test_doppione_con_fine_futura_ferma(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    b1, _ = _beni(conn)
    p = _prop(conn, 101)
    futura = (date.today() + timedelta(days=365)).isoformat()
    passata = (date.today() - timedelta(days=30)).isoformat()
    _diritto(conn, b1, p, "PROPRIETARIO", 50, "2010-01-01", futura)
    _diritto(conn, b1, p, "COMPROPRIETARIO", 50, "2010-01-01")
    with pytest.raises(RuntimeError):
        migrazione.converti(conn)
    assert conn.execute(text("SELECT count(*) FROM core_relazioni")).scalar() == 0
    conn.execute(text("UPDATE immo_diritti_immobile SET data_fine = :f WHERE tipo_diritto = 'PROPRIETARIO'"),
                 {"f": passata})
    assert migrazione.converti(conn)["diritti"] == 2


def test_data_malformata_ferma(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    b1, _ = _beni(conn)
    d = _diritto(conn, b1, _prop(conn, 101), "PROPRIETARIO", 100, "01/02/2020")
    with pytest.raises(RuntimeError) as e:
        migrazione.converti(conn)
    assert f"Diritto {d}" in str(e.value)
    assert conn.execute(text("SELECT count(*) FROM core_relazioni")).scalar() == 0


def test_conteggi_ruoli_senza_bene(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    b1, _ = _beni(conn)
    _diritto(conn, b1, _prop(conn, 101), "PROPRIETARIO", 100, "2020-01-01")
    _prop(conn, 102)
    conn.execute(text("INSERT INTO immo_conduttori (soggetto_id) VALUES (201), (202)"))
    out = migrazione.converti(conn)
    assert out["proprietari_senza_diritti"] == 1 and out["conduttori_senza_assegnazioni"] == 2
    assert conn.execute(text("SELECT count(*) FROM core_relazioni")).scalar() == 1


def test_idempotente_su_schema_nuovo(db_session, migrazione):
    conn = db_session.connection()
    _schema_nuovo(conn)
    assert migrazione.converti(conn) == {
        "diritti": 0, "assegnazioni": 0, "documenti_proprietario": 0,
        "proprietari_senza_diritti": 0, "conduttori_senza_assegnazioni": 0}


def test_tabelle_vecchie_vuote_conteggi_zero(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    assert migrazione.converti(conn)["diritti"] == 0


def test_doppione_conduttore_ferma(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    b1, _ = _beni(conn)
    c1 = conn.execute(text("INSERT INTO immo_conduttori (soggetto_id) VALUES (201) RETURNING id")).scalar()
    c2 = conn.execute(text("INSERT INTO immo_conduttori (soggetto_id) VALUES (201) RETURNING id")).scalar()
    conn.execute(text(
        "INSERT INTO immo_assegnazioni_conduttore (bene_id, conduttore_id, data_inizio) "
        "VALUES (:b, :c1, '2022-01-01'), (:b, :c2, '2023-01-01')"), {"b": b1, "c1": c1, "c2": c2})
    with pytest.raises(RuntimeError) as e:
        migrazione.converti(conn)
    assert f"bene {b1}" in str(e.value) and "soggetto 201" in str(e.value)
    assert conn.execute(text("SELECT count(*) FROM core_relazioni")).scalar() == 0


def test_date_invertite_ferma(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    b1, _ = _beni(conn)
    d = _diritto(conn, b1, _prop(conn, 101), "PROPRIETARIO", 100, "2020-01-01", "2019-01-01")
    with pytest.raises(RuntimeError) as e:
        migrazione.converti(conn)
    assert f"Diritto {d}" in str(e.value)
    assert conn.execute(text("SELECT count(*) FROM core_relazioni")).scalar() == 0
    assert conn.execute(text("SELECT count(*) FROM immo_diritti_immobile")).scalar() == 1
    conn.execute(text("DELETE FROM immo_diritti_immobile"))
    c = conn.execute(text("INSERT INTO immo_conduttori (soggetto_id) VALUES (201) RETURNING id")).scalar()
    a = conn.execute(text(
        "INSERT INTO immo_assegnazioni_conduttore (bene_id, conduttore_id, data_inizio, data_fine) "
        "VALUES (:b, :c, '2022-01-01', '2021-01-01') RETURNING id"), {"b": b1, "c": c}).scalar()
    with pytest.raises(RuntimeError) as e:
        migrazione.converti(conn)
    assert str(a) in str(e.value)
    assert conn.execute(text("SELECT count(*) FROM core_relazioni")).scalar() == 0
    assert conn.execute(text("SELECT count(*) FROM immo_assegnazioni_conduttore")).scalar() == 1


def test_doppione_conduttore_chiuso_migra(db_session, migrazione):
    conn = db_session.connection()
    _schema_vecchio(conn)
    b1, _ = _beni(conn)
    c = conn.execute(text("INSERT INTO immo_conduttori (soggetto_id) VALUES (201) RETURNING id")).scalar()
    conn.execute(text(
        "INSERT INTO immo_assegnazioni_conduttore (bene_id, conduttore_id, data_inizio, data_fine) "
        "VALUES (:b, :c, '2020-01-01', '2021-01-01'), (:b, :c, '2021-06-01', '2022-01-01')"),
        {"b": b1, "c": c})
    assert migrazione.converti(conn)["assegnazioni"] == 2
