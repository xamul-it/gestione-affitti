"""Raggruppamenti (rami) of beni — phase 4a of
docs/superpowers/specs/2026-11-10-beni-catastali-design.md.

crea_schema(): table immo_raggruppamenti and column immo_beni.raggruppamento_id.
converti(): open PARTE_DI_FONDO links become one FONDO ramo per main parcel.
It stops and lists the doubtful cases before any write. Nothing is zeroed.
Downgrade is the backup.
"""
from alembic import op, context
from sqlalchemy import text

revision = "2026112502_raggruppamenti"
down_revision = "2026112501_relazione_unica"
branch_labels = None
depends_on = None

target_schema = "tenant"


def crea_schema(conn) -> None:
    """Table, column, indexes; idempotent; same columns as models/raggruppamento.py."""
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS immo_raggruppamenti (
            id SERIAL PRIMARY KEY,
            tipo VARCHAR(30) NOT NULL,
            nome VARCHAR(200) NOT NULL,
            padre_id INTEGER REFERENCES immo_raggruppamenti(id) ON DELETE RESTRICT,
            descrizione TEXT,
            note TEXT,
            attivo BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ,
            CONSTRAINT immo_raggruppamenti_non_se_stesso CHECK (padre_id IS NULL OR padre_id <> id)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_immo_raggruppamenti_padre_id ON immo_raggruppamenti (padre_id)"))
    conn.execute(text(
        "ALTER TABLE immo_beni ADD COLUMN IF NOT EXISTS raggruppamento_id INTEGER"))
    esiste_fk = conn.execute(text(
        "SELECT 1 FROM pg_constraint WHERE conname = 'immo_beni_raggruppamento_id_fkey' "
        "AND connamespace = current_schema()::regnamespace")).first()
    if not esiste_fk:
        conn.execute(text(
            "ALTER TABLE immo_beni ADD CONSTRAINT immo_beni_raggruppamento_id_fkey "
            "FOREIGN KEY (raggruppamento_id) REFERENCES immo_raggruppamenti(id) ON DELETE RESTRICT"))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_immo_beni_raggruppamento_id ON immo_beni (raggruppamento_id)"))


def _dubbi(conn) -> list:
    """Cases the migration does not guess: listed, then it stops before any write."""
    problemi = []
    for r in conn.execute(text("""
        SELECT k.id, p.codice AS principale, c.codice AS collegato, k.data_fine
        FROM immo_beni_collegamenti k JOIN immo_beni p ON p.id = k.bene_id JOIN immo_beni c ON c.id = k.bene_collegato_id
        WHERE k.tipo = 'PARTE_DI_FONDO' AND k.data_fine IS NOT NULL ORDER BY k.id""")):
        problemi.append(f"collegamento {r.id} {r.principale} -> {r.collegato} chiuso il {r.data_fine}: "
                        "si perderebbe, decidere prima")
    for r in conn.execute(text("""
        SELECT c.codice, string_agg(p.codice, ', ' ORDER BY p.codice) AS fondi
        FROM immo_beni_collegamenti k JOIN immo_beni p ON p.id = k.bene_id JOIN immo_beni c ON c.id = k.bene_collegato_id
        WHERE k.tipo = 'PARTE_DI_FONDO' AND k.data_fine IS NULL
        GROUP BY c.codice HAVING count(DISTINCT k.bene_id) > 1 ORDER BY c.codice""")):
        problemi.append(f"particella {r.codice} in più fondi ({r.fondi})")
    for r in conn.execute(text("""
        SELECT DISTINCT b.codice FROM immo_beni b
        WHERE EXISTS (SELECT 1 FROM immo_beni_collegamenti k WHERE k.tipo = 'PARTE_DI_FONDO'
                      AND k.data_fine IS NULL AND k.bene_id = b.id)
          AND EXISTS (SELECT 1 FROM immo_beni_collegamenti k WHERE k.tipo = 'PARTE_DI_FONDO'
                      AND k.data_fine IS NULL AND k.bene_collegato_id = b.id)
        ORDER BY b.codice""")):
        problemi.append(f"terreno {r.codice} è sia fondo principale sia parte di un altro fondo")
    for r in conn.execute(text("""
        SELECT DISTINCT b.codice FROM immo_beni b JOIN immo_beni_collegamenti k
          ON k.tipo = 'PARTE_DI_FONDO' AND k.data_fine IS NULL AND b.id IN (k.bene_id, k.bene_collegato_id)
        WHERE b.raggruppamento_id IS NOT NULL ORDER BY b.codice""")):
        problemi.append(f"terreno {r.codice} è già in un raggruppamento")
    return problemi


def converti(conn) -> dict:
    """Open PARTE_DI_FONDO links -> one FONDO ramo per main parcel (name = its code), holding the
    main parcel and its parts; the links are then removed. PERTINENZA and FABBRICATO_SU_PARTICELLA
    stay links. Stops with the list of doubtful cases before writing anything."""
    problemi = _dubbi(conn)
    if problemi:
        raise RuntimeError("Migrazione raggruppamenti fermata, casi da decidere:\n  - " + "\n  - ".join(problemi))
    conteggi = {"fondi_creati": 0, "terreni_spostati": 0, "collegamenti_rimossi": 0}
    fondi = conn.execute(text("""
        SELECT k.bene_id, p.codice, array_agg(k.bene_collegato_id ORDER BY k.bene_collegato_id) AS parti
        FROM immo_beni_collegamenti k JOIN immo_beni p ON p.id = k.bene_id
        WHERE k.tipo = 'PARTE_DI_FONDO' AND k.data_fine IS NULL
        GROUP BY k.bene_id, p.codice ORDER BY p.codice""")).all()
    for principale, codice, parti in fondi:
        ramo = conn.execute(text(
            "INSERT INTO immo_raggruppamenti (tipo, nome) VALUES ('FONDO', :n) RETURNING id"), {"n": codice}).scalar()
        conteggi["fondi_creati"] += 1
        conteggi["terreni_spostati"] += conn.execute(text(
            "UPDATE immo_beni SET raggruppamento_id = :r WHERE id = ANY(:ids)"),
            {"r": ramo, "ids": [principale, *parti]}).rowcount
    conteggi["collegamenti_rimossi"] = conn.execute(text(
        "DELETE FROM immo_beni_collegamenti WHERE tipo = 'PARTE_DI_FONDO'")).rowcount
    return conteggi


def _get_target_schema():
    return context.get_x_argument(as_dictionary=True).get("schema")


def upgrade():
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    conn = op.get_bind()
    if not conn.execute(text("SELECT to_regclass('immo_beni') IS NOT NULL")).scalar():
        return
    crea_schema(conn)
    conteggi = converti(conn)
    print(f"  [{schema}] raggruppamenti: {conteggi}", flush=True)


def downgrade():
    raise NotImplementedError("Restore from the backup taken before the migration")
