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


CATENA_TENANT = (
    "2025022002_tenant_tables",
    "2026092301_conduttori_spese",
    "2026110901_variazioni_catastali",
    "2026110902_ape_migrato",
    "2026111201_beni",
)


def _carica(nome):
    path = MIGRATION.parent / f"{nome}.py"
    spec = importlib.util.spec_from_file_location(f"migr_{nome}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Op:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql):
        return self.conn.execute(sql)

    def get_bind(self):
        return self.conn


class _Context:
    def __init__(self, schema):
        self.schema = schema

    def get_x_argument(self, as_dictionary=True):
        return {"schema": self.schema}


def test_installazione_su_tenant_nuovo(db_session):
    """The whole immobili tenant chain runs on an empty schema (new tenant)."""
    schema = "tenant_pytest_beni_nuovo"
    conn = db_session.connection()
    conn.execute(text(f"CREATE SCHEMA {schema}"))
    conn.execute(text(f"SET search_path TO {schema}, public"))
    # Tables of other modules / the core chain that a new tenant already has.
    conn.execute(text("CREATE TABLE anag_soggetti_anagrafici (id SERIAL PRIMARY KEY)"))
    conn.execute(text("CREATE TABLE core_scadenze (id SERIAL PRIMARY KEY, entity_type VARCHAR(50), entity_id INTEGER)"))
    conn.execute(text("CREATE TABLE core_documenti (id SERIAL PRIMARY KEY, entity_type VARCHAR(50), entity_id INTEGER)"))
    for nome in CATENA_TENANT:
        modulo = _carica(nome)
        modulo.op = _Op(conn)
        modulo.context = _Context(schema)
        modulo.upgrade()

    def colonne(tabella):
        return {r[0] for r in conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_schema = :s AND table_name = :t"
        ), {"s": schema, "t": tabella})}

    assert "tipo_bene" in colonne("immo_beni")
    assert not colonne("immo_unita_immobiliari") & {"indirizzo", "citta", "codice", "created_at"}
    for tabella in ("immo_diritti_immobile", "immo_assegnazioni_conduttore",
                    "immo_variazioni_catastali", "immo_spese_ricorrenti"):
        assert "bene_id" in colonne(tabella), tabella
        assert "unita_immobiliare_id" not in colonne(tabella), tabella


def test_azzera_toglie_documenti_di_tutti_gli_oggetti_svuotati(db_session, migrazione):
    for entity_type in ("PROPRIETARIO", "SPESA", "INCASSO", "CERTIFICATO_ENERGETICO", "AFFITTUARIO"):
        db_session.execute(text(
            "INSERT INTO core_documenti (entity_type, entity_id, tipo_documento) VALUES (:t, 999001, 'ALTRO')"
        ), {"t": entity_type})
    migrazione.azzera(db_session.connection())
    rimasti = {r[0] for r in db_session.execute(text(
        "SELECT entity_type FROM core_documenti WHERE entity_id = 999001"))}
    # affittuari are not emptied, so their documents stay
    assert rimasti == {"AFFITTUARIO"}


def test_rieseguire_la_migrazione_non_riazzera(db_session, migrazione):
    bene_id = _conta(db_session,
        "INSERT INTO immo_beni (tipo_bene, codice) VALUES ('UNITA', 'AZZ-RERUN') RETURNING id")
    db_session.execute(text(
        "INSERT INTO immo_unita_immobiliari (id, tipo) VALUES (:id, 'Box')"), {"id": bene_id})
    migrazione.op = _Op(db_session.connection())
    migrazione.context = _Context("tenant_qa_test")
    migrazione.upgrade()
    assert _conta(db_session, "SELECT count(*) FROM immo_unita_immobiliari WHERE id = :id", id=bene_id) == 1
