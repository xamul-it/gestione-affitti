"""create pec tables

Revision ID: 2026031901_create_pec_tables
Revises:
Create Date: 2026-03-19

Crea tutte le tabelle del modulo gestione_pec nello schema tenant.
Le tabelle vengono create in ordine rispettando le FK:
  1. pec_caselle
  2. pec_utenti_abilitati  (FK → pec_caselle)
  3. pec_messaggi          (FK → pec_caselle)
  4. pec_audit_accessi     (FK → pec_caselle, pec_messaggi)
  5. pec_audit_risposte    (FK → pec_caselle, pec_messaggi)
  6. pec_notifiche_log     (FK → pec_caselle, pec_messaggi)
"""

from alembic import op, context
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "2026031901_create_pec_tables"
down_revision = None
branch_labels = None
depends_on = None

# Run only in tenant schemas
target_schema = "tenant"


def upgrade() -> None:
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if not schema or schema == "public":
        return

    # 1. pec_caselle
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS pec_caselle (
            id                          SERIAL PRIMARY KEY,
            nome_display                VARCHAR(200)    NOT NULL,
            indirizzo_pec               VARCHAR(255)    NOT NULL,
            protocollo                  VARCHAR(10)     NOT NULL DEFAULT 'IMAP',
            imap_host                   VARCHAR(255)    NOT NULL,
            imap_port                   INTEGER         NOT NULL DEFAULT 993,
            imap_ssl                    BOOLEAN         NOT NULL DEFAULT true,
            imap_folder                 VARCHAR(100)    NOT NULL DEFAULT 'INBOX',
            segna_letto_su_server       BOOLEAN         NOT NULL DEFAULT false,
            smtp_host                   VARCHAR(255),
            smtp_port                   INTEGER                  DEFAULT 465,
            smtp_tls                    VARCHAR(20),
            username_enc                TEXT            NOT NULL,
            password_enc                TEXT            NOT NULL,
            polling_intervallo_minuti   INTEGER         NOT NULL DEFAULT 15,
            is_attiva                   BOOLEAN         NOT NULL DEFAULT true,
            ultimo_polling_at           TIMESTAMPTZ,
            ultimo_uid_visto            VARCHAR(100),
            errori_consecutivi          INTEGER         NOT NULL DEFAULT 0,
            ultimo_errore               TEXT,
            note                        TEXT,
            created_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at                  TIMESTAMPTZ,
            CONSTRAINT uq_pec_caselle_indirizzo_pec UNIQUE (indirizzo_pec)
        )
    """))

    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_caselle_is_attiva "
        "ON pec_caselle(is_attiva)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_caselle_indirizzo_pec "
        "ON pec_caselle(indirizzo_pec)"
    ))

    # 2. pec_utenti_abilitati
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS pec_utenti_abilitati (
            id              SERIAL PRIMARY KEY,
            casella_id      INTEGER     NOT NULL
                                REFERENCES pec_caselle(id) ON DELETE CASCADE,
            user_id         INTEGER     NOT NULL,
            puo_rispondere  BOOLEAN     NOT NULL DEFAULT false,
            notifica_email  BOOLEAN     NOT NULL DEFAULT true,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_pec_utenti_abilitati_casella_user
                UNIQUE (casella_id, user_id)
        )
    """))

    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_utenti_abilitati_casella_id "
        "ON pec_utenti_abilitati(casella_id)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_utenti_abilitati_user_id "
        "ON pec_utenti_abilitati(user_id)"
    ))

    # 3. pec_messaggi
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS pec_messaggi (
            id              SERIAL PRIMARY KEY,
            casella_id      INTEGER         NOT NULL
                                REFERENCES pec_caselle(id) ON DELETE CASCADE,
            uid_imap        VARCHAR(100)    NOT NULL,
            message_id      VARCHAR(500),
            in_reply_to     VARCHAR(500),
            thread_id       VARCHAR(500),
            da              VARCHAR(500)    NOT NULL,
            a               TEXT,
            cc              TEXT,
            oggetto         VARCHAR(1000),
            data_invio      TIMESTAMPTZ,
            data_ricezione  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            corpo_testo     TEXT,
            corpo_html      TEXT,
            allegati_meta   JSONB,
            is_letto        BOOLEAN         NOT NULL DEFAULT false,
            is_risposto     BOOLEAN         NOT NULL DEFAULT false,
            hash_contenuto  VARCHAR(64),
            created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_pec_messaggi_casella_uid
                UNIQUE (casella_id, uid_imap)
        )
    """))

    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_messaggi_casella_id "
        "ON pec_messaggi(casella_id)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_messaggi_thread_id "
        "ON pec_messaggi(thread_id)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_messaggi_hash_contenuto "
        "ON pec_messaggi(hash_contenuto)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_messaggi_data_ricezione "
        "ON pec_messaggi(data_ricezione)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_messaggi_is_letto "
        "ON pec_messaggi(is_letto)"
    ))

    # 4. pec_audit_accessi (append-only)
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS pec_audit_accessi (
            id              SERIAL PRIMARY KEY,
            casella_id      INTEGER
                                REFERENCES pec_caselle(id) ON DELETE SET NULL,
            messaggio_id    INTEGER
                                REFERENCES pec_messaggi(id) ON DELETE SET NULL,
            user_id         INTEGER     NOT NULL,
            azione          VARCHAR(50) NOT NULL,
            ip_address      VARCHAR(45),
            user_agent      TEXT,
            dettagli        JSONB,
            timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_audit_accessi_casella_id "
        "ON pec_audit_accessi(casella_id)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_audit_accessi_messaggio_id "
        "ON pec_audit_accessi(messaggio_id)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_audit_accessi_user_id "
        "ON pec_audit_accessi(user_id)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_audit_accessi_timestamp "
        "ON pec_audit_accessi(timestamp)"
    ))

    # 5. pec_audit_risposte (append-only)
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS pec_audit_risposte (
            id                          SERIAL PRIMARY KEY,
            casella_id                  INTEGER
                                            REFERENCES pec_caselle(id) ON DELETE SET NULL,
            messaggio_originale_id      INTEGER
                                            REFERENCES pec_messaggi(id) ON DELETE SET NULL,
            user_id                     INTEGER     NOT NULL,
            destinatari                 TEXT,
            oggetto_risposta            VARCHAR(1000),
            corpo_risposta_testo        TEXT,
            corpo_risposta_html         TEXT,
            message_id_risposta         VARCHAR(500),
            snapshot_da                 VARCHAR(500),
            snapshot_oggetto            VARCHAR(1000),
            snapshot_corpo_testo        TEXT,
            snapshot_data_invio         TIMESTAMPTZ,
            smtp_status                 VARCHAR(20),
            smtp_error                  TEXT,
            hash_integrita              VARCHAR(64),
            inviato_at                  TIMESTAMPTZ,
            created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_audit_risposte_casella_id "
        "ON pec_audit_risposte(casella_id)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_audit_risposte_messaggio_originale_id "
        "ON pec_audit_risposte(messaggio_originale_id)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_audit_risposte_user_id "
        "ON pec_audit_risposte(user_id)"
    ))

    # 6. pec_notifiche_log
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS pec_notifiche_log (
            id                  SERIAL PRIMARY KEY,
            casella_id          INTEGER
                                    REFERENCES pec_caselle(id) ON DELETE SET NULL,
            messaggio_id        INTEGER
                                    REFERENCES pec_messaggi(id) ON DELETE SET NULL,
            user_id             INTEGER     NOT NULL,
            email_destinatario  VARCHAR(255) NOT NULL,
            stato               VARCHAR(20)  NOT NULL,
            errore              TEXT,
            sent_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))

    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_notifiche_log_casella_id "
        "ON pec_notifiche_log(casella_id)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_notifiche_log_messaggio_id "
        "ON pec_notifiche_log(messaggio_id)"
    ))
    op.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pec_notifiche_log_user_id "
        "ON pec_notifiche_log(user_id)"
    ))


def downgrade() -> None:
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if not schema or schema == "public":
        return

    # Drop in reverse order to respect FK constraints
    op.execute(text("DROP TABLE IF EXISTS pec_notifiche_log CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS pec_audit_risposte CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS pec_audit_accessi CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS pec_messaggi CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS pec_utenti_abilitati CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS pec_caselle CASCADE"))
