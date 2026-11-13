"""Common asset (immo_beni) with the unit as joined subclass, after a data reset.

Phase 1 of docs/superpowers/specs/2026-11-10-beni-catastali-design.md.
The user decided (2026-11-12) to throw away this round's data and reload it
from the cadastral documents, so the migration first empties the immobili
tables and everything that depends on them (affitti_lungo contracts,
affitti_brevi bookings, documents/deadlines/relations of those objects),
then moves the common identification fields from immo_unita_immobiliari to
immo_beni (same id) and points rights, tenant assignments, cadastral changes
and recurring costs to bene_id. Files in storage are left alone.

promote.sh must be run with PROMOTE_PERDITA_CONSENTITA listing the emptied
tables, otherwise its row-count check stops the release.
"""
from alembic import op, context
from sqlalchemy import text

revision = "2026111201_beni"
down_revision = "2026110902_ape_migrato"
branch_labels = None
depends_on = None

target_schema = "tenant"

# Children before parents; TRUNCATE without CASCADE fails if a table that
# references these is missing from the list, instead of emptying it silently.
TABELLE_AZZERATE = (
    "immo_diritti_immobile",
    "immo_assegnazioni_conduttore",
    "immo_variazioni_catastali",
    "immo_spese_ricorrenti",
    "immo_certificati_energetici",
    "immo_millesimi_unita",
    "immo_tabelle_millesimali",
    "immo_proprietari",
    "immo_conduttori",
    # Exists only from 2026111301 on; listed so azzera() still works on a
    # schema migrated past it (tables that are missing are skipped).
    "immo_terreni_porzioni",
    "immo_terreni",
    "immo_unita_immobiliari",
    "immo_condomini",
    "ripartizioni_spese",
    "incassi",
    "spese",
    "contratti",
    "ab_ospiti_soggiorni",
    "ab_tasse_soggiorni",
    "ab_comunicazioni",
    "ab_soggiorni",
    "ab_prenotazioni",
    "ab_blocchi_calendario",
    "ab_calendari_canali",
)

# Every core_* entity_type whose objects live in TABELLE_AZZERATE: their ids
# restart from 1, so leftovers would attach to the next new object.
# AFFITTUARIO, TECNICO and SOGGETTO_ANAGRAFICO stay (their tables are kept).
ENTITY_TYPES_AZZERATI = (
    "immobile", "condominio", "spesa_ricorrente", "contratto", "comunicazione",
    "proprietario", "spesa", "incasso", "certificato_energetico",
)

TABELLE_CORE = ("core_relazioni", "core_documenti", "core_scadenze")

# Tables whose unita_immobiliare_id becomes bene_id.
TABELLE_FIGLIE = (
    "immo_diritti_immobile",
    "immo_assegnazioni_conduttore",
    "immo_variazioni_catastali",
    "immo_spese_ricorrenti",
)

COLONNE_SPOSTATE = (
    "codice", "indirizzo", "citta", "cap", "provincia",
    "foglio", "particella", "subalterno", "descrizione", "note",
    "created_at", "updated_at",
)


def _esiste(conn, tabella):
    return conn.execute(text("SELECT to_regclass(:t) IS NOT NULL"), {"t": tabella}).scalar()


def _colonna_esiste(conn, tabella, colonna):
    return conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = :t AND column_name = :c)"
    ), {"t": tabella, "c": colonna}).scalar()


def azzera(conn) -> dict:
    """Empty the asset data of the current schema; returns table -> rows removed."""
    risultato = {}
    presenti = [t for t in TABELLE_AZZERATE if _esiste(conn, t)]
    for tabella in presenti:
        risultato[tabella] = conn.execute(text(f"SELECT count(*) FROM {tabella}")).scalar()
    if presenti:
        conn.execute(text(f"TRUNCATE {', '.join(presenti)} RESTART IDENTITY"))
    for tabella in TABELLE_CORE:
        if _esiste(conn, tabella):
            risultato[tabella] = conn.execute(text(
                f"DELETE FROM {tabella} WHERE lower(entity_type) = ANY(:tipi)"
            ), {"tipi": list(ENTITY_TYPES_AZZERATI)}).rowcount
    return risultato


def _fk_sulla_colonna(conn, tabella, colonna):
    return [r[0] for r in conn.execute(text(
        "SELECT c.conname FROM pg_constraint c "
        "JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey) "
        "WHERE c.conrelid = to_regclass(:t) AND c.contype = 'f' AND a.attname = :c"
    ), {"t": tabella, "c": colonna})]


