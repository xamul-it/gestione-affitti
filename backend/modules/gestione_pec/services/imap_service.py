"""
Servizio IMAP per la lettura dei messaggi PEC.

Responsabilità:
- Connessione all'host IMAP configurato sulla PecCasella
- Recupero incrementale dei messaggi tramite UID (PEEK o normale a seconda
  di segna_letto_su_server)
- Parsing dell'intero messaggio email (intestazioni RFC 2047, body, allegati)
- Restituzione di una lista di dict pronti per essere salvati nel DB

NON modifica nulla nel database: è compito di _poll_casella() in
polling_scheduler.py.
"""
from __future__ import annotations

import email
import email.utils
import hashlib
import logging
import socket
from email.header import decode_header
from typing import TYPE_CHECKING

import imapclient
import imapclient.exceptions

if TYPE_CHECKING:
    from gestione_pec.models.casella import PecCasella

logger = logging.getLogger(__name__)

# Quanti giorni di storia recuperare al primo sync
_FIRST_SYNC_DAYS = 30


# ---------------------------------------------------------------------------
# Helper RFC 2047 decode
# ---------------------------------------------------------------------------

def _decode_header_value(value: str | None) -> str | None:
    """Decodifica un header email che può contenere encoding RFC 2047."""
    if not value:
        return None
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded).strip() or None


# ---------------------------------------------------------------------------
# Classe principale
# ---------------------------------------------------------------------------

