"""
Servizio di notifica email per nuovi messaggi PEC.

Invia email agli utenti abilitati alla casella con notifica_email=True
quando il polling trova nuovi messaggi. Usa un SMTP applicativo separato
dalle caselle PEC dei clienti (configurato in NOTIFICHE_SMTP_*).

Principi:
- Non solleva mai eccezioni: swallows tutto e logga l'errore
- Logga ogni tentativo in pec_notifiche_log (SENT / FAILED)
- Se NOTIFICHE_SMTP_HOST non è configurato, la funzione è no-op
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers interni
# ---------------------------------------------------------------------------

def _is_notifiche_enabled() -> bool:
    """Controlla se le notifiche email sono configurate."""
    from app.core.config import settings
    return bool(settings.NOTIFICHE_SMTP_HOST)


def _build_email_text(casella_nome: str, casella_pec: str, num_messaggi: int) -> str:
    """Corpo plain-text della notifica."""
    if num_messaggi == 1:
        intro = "È arrivato 1 nuovo messaggio PEC"
    else:
        intro = f"Sono arrivati {num_messaggi} nuovi messaggi PEC"
    return (
        f"{intro} nella casella «{casella_nome}» ({casella_pec}).\n\n"
        "Accedi alla piattaforma per visualizzarli.\n\n"
        "-- Notifica automatica del sistema --"
    )


def _build_email_html(casella_nome: str, casella_pec: str, num_messaggi: str) -> str:
    """Corpo HTML della notifica."""
    if num_messaggi == 1:
        intro = "È arrivato <strong>1 nuovo messaggio PEC</strong>"
    else:
        intro = f"Sono arrivati <strong>{num_messaggi} nuovi messaggi PEC</strong>"
    return f"""<!DOCTYPE html>
<html lang="it">
<body style="font-family:sans-serif;color:#333;max-width:600px;margin:0 auto">
  <p>{intro} nella casella <em>{casella_nome}</em> ({casella_pec}).</p>
  <p>Accedi alla piattaforma per visualizzarli.</p>
  <hr style="border:none;border-top:1px solid #eee;margin-top:32px"/>
  <p style="font-size:12px;color:#888">Notifica automatica del sistema</p>