def _indici_sulla_colonna(conn, tabella, colonna):
    return [r[0] for r in conn.execute(text(
        "SELECT i.relname FROM pg_index x "
        "JOIN pg_class i ON i.oid = x.indexrelid "
        "JOIN pg_attribute a ON a.attrelid = x.indrelid AND a.attnum = ANY(x.indkey) "
        "WHERE x.indrelid = to_regclass(:t) AND NOT x.indisprimary AND a.attname = :c"
    ), {"t": tabella, "c": colonna})]


def ristruttura(conn) -> None:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS immo_beni (
            id SERIAL PRIMARY KEY,
            tipo_bene VARCHAR(10) NOT NULL CHECK (tipo_bene IN ('UNITA', 'TERRENO')),
            codice VARCHAR(50) NOT NULL UNIQUE,
            comune_codice VARCHAR(4),
            comune VARCHAR(100),
            provincia VARCHAR(2),
            indirizzo VARCHAR(255),
            cap VARCHAR(10),
            sezione VARCHAR(20),
            foglio VARCHAR(20),
            particella VARCHAR(20),
            denominatore VARCHAR(20),
            subalterno VARCHAR(20),
            partita VARCHAR(20),
            descrizione TEXT,
            note TEXT,
            attivo BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_immo_beni_foglio_particella ON immo_beni (foglio, particella)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_immo_beni_comune_codice ON immo_beni (comune_codice)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_immo_beni_tipo_bene ON immo_beni (tipo_bene)"))

    # The unit keeps its own data; the id is the bene's id.
    for colonna in COLONNE_SPOSTATE:
        conn.execute(text(f"ALTER TABLE immo_unita_immobiliari DROP COLUMN IF EXISTS {colonna}"))
    conn.execute(text("ALTER TABLE immo_unita_immobiliari ALTER COLUMN id DROP DEFAULT"))
    conn.execute(text("DROP SEQUENCE IF EXISTS immo_unita_immobiliari_id_seq"))
    if not _fk_sulla_colonna(conn, "immo_unita_immobiliari", "id"):
        conn.execute(text(
            "ALTER TABLE immo_unita_immobiliari ADD CONSTRAINT immo_unita_immobiliari_bene_fkey "
            "FOREIGN KEY (id) REFERENCES immo_beni(id) ON DELETE CASCADE"
        ))

    for tabella in TABELLE_FIGLIE:
        if not _colonna_esiste(conn, tabella, "unita_immobiliare_id"):
            continue
        for fk in _fk_sulla_colonna(conn, tabella, "unita_immobiliare_id"):
            conn.execute(text(f"ALTER TABLE {tabella} DROP CONSTRAINT {fk}"))
        for indice in _indici_sulla_colonna(conn, tabella, "unita_immobiliare_id"):
            conn.execute(text(f"DROP INDEX {indice}"))
        if tabella == "immo_spese_ricorrenti":
            conn.execute(text(
                "ALTER TABLE immo_spese_ricorrenti DROP CONSTRAINT IF EXISTS ck_spesa_ricorrente_unita_xor_condominio"
            ))
        conn.execute(text(f"ALTER TABLE {tabella} RENAME COLUMN unita_immobiliare_id TO bene_id"))
        conn.execute(text(
            f"ALTER TABLE {tabella} ADD CONSTRAINT {tabella}_bene_id_fkey "
            "FOREIGN KEY (bene_id) REFERENCES immo_beni(id) ON DELETE CASCADE"
        ))
        conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{tabella}_bene ON {tabella} (bene_id)"))
        if tabella == "immo_spese_ricorrenti":
            conn.execute(text(
                "ALTER TABLE immo_spese_ricorrenti ADD CONSTRAINT ck_spesa_ricorrente_bene_xor_condominio "
                "CHECK ((bene_id IS NOT NULL) <> (condominio_id IS NOT NULL))"
            ))


def _get_target_schema():
    return context.get_x_argument(as_dictionary=True).get("schema")


def upgrade():
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    conn = op.get_bind()
    if not _esiste(conn, "immo_unita_immobiliari"):
        return
    # Reset only the old layout (code still on the unit): never a schema
    # already moved to immo_beni, nor a new tenant created empty.
    if _colonna_esiste(conn, "immo_unita_immobiliari", "codice"):
        azzera(conn)
    ristruttura(conn)


def downgrade():
    raise NotImplementedError(
        "2026111201_beni azzera i dati: per tornare indietro ripristinare il backup di promote.sh"
    )
