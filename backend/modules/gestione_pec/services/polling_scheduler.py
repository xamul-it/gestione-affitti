"""
Scheduler di polling PEC basato su APScheduler.

Architettura:
- Un job per casella PEC attiva (identificato da "pec_poll_{tenant}_{id}")
- Ogni job chiama la funzione standalone _poll_casella() in un thread
  separato (BackgroundScheduler usa un thread pool interno)
- Il singleton globale viene avviato da register_module() all'avvio
  dell'applicazione

Tenant discovery:
- Legge le righe attive da public.core_tenants (colonne: schema_name, active)
- Per ogni tenant imposta il search_path prima di interrogare pec_caselle
"""
from __future__ import annotations

import logging
import random
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Job function (standalone per evitare circular imports al boot)
# ---------------------------------------------------------------------------

def _poll_casella(casella_id: int, tenant_schema: str) -> None:
    """
    Esegue un ciclo di polling IMAP per la casella specificata.

    Chiamata dal BackgroundScheduler in un thread del suo pool.
    Tutti gli import sono locali per evitare problemi di circular import
    durante il boot dell'applicazione.
    """
    # Import locali obbligatori — NON spostare a livello di modulo
    from datetime import datetime, timezone

    from sqlalchemy import text

    from app.core.database import SessionLocal
    from gestione_pec.models.casella import PecCasella
    from gestione_pec.models.messaggio import PecMessaggio
    from gestione_pec.services.crypto_service import decrypt_credential
    from gestione_pec.services.imap_service import ImapService

    MAX_ERRORI_CONSECUTIVI = 5

    db = SessionLocal()
    try:
        db.execute(text(f"SET search_path TO {tenant_schema}, public"))
        db.commit()  # SET non transazionale su alcuni driver — flush immediato

        casella: PecCasella | None = (
            db.query(PecCasella).filter(PecCasella.id == casella_id).first()
        )
        if not casella or not casella.is_attiva:
            logger.debug(
                "[PecPoll] %s/%s: casella non trovata o inattiva, job saltato",
                tenant_schema, casella_id,
            )
            return

        # Decifra credenziali — MAI loggare i valori restituiti
        password_plain = decrypt_credential(casella.password_enc)
        username_plain = decrypt_credential(casella.username_enc)

        imap = ImapService(casella, username_plain, password_plain)
        messaggi_dati = imap.fetch_new_messages()

        nuovi = 0
        max_uid: str | None = casella.ultimo_uid_visto

        for dati in messaggi_dati:
            # Deduplicazione per (casella_id, uid_imap)
            exists = (
                db.query(PecMessaggio)
                .filter(
                    PecMessaggio.casella_id == casella_id,
                    PecMessaggio.uid_imap == dati["uid_imap"],
                )
                .first()
            )
            if exists:
                continue

            msg = PecMessaggio(
                casella_id=casella_id,
                uid_imap=dati["uid_imap"],
                message_id=dati.get("message_id"),
                in_reply_to=dati.get("in_reply_to"),
                thread_id=dati.get("thread_id"),
                da=dati.get("da", ""),
                a=dati.get("a"),
                cc=dati.get("cc"),
                oggetto=dati.get("oggetto"),
                data_invio=dati.get("data_invio"),
                corpo_testo=dati.get("corpo_testo"),
                corpo_html=dati.get("corpo_html"),
                allegati_meta=dati.get("allegati_meta"),
                hash_contenuto=dati.get("hash_contenuto"),
                is_letto=False,
                is_risposto=False,
            )
            db.add(msg)
            nuovi += 1

            # Tieni traccia del massimo UID visto in questo batch
            uid_int = int(dati["uid_imap"])
            if max_uid is None or uid_int > int(max_uid):
                max_uid = dati["uid_imap"]

        db.flush()

        # Raccoglie gli ID dei nuovi messaggi prima del commit per passarli alle notifiche
        nuovi_ids: list[int] = []
        if nuovi > 0:
            # flush() ha già assegnato gli id; li recuperiamo dal db
            from gestione_pec.models.messaggio import PecMessaggio as _Msg
            recenti = (
                db.query(_Msg.id)
                .filter(
                    _Msg.casella_id == casella_id,
                    _Msg.uid_imap.in_(
                        [str(d["uid_imap"]) for d in messaggi_dati]
                    ),
                )
                .all()
            )
            nuovi_ids = [r[0] for r in recenti]

        # Aggiorna stato della casella
        casella.ultimo_polling_at = datetime.now(timezone.utc)
        casella.errori_consecutivi = 0
        casella.ultimo_errore = None
        if max_uid is not None:
            casella.ultimo_uid_visto = str(max_uid)

        db.commit()

        if nuovi > 0:
            logger.info(
                "[PecPoll] %s/%s: %d nuovi messaggi salvati",
                tenant_schema, casella_id, nuovi,
            )
            from gestione_pec.services.notification_service import notify_new_messages
            notify_new_messages(db, casella_id, tenant_schema, nuovi, nuovi_ids)
        else:
            logger.debug(
                "[PecPoll] %s/%s: nessun nuovo messaggio",
                tenant_schema, casella_id,
            )

    except Exception as exc:
        logger.error(
            "[PecPoll] %s/%s: errore durante il polling: %s",
            tenant_schema, casella_id, exc,
            exc_info=True,
        )
        try:
            db.rollback()
            # Rilancia il search_path dopo il rollback
            db.execute(text(f"SET search_path TO {tenant_schema}, public"))
            from gestione_pec.models.casella import PecCasella as _PecCasella
            casella = db.query(_PecCasella).filter(_PecCasella.id == casella_id).first()
            if casella:
                casella.errori_consecutivi = (casella.errori_consecutivi or 0) + 1
                casella.ultimo_errore = str(exc)[:2000]  # Limita la lunghezza
                if casella.errori_consecutivi >= MAX_ERRORI_CONSECUTIVI:
                    casella.is_attiva = False
                    logger.warning(
                        "[PecPoll] %s/%s: casella disattivata dopo %d errori consecutivi",
                        tenant_schema, casella_id, MAX_ERRORI_CONSECUTIVI,
                    )
                db.commit()
        except Exception as inner_exc:
            logger.error(
                "[PecPoll] %s/%s: impossibile aggiornare stato errore: %s",
                tenant_schema, casella_id, inner_exc,
            )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class PecPollingScheduler:
    """
    Gestisce un BackgroundScheduler APScheduler con un job per casella PEC.

    Utilizza un lock per rendere thread-safe start/stop.
    """

    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 60,
            }
        )
        self._started = False
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Avvia lo scheduler e carica i job per tutte le caselle attive."""
        with self._lock:
            if self._started:
                logger.debug("[PecScheduler] già avviato, skip")
                return
            self.scheduler.start()
            self._started = True
            logger.info("[PecScheduler] BackgroundScheduler avviato")

        # Carica i job fuori dal lock per evitare deadlock nelle query DB
        self._load_all_jobs()

    def stop(self) -> None:
        """Arresta lo scheduler in modo sicuro."""
        with self._lock:
            if not self._started:
                return
            try:
                self.scheduler.shutdown(wait=False)
            except Exception as exc:
                logger.warning("[PecScheduler] errore durante lo shutdown: %s", exc)
            finally:
                self._started = False
                logger.info("[PecScheduler] scheduler arrestato")

    # ------------------------------------------------------------------
    # Job management
    # ------------------------------------------------------------------

    def _load_all_jobs(self) -> None:
        """
        Legge tutti i tenant attivi da public.core_tenants e crea i job
        per le rispettive caselle PEC.
        """
        from sqlalchemy import text

        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            tenants = db.execute(
                text(
                    "SELECT schema_name FROM public.core_tenants "
                    "WHERE active = true OR active IS NULL"
                )
            ).fetchall()
        except Exception as exc:
            logger.warning("[PecScheduler] impossibile leggere i tenant: %s", exc)
            tenants = []
        finally:
            db.close()

        for row in tenants:
            tenant_schema = row[0]
            self._load_tenant_jobs(tenant_schema)

    def _load_tenant_jobs(self, tenant_schema: str) -> None:
        """Carica i job per tutte le caselle attive di un singolo tenant."""
        from sqlalchemy import text

        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            db.execute(text(f"SET search_path TO {tenant_schema}, public"))
            db.commit()

            # Import locale per evitare circular import al boot
            from gestione_pec.models.casella import PecCasella

            caselle = (
                db.query(PecCasella)
                .filter(PecCasella.is_attiva == True)  # noqa: E712
                .all()
            )
            for casella in caselle:
                self.add_casella_job(
                    casella.id,
                    tenant_schema,
                    casella.polling_intervallo_minuti,
                )
        except Exception as exc:
            logger.warning(
                "[PecScheduler] impossibile caricare job per tenant %s: %s",
                tenant_schema, exc,
            )
        finally:
            db.close()

    def add_casella_job(
        self,
        casella_id: int,
        tenant_schema: str,
        intervallo_minuti: int,
    ) -> None:
        """
        Aggiunge o sostituisce il job di polling per una singola casella.

        Il jitter (0-60 s) distribuisce l'esecuzione iniziale per evitare
        che tutti i job partano contemporaneamente.
        """
        if not self._started:
            logger.warning(
                "[PecScheduler] scheduler non avviato, impossibile aggiungere job "
                "per %s/%s",
                tenant_schema, casella_id,
            )
            return

        job_id = f"pec_poll_{tenant_schema}_{casella_id}"
        jitter = random.randint(0, 60)

        self.scheduler.add_job(
            func=_poll_casella,
            trigger=IntervalTrigger(minutes=intervallo_minuti, jitter=jitter),
            id=job_id,
            args=[casella_id, tenant_schema],
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            name=f"PEC poll {tenant_schema}/{casella_id}",
        )
        logger.info(
            "[PecScheduler] job registrato: %s ogni %d min",
            job_id, intervallo_minuti,
        )

    def remove_casella_job(self, casella_id: int, tenant_schema: str) -> None:
        """Rimuove il job di polling per una casella. Silenzioso se non esiste."""
        job_id = f"pec_poll_{tenant_schema}_{casella_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info("[PecScheduler] job rimosso: %s", job_id)
        except Exception:
            # Il job potrebbe non esistere — comportamento atteso
            pass

    def reschedule_casella_job(
        self,
        casella_id: int,
        tenant_schema: str,
        intervallo_minuti: int,
    ) -> None:
        """
        Aggiorna l'intervallo di polling per una casella.
        Se il job non esiste, lo crea ex novo.
        """
        job_id = f"pec_poll_{tenant_schema}_{casella_id}"
        try:
            self.scheduler.reschedule_job(
                job_id,
                trigger=IntervalTrigger(minutes=intervallo_minuti),
            )
            logger.info(
                "[PecScheduler] job rischedulato: %s ogni %d min",
                job_id, intervallo_minuti,
            )
        except Exception:
            # Job non esiste ancora
            self.add_casella_job(casella_id, tenant_schema, intervallo_minuti)

    def trigger_now(self, casella_id: int, tenant_schema: str) -> None:
        """
        Esegue il polling immediatamente in un thread daemon separato.
        Non attende il completamento.
        """
        t = threading.Thread(
            target=_poll_casella,
            args=[casella_id, tenant_schema],
            daemon=True,
            name=f"pec_manual_{tenant_schema}_{casella_id}",
        )
        t.start()
        logger.info(
            "[PecScheduler] polling manuale avviato per %s/%s",
            tenant_schema, casella_id,
        )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Restituisce lo stato corrente dello scheduler e la lista dei job."""
        jobs = []
        if self._started:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": (
                        job.next_run_time.isoformat()
                        if job.next_run_time
                        else None
                    ),
                })
        return {"running": self._started, "jobs": jobs}


# ---------------------------------------------------------------------------
# Singleton globale
# ---------------------------------------------------------------------------

_scheduler: PecPollingScheduler | None = None
_singleton_lock = threading.Lock()


def get_scheduler() -> PecPollingScheduler:
    """Restituisce l'istanza singleton di PecPollingScheduler."""
    global _scheduler
    if _scheduler is None:
        with _singleton_lock:
            if _scheduler is None:
                _scheduler = PecPollingScheduler()
    return _scheduler