</body>
</html>"""


def _send_via_smtp(to_email: str, subject: str, body_text: str, body_html: str) -> None:
    """
    Invia effettivamente l'email tramite SMTP applicativo.

    Solleva eccezioni in caso di errore (gestite dal chiamante).
    """
    from app.core.config import settings

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.NOTIFICHE_SMTP_FROM_EMAIL or settings.NOTIFICHE_SMTP_USER
    msg["To"] = to_email

    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    host = settings.NOTIFICHE_SMTP_HOST
    port = settings.NOTIFICHE_SMTP_PORT
    user = settings.NOTIFICHE_SMTP_USER
    password = settings.NOTIFICHE_SMTP_PASSWORD
    tls = (settings.NOTIFICHE_SMTP_TLS or "STARTTLS").upper()

    if tls == "SSL":
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=ctx, timeout=15) as smtp:
            if user and password:
                smtp.login(user, password)
            smtp.sendmail(msg["From"], [to_email], msg.as_string())
    elif tls == "STARTTLS":
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            if user and password:
                smtp.login(user, password)
            smtp.sendmail(msg["From"], [to_email], msg.as_string())
    else:
        # Nessuna cifratura (sconsigliato in produzione)
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            if user and password:
                smtp.login(user, password)
            smtp.sendmail(msg["From"], [to_email], msg.as_string())


def _log_notifica(
    db: "Session",
    casella_id: int,
    messaggio_id: int | None,
    user_id: int,
    email_destinatario: str,
    stato: str,
    errore: str | None = None,
) -> None:
    """Salva il log della notifica in pec_notifiche_log. Swallows exceptions."""
    try:
        from gestione_pec.models.notifica_log import PecNotificaLog

        log = PecNotificaLog(
            casella_id=casella_id,
            messaggio_id=messaggio_id,
            user_id=user_id,
            email_destinatario=email_destinatario,
            stato=stato,
            errore=errore[:2000] if errore else None,
            sent_at=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
    except Exception as exc:
        logger.warning("[PecNotify] impossibile salvare log notifica: %s", exc)
        try:
            db.rollback()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# API pubblica
# ---------------------------------------------------------------------------

def notify_new_messages(
    db: "Session",
    casella_id: int,
    tenant_schema: str,
    num_messaggi: int,
    messaggio_ids: list[int] | None = None,
) -> None:
    """
    Invia notifiche email agli utenti abilitati con notifica_email=True.

    Chiamata da _poll_casella() dopo aver salvato i nuovi messaggi.
    Non solleva mai eccezioni.

    Args:
        db: sessione con search_path già impostato al tenant corretto
        casella_id: ID della casella che ha ricevuto nuovi messaggi
        tenant_schema: nome dello schema tenant (solo per logging)
        num_messaggi: numero di nuovi messaggi ricevuti
        messaggio_ids: lista opzionale di ID messaggi (per log granulare)
    """
    if not _is_notifiche_enabled():
        logger.debug(
            "[PecNotify] NOTIFICHE_SMTP_HOST non configurato, notifiche disabilitate"
        )
        return

    if num_messaggi <= 0:
        return

    try:
        from gestione_pec.models.casella import PecCasella
        from gestione_pec.models.utente_abilitato import PecUtenteAbilitato

        casella: PecCasella | None = (
            db.query(PecCasella).filter(PecCasella.id == casella_id).first()
        )
        if not casella:
            logger.warning(
                "[PecNotify] %s/%s: casella non trovata",
                tenant_schema, casella_id,
            )
            return

        # Recupera utenti con notifica abilitata
        utenti = (
            db.query(PecUtenteAbilitato)
            .filter(
                PecUtenteAbilitato.casella_id == casella_id,
                PecUtenteAbilitato.notifica_email == True,  # noqa: E712
            )
            .all()
        )

        if not utenti:
            logger.debug(
                "[PecNotify] %s/%s: nessun utente con notifica_email=True",
                tenant_schema, casella_id,
            )
            return

        # Recupera gli indirizzi email degli utenti da public.core_users
        # (ricorda: cross-schema, nessuna FK reale)
        user_ids = [u.user_id for u in utenti]
        user_id_to_notifica = {u.user_id: u for u in utenti}

        from sqlalchemy import text
        email_rows = db.execute(
            text(
                "SELECT id, email FROM public.core_users "
                "WHERE id = ANY(:ids) AND email IS NOT NULL"
            ),
            {"ids": user_ids},
        ).fetchall()

        if not email_rows:
            logger.debug(
                "[PecNotify] %s/%s: nessun indirizzo email trovato per gli utenti",
                tenant_schema, casella_id,
            )
            return

        if num_messaggi == 1:
            subject = f"[PEC] Nuovo messaggio in {casella.nome_display}"
        else:
            subject = f"[PEC] {num_messaggi} nuovi messaggi in {casella.nome_display}"

        body_text = _build_email_text(
            casella.nome_display, casella.indirizzo_pec, num_messaggi
        )
        body_html = _build_email_html(
            casella.nome_display, casella.indirizzo_pec, num_messaggi
        )

        # ID del primo messaggio nuovo (per il log), se disponibile
        primo_messaggio_id = messaggio_ids[0] if messaggio_ids else None

        for user_id, email in email_rows:
            try:
                _send_via_smtp(email, subject, body_text, body_html)
                _log_notifica(
                    db, casella_id, primo_messaggio_id, user_id, email, "SENT"
                )
                logger.info(
                    "[PecNotify] %s/%s: notifica inviata a %s",
                    tenant_schema, casella_id, email,
                )
            except Exception as exc:
                logger.warning(
                    "[PecNotify] %s/%s: errore invio notifica a %s: %s",
                    tenant_schema, casella_id, email, exc,
                )
                _log_notifica(
                    db, casella_id, primo_messaggio_id, user_id, email,
                    "FAILED", str(exc),
                )

    except Exception as exc:
        logger.error(
            "[PecNotify] %s/%s: errore inatteso nel servizio notifiche: %s",
            tenant_schema, casella_id, exc,
            exc_info=True,
        )
