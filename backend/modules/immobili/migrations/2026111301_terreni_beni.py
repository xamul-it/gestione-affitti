"""Land parcels become beni (same id in immo_beni) with portions.

Phase 2a of docs/superpowers/specs/2026-11-10-beni-catastali-design.md.
Unlike 2026111201 nothing is thrown away: every land parcel of the old
layout becomes a bene of type TERRENO plus one portion holding its
quality, class, surface (always in m²) and incomes.

Old layout = immo_terreni still has the column `comune`. A new tenant
whose immo_terreni was created by 2025022002 from today's model already
has the new layout: only the portions table is added.
"""
from alembic import op, context
from sqlalchemy import text

revision = "2026111301_terreni_beni"
down_revision = "2026111201_beni"
branch_labels = None
depends_on = None

target_schema = "tenant"

# Fields of the old immo_terreni that move to immo_beni (old name -> new name).
COLONNE_COMUNI = {
    "codice": "codice",
    "descrizione": "descrizione",
    "indirizzo": "indirizzo",
    "comune": "comune",
    "cap": "cap",
    "provincia": "provincia",
    "sezione_catastale": "sezione",
    "foglio": "foglio",
    "particella": "particella",
    "subalterno": "subalterno",
    "note": "note",
}


def _esiste(conn, tabella):
    return conn.execute(text("SELECT to_regclass(:t) IS NOT NULL"), {"t": tabella}).scalar()


def _colonna_esiste(conn, tabella, colonna):
    return conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = :t AND column_name = :c)"
    ), {"t": tabella, "c": colonna}).scalar()


def _crea_terreni(conn) -> None:
    """New immo_terreni: same columns as models/terreno.py (Terreno(Bene))."""
    conn.execute(text("""
        CREATE TABLE immo_terreni (
            id INTEGER PRIMARY KEY REFERENCES immo_beni(id) ON DELETE CASCADE,
            nome VARCHAR(255),
            tipologia_id INTEGER REFERENCES public.immo_tipologie_terreno(id) ON DELETE SET NULL,
            nazione VARCHAR(100) DEFAULT 'Italia',
            superficie_mq DOUBLE PRECISION,
            edificabile BOOLEAN NOT NULL DEFAULT FALSE,
            esente_imu_montano BOOLEAN NOT NULL DEFAULT FALSE,
            servitu TEXT
        )
    """))
    conn.execute(text("CREATE INDEX ix_immo_terreni_tipologia_id ON immo_terreni (tipologia_id)"))


def crea_porzioni(conn) -> None:
    """Portions table, idempotent; immo_terreni must already have the new layout."""
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS immo_terreni_porzioni (
            id SERIAL PRIMARY KEY,
            terreno_id INTEGER NOT NULL REFERENCES immo_terreni(id) ON DELETE CASCADE,
            porzione VARCHAR(5),
            qualita VARCHAR(100) NOT NULL,
            classe VARCHAR(10),
            superficie_mq DOUBLE PRECISION NOT NULL CHECK (superficie_mq >= 0),
            reddito_dominicale NUMERIC(12, 2),
            reddito_agrario NUMERIC(12, 2),
            deduzioni VARCHAR(100)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_immo_terreni_porzioni_terreno ON immo_terreni_porzioni (terreno_id)"
    ))


def converti(conn) -> int:
    """Move the old-layout land parcels to immo_beni; returns how many were converted."""
    if not _esiste(conn, "immo_terreni") or not _colonna_esiste(conn, "immo_terreni", "comune"):
        return 0
    conn.execute(text("ALTER TABLE immo_terreni RENAME TO immo_terreni_vecchi"))
    # Constraint and index names stay with the renamed table: free them.
    for (nome,) in conn.execute(text(
        "SELECT conname FROM pg_constraint WHERE conrelid = 'immo_terreni_vecchi'::regclass "
        "AND contype IN ('p', 'u', 'f')"
    )).all():
        conn.execute(text(f'ALTER TABLE immo_terreni_vecchi DROP CONSTRAINT "{nome}"'))
    for (nome,) in conn.execute(text(
        "SELECT indexname FROM pg_indexes WHERE schemaname = current_schema() "
        "AND tablename = 'immo_terreni_vecchi'"
    )).all():
        conn.execute(text(f'DROP INDEX "{nome}"'))
    _crea_terreni(conn)
    crea_porzioni(conn)

    vecchi = conn.execute(text("SELECT * FROM immo_terreni_vecchi ORDER BY id")).mappings().all()
    for v in vecchi:
        valori = {nuovo: v[vecchio] for vecchio, nuovo in COLONNE_COMUNI.items()}
        codice = valori["codice"]
        while conn.execute(text("SELECT 1 FROM immo_beni WHERE codice = :c"), {"c": codice}).first():
            codice = f"{codice}-T"
        valori["codice"] = codice
        valori["attivo"] = True if v["attivo"] is None else v["attivo"]
        valori["created_at"] = v["created_at"]
        valori["updated_at"] = v["updated_at"]
        colonne = ", ".join(valori)
        segnaposti = ", ".join(f":{c}" for c in valori)
        bene_id = conn.execute(text(
            f"INSERT INTO immo_beni (tipo_bene, {colonne}) "
            f"VALUES ('TERRENO', {segnaposti.replace(':created_at', 'coalesce(:created_at, now())')}) "
            "RETURNING id"
        ), valori).scalar()
        superficie = v["superficie"] or 0
        if (v["unita_misura_superficie"] or "").lower() == "ha":
            superficie = superficie * 10000
        conn.execute(text(
            "INSERT INTO immo_terreni (id, nome, tipologia_id, nazione, superficie_mq) "
            "VALUES (:id, :nome, :tipologia_id, :nazione, :superficie)"
        ), {"id": bene_id, "nome": v["nome"], "tipologia_id": v["tipologia_id"],
            "nazione": v["nazione"], "superficie": superficie})
        conn.execute(text(
            "INSERT INTO immo_terreni_porzioni (terreno_id, qualita, classe, superficie_mq, "
            "reddito_dominicale, reddito_agrario) "
            "VALUES (:id, coalesce(:qualita, 'NON INDICATA'), :classe, :superficie, :rd, :ra)"
        ), {"id": bene_id, "qualita": v["qualita_coltura"], "classe": v["classe_catastale"],
            "superficie": superficie, "rd": v["reddito_dominicale"], "ra": v["reddito_agrario"]})

    conn.execute(text("DROP TABLE immo_terreni_vecchi"))
    return len(vecchi)


def _get_target_schema():
    return context.get_x_argument(as_dictionary=True).get("schema")


def upgrade():
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    conn = op.get_bind()
    if not _esiste(conn, "immo_terreni"):
        return
    converti(conn)
    crea_porzioni(conn)


def downgrade():
    raise NotImplementedError(
        "2026111301_terreni_beni: per tornare indietro ripristinare il backup di promote.sh"
    )
