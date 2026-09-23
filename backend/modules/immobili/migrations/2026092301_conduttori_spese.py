"""Add Conduttore, AssegnazioneConduttore and SpesaRicorrenteImmobile
tenant tables: the occupant-side counterpart to Proprietario/DirittoImmobile,
and a generalized recurring-expense/deadline tracker (IMU, TARI, utility
bills, ...) linked to either a property unit or a condominio.

Uses raw SQL via op.execute(), not op.create_table(): env.py's module
prefixing wrapper (_install_module_prefixing) normalizes this module's
module_short_code "IMMO" to the prefix "IMMO_" (uppercase), which never
matches this module's actual lowercase "immo_" table-name convention —
_should_prefix() then prepends "IMMO_" to already-correctly-named tables
(e.g. "immo_conduttori" -> "IMMO_immo_conduttori"), breaking every FK that
references the un-mangled name. op.execute() is not one of the wrapped
functions, so raw SQL sidesteps the bug entirely — the same reason
anagrafica_italiana's migrations (whose module_short_code "anag" happens
to already be lowercase, avoiding the mismatch) still use this style
rather than op.create_table().
"""
from alembic import op, context
from sqlalchemy import text

revision = "2026092301_conduttori_spese"
down_revision = "2025022002_tenant_tables"
branch_labels = None
depends_on = None

target_schema = "tenant"


def _get_target_schema():
    return context.get_x_argument(as_dictionary=True).get("schema")


def upgrade():
    schema = _get_target_schema()
    if not schema or schema == "public":
        return

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS immo_conduttori (
            id SERIAL PRIMARY KEY,
            soggetto_id INTEGER NOT NULL REFERENCES anag_soggetti_anagrafici(id) ON DELETE CASCADE,
            note VARCHAR(500),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        )
    """))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_immo_conduttori_soggetto_id ON immo_conduttori(soggetto_id)"))

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS immo_assegnazioni_conduttore (
            id SERIAL PRIMARY KEY,
            unita_immobiliare_id INTEGER NOT NULL REFERENCES immo_unita_immobiliari(id) ON DELETE CASCADE,
            conduttore_id INTEGER NOT NULL REFERENCES immo_conduttori(id) ON DELETE CASCADE,
            data_inizio DATE,
            data_fine DATE,
            note VARCHAR(500),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        )
    """))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_immo_assegnazioni_conduttore_unita "
        "ON immo_assegnazioni_conduttore(unita_immobiliare_id)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_immo_assegnazioni_conduttore_conduttore "
        "ON immo_assegnazioni_conduttore(conduttore_id)"
    ))

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS immo_spese_ricorrenti (
            id SERIAL PRIMARY KEY,
            unita_immobiliare_id INTEGER REFERENCES immo_unita_immobiliari(id) ON DELETE CASCADE,
            condominio_id INTEGER REFERENCES immo_condomini(id) ON DELETE CASCADE,
            tipo_spesa VARCHAR(50) NOT NULL,
            responsabile VARCHAR(20) NOT NULL,
            periodo VARCHAR(50) NOT NULL,
            rata VARCHAR(50),
            importo NUMERIC(10, 2) NOT NULL,
            data_scadenza DATE NOT NULL,
            pagato BOOLEAN NOT NULL DEFAULT false,
            data_pagamento DATE,
            note TEXT,
            scadenza_id INTEGER REFERENCES core_scadenze(id) ON DELETE SET NULL,
            CONSTRAINT ck_spesa_ricorrente_unita_xor_condominio
                CHECK ((unita_immobiliare_id IS NOT NULL) != (condominio_id IS NOT NULL))
        )
    """))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_immo_spese_ricorrenti_unita ON immo_spese_ricorrenti(unita_immobiliare_id)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_immo_spese_ricorrenti_condominio ON immo_spese_ricorrenti(condominio_id)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_immo_spese_ricorrenti_tipo_spesa ON immo_spese_ricorrenti(tipo_spesa)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_immo_spese_ricorrenti_responsabile ON immo_spese_ricorrenti(responsabile)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_immo_spese_ricorrenti_data_scadenza ON immo_spese_ricorrenti(data_scadenza)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_immo_spese_ricorrenti_pagato ON immo_spese_ricorrenti(pagato)"))


def downgrade():
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    op.execute(text("DROP TABLE IF EXISTS immo_spese_ricorrenti"))
    op.execute(text("DROP TABLE IF EXISTS immo_assegnazioni_conduttore"))
    op.execute(text("DROP TABLE IF EXISTS immo_conduttori"))
