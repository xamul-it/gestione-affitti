"""
Compliance Scadenze Service

Collega affitti_brevi al motore scadenze core della piattaforma
(app.core.platform_services.scadenza_service.ScadenzaService) per le
comunicazioni obbligatorie legate a un Soggiorno: comunicazione Polizia
(24h dal check-in) e promemoria pagamento tassa di soggiorno (giorno del
check-in). Vedi docs/superpowers/specs/2026-09-28-affitti-brevi-motore-
scadenze-compliance-design.md.

Non invia nulla a nessun portale esterno: il completamento è sempre
manuale in questa fase (vedi completa_comunicazione).
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from affitti_brevi.models import (
    Comunicazione,
    MetodoInvio,
    TipoComunicazione,
    StatoComunicazione,
    Soggiorno,
)
from app.core.auth.init_data import get_system_user_id
from app.core.auth.models import User
from app.core.platform_services import ScadenzaService
from app.core.schemas import ScadenzaCreate, PrioritaScadenza


def _get_admin_destinatari_ids(db: Session) -> List[int]:
    """
    Id di tutti i superuser attivi del tenant corrente.

    Non esiste ancora un concetto di "responsabile struttura" nel sistema
    (vedi spec, sezione decisioni di scope): per questo sotto-progetto le
    scadenze compliance notificano tutti gli admin del tenant.
    """
    return [
        row[0] for row in
        db.query(User.id).filter(User.is_superuser == True, User.is_active == True).all()
    ]


class ComplianceScadenzeService:
    def __init__(self, db: Session):
        self.db = db

    def genera_scadenza_polizia(self, soggiorno: Soggiorno) -> Optional[Comunicazione]:
        """Genera la Comunicazione+Scadenza per la comunicazione Polizia
        (24h dal check-in). Idempotente: None se già esiste."""
        esistente = self.db.query(Comunicazione).filter(
            Comunicazione.soggiorno_id == soggiorno.id,
            Comunicazione.tipo == TipoComunicazione.POLIZIA.value,
        ).first()
        if esistente:
            return None

        checkin_start = datetime.combine(soggiorno.data_checkin, datetime.min.time()).replace(tzinfo=timezone.utc)
        scadenza_dt = checkin_start + timedelta(hours=24)

        comunicazione = Comunicazione(
            soggiorno_id=soggiorno.id,
            unita_immobiliare_id=soggiorno.unita_immobiliare_id,
            tipo=TipoComunicazione.POLIZIA.value,
            stato=StatoComunicazione.DA_PREPARARE.value,
            data_scadenza=scadenza_dt,
        )
        self.db.add(comunicazione)
        self.db.flush()

        scadenza = ScadenzaService(self.db).create_scadenza(
            ScadenzaCreate(
                modulo="affitti_brevi",
                entity_type="comunicazione",
                entity_id=comunicazione.id,
                titolo=f"Comunicazione Polizia — Soggiorno #{soggiorno.id}",
                descrizione=(
                    f"Comunicare i dati di {soggiorno.numero_ospiti_previsti} ospiti entro 24h "
                    f"dal check-in del {soggiorno.data_checkin.isoformat()}."
                ),
                data_scadenza=scadenza_dt.date(),
                priorita=PrioritaScadenza.ALTA,
                destinatari_ids=_get_admin_destinatari_ids(self.db),
            ),
            user_id=get_system_user_id(self.db),
        )
        comunicazione.scadenza_id = scadenza.id
        self.db.commit()
        self.db.refresh(comunicazione)
        return comunicazione

    def genera_scadenza_tassa(self, soggiorno: Soggiorno) -> Optional[Comunicazione]:
        """Genera la Comunicazione+Scadenza promemoria pagamento tassa di
        soggiorno (giorno del check-in). Idempotente: None se già esiste."""
        esistente = self.db.query(Comunicazione).filter(
            Comunicazione.soggiorno_id == soggiorno.id,
            Comunicazione.tipo == TipoComunicazione.TASSA_DICHIARAZIONE.value,
        ).first()
        if esistente:
            return None

        checkin_start = datetime.combine(soggiorno.data_checkin, datetime.min.time()).replace(tzinfo=timezone.utc)

        importo = None
        if soggiorno.tassa_soggiorno is not None:
            importo = soggiorno.tassa_soggiorno.importo_effettivo

        descrizione = f"Richiedi il pagamento della tassa di soggiorno per il soggiorno #{soggiorno.id}."
        descrizione += f" Importo calcolato: € {importo:.2f}." if importo is not None else " Importo da calcolare."

        comunicazione = Comunicazione(
            soggiorno_id=soggiorno.id,
            unita_immobiliare_id=soggiorno.unita_immobiliare_id,
            tipo=TipoComunicazione.TASSA_DICHIARAZIONE.value,
            stato=StatoComunicazione.DA_PREPARARE.value,
            data_scadenza=checkin_start,
        )
        self.db.add(comunicazione)
        self.db.flush()

        scadenza = ScadenzaService(self.db).create_scadenza(
            ScadenzaCreate(
                modulo="affitti_brevi",
                entity_type="comunicazione",
                entity_id=comunicazione.id,
                titolo=f"Richiedi pagamento tassa di soggiorno — Soggiorno #{soggiorno.id}",
                descrizione=descrizione,
                data_scadenza=soggiorno.data_checkin,
                priorita=PrioritaScadenza.MEDIA,
                destinatari_ids=_get_admin_destinatari_ids(self.db),
            ),
            user_id=get_system_user_id(self.db),
        )
        comunicazione.scadenza_id = scadenza.id
        self.db.commit()
        self.db.refresh(comunicazione)
        return comunicazione

    def completa_comunicazione(self, comunicazione_id: int, note: Optional[str] = None) -> Comunicazione:
        """Marca la Comunicazione come inviata (manualmente) e completa la
        Scadenza core collegata, se presente."""
        comunicazione = self.db.query(Comunicazione).filter(
            Comunicazione.id == comunicazione_id
        ).first()
        if not comunicazione:
            raise ValueError(f"Comunicazione {comunicazione_id} non trovata")

        comunicazione.mark_inviata(MetodoInvio.MANUALE)
        self.db.commit()
        self.db.refresh(comunicazione)

        if comunicazione.scadenza_id:
            ScadenzaService(self.db).completa_scadenza(
                comunicazione.scadenza_id,
                user_id=get_system_user_id(self.db),
                note=note or "Completata da affitti_brevi",
            )

        return comunicazione