class ImapService:
    """
    Gestisce la sessione IMAP per una singola PecCasella.

    Args:
        casella:        istanza ORM PecCasella (solo lettura).
        username_plain: username IMAP già decifrato.
        password_plain: password IMAP già decifrata.
    """

    def __init__(self, casella: "PecCasella", username_plain: str, password_plain: str) -> None:
        self._casella = casella
        self._username = username_plain
        self._password = password_plain

    # ------------------------------------------------------------------
    # API pubblica
    # ------------------------------------------------------------------

    def fetch_new_messages(self) -> list[dict]:
        """
        Connette al server IMAP, scarica i nuovi messaggi e li restituisce
        come lista di dict.

        Non modifica nessuno stato sul server né nel database.

        Returns:
            Lista di dict con tutti i campi necessari a costruire un
            PecMessaggio.  La lista è vuota se non ci sono messaggi nuovi.
        """
        casella = self._casella

        try:
            client = imapclient.IMAPClient(
                host=casella.imap_host,
                port=casella.imap_port,
                ssl=casella.imap_ssl,
                timeout=30,
            )
        except (socket.timeout, ConnectionRefusedError, OSError) as exc:
            logger.error(
                "[ImapService] %s: errore connessione: %s",
                casella.indirizzo_pec, exc,
            )
            return []

        try:
            try:
                client.login(self._username, self._password)
            except imapclient.exceptions.LoginError as exc:
                logger.error(
                    "[ImapService] %s: credenziali non valide: %s",
                    casella.indirizzo_pec, exc,
                )
                return []

            client.select_folder(casella.imap_folder, readonly=True)

            uids = self._search_uids(client)
            if not uids:
                return []

            results = []
            for uid in uids:
                parsed = self._fetch_and_parse(client, uid)
                if parsed is not None:
                    results.append(parsed)
            return results

        except (socket.timeout, ConnectionRefusedError, OSError) as exc:
            logger.error(
                "[ImapService] %s: errore di rete durante il fetch: %s",
                casella.indirizzo_pec, exc,
            )
            return []
        except Exception as exc:
            logger.error(
                "[ImapService] %s: errore inatteso: %s",
                casella.indirizzo_pec, exc,
                exc_info=True,
            )
            return []
        finally:
            try:
                client.logout()
            except Exception:
                pass

    def test_connection(self) -> dict:
        """
        Verifica connessione e login IMAP.

        Returns:
            {"successo": bool, "messaggio": str, "num_messaggi": int | None}
        """
        casella = self._casella
        try:
            client = imapclient.IMAPClient(
                host=casella.imap_host,
                port=casella.imap_port,
                ssl=casella.imap_ssl,
                timeout=10,
            )
        except (socket.timeout, ConnectionRefusedError, OSError) as exc:
            return {"successo": False, "messaggio": f"Errore di connessione: {exc}", "num_messaggi": None}

        try:
            try:
                client.login(self._username, self._password)
            except imapclient.exceptions.LoginError as exc:
                return {"successo": False, "messaggio": f"Credenziali non valide: {exc}", "num_messaggi": None}

            inbox_info = client.select_folder(casella.imap_folder, readonly=True)
            num_messaggi = inbox_info.get(b"EXISTS", 0)
            return {"successo": True, "messaggio": "Connessione riuscita", "num_messaggi": num_messaggi}

        except (socket.timeout, ConnectionRefusedError, OSError) as exc:
            return {"successo": False, "messaggio": f"Errore di rete: {exc}", "num_messaggi": None}
        except Exception as exc:
            return {"successo": False, "messaggio": str(exc), "num_messaggi": None}
        finally:
            try:
                client.logout()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Metodi privati
    # ------------------------------------------------------------------

    def _search_uids(self, client: imapclient.IMAPClient) -> list[int]:
        """
        Determina la lista di UID da recuperare in base all'ultimo UID visto.

        Strategia:
        - Primo sync (ultimo_uid_visto is None): SINCE ultimi 30 giorni
        - Sync incrementale: cerca UID maggiori di ultimo_uid_visto usando
          i criteri UID RANGE e poi filtra manualmente
        """
        casella = self._casella

        if casella.ultimo_uid_visto is None:
            from datetime import date, timedelta
            since_date = date.today() - timedelta(days=_FIRST_SYNC_DAYS)
            # imapclient accetta date Python direttamente
            uids = client.search(["SINCE", since_date])
            return uids

        # Recupera tutti i messaggi a partire dall'ultimo uid (incluso)
        # usando la sintassi UID range "ultimo_uid:*"
        last_uid = int(casella.ultimo_uid_visto)
        try:
            # Il range "last_uid:*" include l'ultimo UID già processato,
            # quindi lo escludiamo nel filtro
            uids = client.search(["UID", f"{last_uid}:*"])
        except Exception:
            # Alcuni server non supportano search per UID range: fallback UNSEEN
            uids = client.search(["UNSEEN"])
            return uids

        # Escludi l'UID già processato in precedenza
        return [uid for uid in uids if uid > last_uid]

    def _fetch_and_parse(self, client: imapclient.IMAPClient, uid: int) -> dict | None:
        """
        Recupera un singolo messaggio via IMAP e lo parsa.

        Usa BODY.PEEK[] se segna_letto_su_server è False,
        altrimenti BODY[] (che marca il flag Seen sul server).
        """
        casella = self._casella
        fetch_key = b"BODY[]" if casella.segna_letto_su_server else b"BODY.PEEK[]"
        fetch_spec = ["RFC822.SIZE"]
        if casella.segna_letto_su_server:
            fetch_spec.append("BODY[]")
        else:
            fetch_spec.append("BODY.PEEK[]")

        try:
            data = client.fetch([uid], fetch_spec)
        except Exception as exc:
            logger.warning("[ImapService] UID %s: errore fetch: %s", uid, exc)
            return None

        if uid not in data:
            return None

        msg_data = data[uid]
        raw_bytes = msg_data.get(fetch_key)
        if not raw_bytes:
            # Prova chiave alternativa nel caso il server risponda in modo diverso
            for key in msg_data:
                if isinstance(key, bytes) and b"BODY" in key:
                    raw_bytes = msg_data[key]
                    break

        if not raw_bytes:
            logger.warning("[ImapService] UID %s: corpo vuoto", uid)
            return None

        try:
            msg = email.message_from_bytes(raw_bytes)
        except Exception as exc:
            logger.warning("[ImapService] UID %s: errore parsing: %s", uid, exc)
            return None

        return self._extract_fields(uid, msg)

    def _extract_fields(self, uid: int, msg: email.message.Message) -> dict:
        """Estrae tutti i campi da un oggetto email.message.Message."""
        # --- Intestazioni ---
        da = _decode_header_value(msg.get("From")) or ""
        a = _decode_header_value(msg.get("To"))
        cc = _decode_header_value(msg.get("Cc"))
        oggetto = _decode_header_value(msg.get("Subject"))

        raw_message_id = msg.get("Message-ID", "")
        message_id = raw_message_id.strip().strip("<>").strip() or None

        raw_in_reply_to = msg.get("In-Reply-To", "")
        in_reply_to = raw_in_reply_to.strip().strip("<>").strip() or None

        # Thread ID: primo elemento di References, poi In-Reply-To, poi Message-ID
        references_raw = msg.get("References", "")
        thread_id: str | None = None
        if references_raw:
            first_ref = references_raw.split()[0]
            thread_id = first_ref.strip("<>").strip() or None
        if not thread_id:
            thread_id = in_reply_to
        if not thread_id:
            thread_id = message_id

        # Data invio
        data_invio = None
        date_str = msg.get("Date")
        if date_str:
            try:
                data_invio = email.utils.parsedate_to_datetime(date_str)
            except Exception:
                data_invio = None

        # --- Corpo e allegati ---
        corpo_testo: str | None = None
        corpo_html: str | None = None
        allegati_meta: list[dict] = []

        if msg.is_multipart():
            for part in msg.walk():
                self._process_part(part, corpo_testo, corpo_html, allegati_meta)
                # Aggiorna i valori se la parte li ha aggiornati (pattern iterativo)
            # Riprocessa in modo imperativo
            corpo_testo, corpo_html, allegati_meta = self._walk_parts(msg)
        else:
            content_type = msg.get_content_type()
            charset = msg.get_content_charset() or "utf-8"
            payload = msg.get_payload(decode=True)
            if payload:
                if content_type == "text/plain":
                    corpo_testo = payload.decode(charset, errors="replace")
                elif content_type == "text/html":
                    corpo_html = payload.decode(charset, errors="replace")

        # --- Hash contenuto per deduplicazione ---
        hash_contenuto = hashlib.sha256(
            f"{da}|{oggetto}|{data_invio}".encode("utf-8", errors="replace")
        ).hexdigest()

        return {
            "uid_imap": str(uid),
            "message_id": message_id,
            "in_reply_to": in_reply_to,
            "thread_id": thread_id,
            "da": da,
            "a": a,
            "cc": cc,
            "oggetto": oggetto,
            "data_invio": data_invio,
            "corpo_testo": corpo_testo,
            "corpo_html": corpo_html,
            "allegati_meta": allegati_meta if allegati_meta else None,
            "hash_contenuto": hash_contenuto,
        }

    def _walk_parts(
        self, msg: email.message.Message
    ) -> tuple[str | None, str | None, list[dict]]:
        """
        Percorre ricorsivamente le parti di un messaggio multipart ed estrae
        corpo testo, corpo HTML e metadati allegati.
        """
        corpo_testo: str | None = None
        corpo_html: str | None = None
        allegati_meta: list[dict] = []

        for part in msg.walk():
            content_disposition = part.get("Content-Disposition", "")
            content_type = part.get_content_type()
            charset = part.get_content_charset() or "utf-8"

            # Allegati (Content-Disposition: attachment)
            if "attachment" in content_disposition.lower():
                filename = _decode_header_value(part.get_filename()) or "allegato"
                payload_bytes = part.get_payload(decode=True)
                allegati_meta.append({
                    "nome": filename,
                    "content_type": content_type,
                    "dimensione_bytes": len(payload_bytes) if payload_bytes else 0,
                })
                continue

            payload_bytes = part.get_payload(decode=True)
            if not payload_bytes:
                continue

            if content_type == "text/plain" and corpo_testo is None:
                corpo_testo = payload_bytes.decode(charset, errors="replace")
            elif content_type == "text/html" and corpo_html is None:
                corpo_html = payload_bytes.decode(charset, errors="replace")

        return corpo_testo, corpo_html, allegati_meta

    # Metodo placeholder usato prima del refactor — kept per evitare errori
    # se qualcosa dovesse chiamarlo; la logica reale è in _walk_parts
    def _process_part(self, part, corpo_testo, corpo_html, allegati_meta):
        pass
