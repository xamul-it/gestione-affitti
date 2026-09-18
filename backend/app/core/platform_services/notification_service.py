"""
NotificationService - Generic Core Notification Service

Creates in-app notifications and, optionally, sends the corresponding
email via the application's own SMTP account (NOTIFICHE_SMTP_* settings —
shared with gestione_pec, not duplicated per module). Core platform
service: any module imports and calls this directly (see
docs/superpowers/specs/2026-09-14-module-communication-architecture-design.md
§3.1) — never re-implement email sending in a module.

Usage:
    from app.core.platform_services import NotificationService
    service = NotificationService(db)
    service.notify(user_ids=[5, 8], tipo="scadenza.reminder", titolo="...", corpo="...")
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.platform.models import Notifica, CanaleNotifica, StatoEmailNotifica

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # WRITE
    # =========================================================================

    def notify(
        self,
        user_ids: List[int],
        tipo: str,
        titolo: str,
        corpo: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        link_url: Optional[str] = None,
        canali: CanaleNotifica = CanaleNotifica.ENTRAMBI,
    ) -> List[Notifica]:
        """
        Create one Notifica per user_id. If canali includes EMAIL, attempts
        to send it immediately via the application SMTP account and updates
        stato_email accordingly. A failed email never raises and never
        removes the in-app notification — it only sets stato_email=FAILED.
        """
        created: List[Notifica] = []

        vuole_email = canali in (CanaleNotifica.EMAIL, CanaleNotifica.ENTRAMBI)

        for user_id in user_ids:
            notifica = Notifica(
                user_id=user_id,
                tipo=tipo,
                titolo=titolo,
                corpo=corpo,
                entity_type=entity_type,
                entity_id=entity_id,
                link_url=link_url,
                canali=canali.value,
                stato_email=StatoEmailNotifica.PENDING.value if vuole_email else StatoEmailNotifica.NON_RICHIESTA.value,
            )
            self.db.add(notifica)
            self.db.flush()
            created.append(notifica)

        if vuole_email:
            for notifica in created:
                self._send_email_for(notifica)

        self.db.commit()
        for notifica in created:
            self.db.refresh(notifica)
        return created

    def _send_email_for(self, notifica: Notifica) -> None:
        """Attempts email delivery for one Notifica; updates it in place, never raises."""
        from app.core.config import settings
        from sqlalchemy import text

        if not settings.NOTIFICHE_SMTP_HOST:
            notifica.stato_email = StatoEmailNotifica.NON_RICHIESTA.value
            return

        row = self.db.execute(
            text("SELECT email FROM public.core_users WHERE id = :id AND email IS NOT NULL"),
            {"id": notifica.user_id},
        ).fetchone()
        if not row:
            notifica.stato_email = StatoEmailNotifica.FAILED.value
            notifica.errore_email = "Utente senza email"
            return

        try:
            self._send_via_smtp(row[0], notifica.titolo, notifica.corpo)
            notifica.stato_email = StatoEmailNotifica.SENT.value
            notifica.errore_email = None
        except Exception as exc:
            logger.warning("[NotificationService] invio email fallito per notifica user_id=%s: %s", notifica.user_id, exc)
            notifica.stato_email = StatoEmailNotifica.FAILED.value
            notifica.errore_email = str(exc)[:2000]

    @staticmethod
    def _send_via_smtp(to_email: str, subject: str, body_text: str) -> None:
        from app.core.config import settings

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.NOTIFICHE_SMTP_FROM_EMAIL or settings.NOTIFICHE_SMTP_USER
        msg["To"] = to_email
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

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
            with smtplib.SMTP(host, port, timeout=15) as smtp:
                if user and password:
                    smtp.login(user, password)
                smtp.sendmail(msg["From"], [to_email], msg.as_string())

    # =========================================================================
    # READ
    # =========================================================================

    def list_for_user(
        self,
        user_id: int,
        solo_non_lette: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Notifica]:
        query = self.db.query(Notifica).filter(Notifica.user_id == user_id)
        if solo_non_lette:
            query = query.filter(Notifica.letta.is_(False))
        return (
            query.order_by(Notifica.creata_il.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def badge_count(self, user_id: int) -> int:
        return (
            self.db.query(Notifica)
            .filter(Notifica.user_id == user_id, Notifica.letta.is_(False))
            .count()
        )

    # =========================================================================
    # STATE
    # =========================================================================

    def segna_letta(self, notifica_id: int, user_id: int) -> Optional[Notifica]:
        notifica = (
            self.db.query(Notifica)
            .filter(Notifica.id == notifica_id, Notifica.user_id == user_id)
            .first()
        )
        if not notifica:
            return None
        notifica.letta = True
        notifica.letta_il = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notifica)
        return notifica

    def segna_tutte_lette(self, user_id: int) -> int:
        notifiche = (
            self.db.query(Notifica)
            .filter(Notifica.user_id == user_id, Notifica.letta.is_(False))
            .all()
        )
        now = datetime.utcnow()
        for notifica in notifiche:
            notifica.letta = True
            notifica.letta_il = now
        self.db.commit()
        return len(notifiche)
