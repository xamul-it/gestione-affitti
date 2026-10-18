"""
Servizio SMTP per l'invio di risposte PEC.
Si autentica come la casella PEC del cliente (non il server applicativo).
"""
import hashlib
import logging
import smtplib
import ssl
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import NamedTuple

logger = logging.getLogger(__name__)


class SmtpResult(NamedTuple):
    successo: bool
    message_id: str | None
    errore: str | None


class SmtpService:
    """
    Invia email SMTP autenticandosi come la casella PEC del cliente.

    Supporta tre modalità TLS:
    - "SSL"      → smtplib.SMTP_SSL (porta 465 default)
    - "STARTTLS" → smtplib.SMTP + starttls() (porta 587 default)
    - "none"     → smtplib.SMTP plain (non usare in produzione)
    """

    def __init__(self, casella, username_plain: str, password_plain: str):
        self.casella = casella
        self.username = username_plain
        self.password = password_plain

    def invia_risposta(
        self,
        destinatari: list[str],
        oggetto: str,
        corpo_testo: str,
        corpo_html: str | None = None,
        in_reply_to: str | None = None,
        references: str | None = None,
    ) -> SmtpResult:
        """
        Costruisce e invia un messaggio MIME Reply.

        Imposta correttamente gli header:
        - From: <indirizzo_pec casella>
        - To: destinatari
        - Subject: oggetto (se non inizia con "Re: " lo aggiunge)
        - In-Reply-To: message_id del messaggio originale
        - References: message_id del messaggio originale
        - Message-ID: generato univoco
        - Date: ora corrente

        Ritorna SmtpResult con successo/errore e message_id assegnato.
        """
        # Genera un Message-ID univoco
        domain = self.casella.indirizzo_pec.split("@")[1]
        message_id = f"<{uuid.uuid4().hex}@{domain}>"

        # Prepara soggetto con "Re: " se non già presente
        if not oggetto.lower().startswith("re:"):
            oggetto = f"Re: {oggetto}"

        # Costruisci messaggio MIME
        if corpo_html:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(corpo_testo, "plain", "utf-8"))
            msg.attach(MIMEText(corpo_html, "html", "utf-8"))
        else:
            msg = MIMEText(corpo_testo, "plain", "utf-8")

        msg["From"] = self.casella.indirizzo_pec
        msg["To"] = ", ".join(destinatari)
        msg["Subject"] = oggetto
        msg["Message-ID"] = message_id
        msg["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = references or in_reply_to

        try:
            self._send(msg, destinatari)
            return SmtpResult(successo=True, message_id=message_id, errore=None)
        except Exception as e:
            logger.error("[SmtpService] Errore invio: %s", e, exc_info=True)
            return SmtpResult(successo=False, message_id=None, errore=str(e))

    def _send(self, msg, destinatari: list[str]) -> None:
        host = self.casella.smtp_host
        port = self.casella.smtp_port or 465
        tls_mode = (self.casella.smtp_tls or "SSL").upper()

        if tls_mode == "SSL":
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=ctx, timeout=30) as server:
                server.login(self.username, self.password)
                server.sendmail(
                    self.casella.indirizzo_pec, destinatari, msg.as_string()
                )

        elif tls_mode == "STARTTLS":
            ctx = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=ctx)
                server.ehlo()
                server.login(self.username, self.password)
                server.sendmail(
                    self.casella.indirizzo_pec, destinatari, msg.as_string()
                )

        else:  # none
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.login(self.username, self.password)
                server.sendmail(
                    self.casella.indirizzo_pec, destinatari, msg.as_string()
                )


def calcola_hash_integrita(
    user_id: int,
    casella_pec: str,
    destinatari: str,
    oggetto: str,
    corpo: str,
    timestamp: str,
) -> str:
    """SHA-256 dei campi chiave per non-ripudio."""
    contenuto = f"{user_id}|{casella_pec}|{destinatari}|{oggetto}|{corpo}|{timestamp}"
    return hashlib.sha256(contenuto.encode("utf-8")).hexdigest()
