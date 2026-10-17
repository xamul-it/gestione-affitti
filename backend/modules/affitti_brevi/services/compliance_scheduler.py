"""
Compliance Scheduler Service

Scheduler in background (APScheduler) che ogni ora scandisce i Soggiorno
con check-in nelle prossime 48 ore, per ogni tenant con affitti_brevi
abilitato, e genera le scadenze di compliance (Polizia, tassa di
soggiorno) tramite ComplianceScadenzeService. Vedi docs/superpowers/specs/
2026-09-28-affitti-brevi-motore-scadenze-compliance-design.md.

Stesso pattern bound-Connection di sync_scheduler.py: un Session legato
all'engine restituisce la connessione al pool a ogni commit, e la query
successiva potrebbe capitare su una connessione diversa che non ha più
il search_path impostato.
"""
from datetime import date, timedelta
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import engine
from .tenant_scan import get_active_tenant_schemas
from .compliance_scadenze_service import ComplianceScadenzeService

logger = logging.getLogger(__name__)


def _scan_tenant(tenant_schema: str) -> dict:
    """Genera le scadenze di compliance dovute per un tenant."""
    if not tenant_schema.replace('_', '').replace('-', '').isalnum():
        logger.error("Invalid tenant schema, skipping compliance scan: %s", tenant_schema)
        return {'soggiorni_esaminati': 0, 'comunicazioni_create': 0, 'errori': 1}

    connection = engine.connect()
    try:
        connection.execute(text(f"SET search_path TO {tenant_schema}, public"))
        connection.commit()

        db = Session(bind=connection)
        try:
            from affitti_brevi.models import Soggiorno

            oggi = date.today()
            limite = oggi + timedelta(days=2)
            soggiorni = db.query(Soggiorno).filter(
                Soggiorno.valido == True,
                Soggiorno.data_checkin >= oggi,
                Soggiorno.data_checkin <= limite,
            ).all()

            service = ComplianceScadenzeService(db)
            create = 0
            errori = 0
            for soggiorno in soggiorni:
                try:
                    if service.genera_scadenza_polizia(soggiorno) is not None:
                        create += 1
                    if service.genera_scadenza_tassa(soggiorno) is not None:
                        create += 1
                except Exception as exc:
                    errori += 1
                    logger.error(
                        "Compliance scan failed for soggiorno %s (tenant %s): %s",
                        soggiorno.id, tenant_schema, exc, exc_info=True,
                    )
            return {
                'soggiorni_esaminati': len(soggiorni),
                'comunicazioni_create': create,
                'errori': errori,
            }
        finally:
            db.close()
    except Exception as exc:
        logger.error("Compliance scan failed for tenant %s: %s", tenant_schema, exc, exc_info=True)
        return {'soggiorni_esaminati': 0, 'comunicazioni_create': 0, 'errori': 1}
    finally:
        connection.close()


class ComplianceScheduler:
    """Scheduler in background per la generazione delle scadenze di compliance."""

    def __init__(self, interval_hours: int = 1):
        self.scheduler = BackgroundScheduler()
        self.interval_hours = interval_hours
        self.is_running = False

    def scan_job(self):
        logger.info("Starting scheduled compliance scan job")
        totals = {'soggiorni_esaminati': 0, 'comunicazioni_create': 0, 'errori': 0}
        for tenant_schema in get_active_tenant_schemas("affitti_brevi"):
            stats = _scan_tenant(tenant_schema)
            for key in totals:
                totals[key] += stats.get(key, 0)
        logger.info(
            "Compliance scan completed: %s soggiorni esaminati, %s comunicazioni create, %s errori",
            totals['soggiorni_esaminati'], totals['comunicazioni_create'], totals['errori'],
        )

    def start(self):
        if self.is_running:
            logger.warning("Compliance scheduler already running")
            return
        try:
            self.scheduler.add_job(
                func=self.scan_job,
                trigger=IntervalTrigger(hours=self.interval_hours),
                id='compliance_scan_job',
                name='Compliance Scadenze Scan',
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            self.scheduler.start()
            self.is_running = True
            logger.info(f"Compliance scheduler started (interval: {self.interval_hours} hours)")

            # Stesso motivo di sync_scheduler.py: job iniziale schedulato come
            # one-off sul thread di background, non eseguito sincrono qui —
            # questo metodo è chiamato da register_module(app), che gira a
            # import-time di app.main (anche per la test suite).
            self.scheduler.add_job(
                func=self.scan_job,
                id='compliance_scan_job_initial',
                name='Compliance Scadenze Scan (initial)',
                replace_existing=True,
            )
        except Exception as exc:
            logger.error(f"Failed to start compliance scheduler: {exc}", exc_info=True)
            raise

    def stop(self):
        if not self.is_running:
            logger.warning("Compliance scheduler not running")
            return
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("Compliance scheduler stopped")


_scheduler_instance = None


def get_compliance_scheduler(interval_hours: int = 1) -> ComplianceScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ComplianceScheduler(interval_hours)
    return _scheduler_instance
