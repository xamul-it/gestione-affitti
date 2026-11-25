"""
Seeds of gestione_pec. No public data. With seed_test_data=True the tenant
gets one example mailbox that is never polled (is_attiva false, .invalid
hosts, fake credentials encrypted like real ones), one received message, the
admin enabled on it, an access audit row, a reply audit row and a
notification log row.

Idempotent: everything hangs off the mailbox address (scripts/tenant_prova.py
reruns it).
"""
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

INDIRIZZO = "esempio@pec.esempio.invalid"


def seed_public(db):
    """Nessun dato pubblico da inizializzare per il modulo PEC."""
    pass


def seed_esempi(db: Session) -> dict:
    from ..services.crypto_service import encrypt_credential

    if db.execute(text("SELECT 1 FROM pec_caselle WHERE indirizzo_pec = :i"), {"i": INDIRIZZO}).first():
        return {}
    utente = db.execute(text("SELECT id FROM public.core_users WHERE username = 'admin'")).scalar() \
        or db.execute(text("SELECT min(id) FROM public.core_users")).scalar()
    if not utente:
        return {}
    casella = db.execute(text(
        "INSERT INTO pec_caselle (nome_display, indirizzo_pec, imap_host, imap_port, imap_ssl, smtp_host, smtp_port, "
        "username_enc, password_enc, is_attiva, note) "
        "VALUES ('PEC di esempio', :i, 'imap.esempio.invalid', 993, true, 'smtp.esempio.invalid', 465, "
        ":u, :p, false, 'Casella di esempio: non viene mai interrogata') RETURNING id"
    ), {"i": INDIRIZZO, "u": encrypt_credential(INDIRIZZO), "p": encrypt_credential("non-una-password")}).scalar()
    messaggio = db.execute(text(
        "INSERT INTO pec_messaggi (casella_id, uid_imap, message_id, da, a, oggetto, data_invio, data_ricezione, "
        "corpo_testo, allegati_meta, is_letto) "
        "VALUES (:c, '1', '<esempio-1@pec.esempio.invalid>', 'comune@pec.esempio.invalid', :i, "
        "'Avviso di accertamento IMU (esempio)', '2026-03-02 09:00+01', '2026-03-02 09:01+01', "
        "'Testo di esempio.', CAST('[]' AS jsonb), true) RETURNING id"
    ), {"c": casella, "i": INDIRIZZO}).scalar()
    db.execute(text(
        "INSERT INTO pec_utenti_abilitati (casella_id, user_id, puo_rispondere, notifica_email) VALUES (:c, :u, true, false)"
    ), {"c": casella, "u": utente})
    db.execute(text(
        "INSERT INTO pec_audit_accessi (casella_id, messaggio_id, user_id, azione, dettagli) "
        "VALUES (:c, :m, :u, 'READ_MESSAGE', CAST('{\"esempio\": true}' AS jsonb))"
    ), {"c": casella, "m": messaggio, "u": utente})
    db.execute(text(
        "INSERT INTO pec_audit_risposte (casella_id, messaggio_originale_id, user_id, destinatari, oggetto_risposta, "
        "corpo_risposta_testo, smtp_status) "
        "VALUES (:c, :m, :u, 'comune@pec.esempio.invalid', 'Re: Avviso di accertamento IMU (esempio)', "
        "'Risposta di esempio.', 'FAILED')"
    ), {"c": casella, "m": messaggio, "u": utente})
    db.execute(text(
        "INSERT INTO pec_notifiche_log (casella_id, messaggio_id, user_id, email_destinatario, stato) "
        "VALUES (:c, :m, :u, 'admin@esempio.invalid', 'SENT')"
    ), {"c": casella, "m": messaggio, "u": utente})
    return {"pec_caselle": 1, "pec_messaggi": 1}


def seed_tenant(db: Session, tenant_id: Optional[int] = None, tenant_schema: Optional[str] = None,
                seed_test_data: bool = False) -> dict:
    if not seed_test_data:
        return {}
    risultati = seed_esempi(db)
    db.commit()
    return risultati
