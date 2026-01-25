"""
SoggiornoService - Operational Stay Management

Manages the operational lifecycle of stays:
- Automatic creation from confirmed bookings
- Guest data collection tracking
- Check-in/check-out status management
- Notification triggers for data collection
- Compliance status tracking (Police, ISTAT, Tax)

Key requirements from analysis:
- Automatic notification at start of occupation
- Data collection reminders with escalation
- Support for guest self-service data entry
"""
from datetime import date, datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging
import secrets

from ..models import (
    Prenotazione,
    Soggiorno,
    OspiteSoggiorno,
    Comunicazione,
    StatoPrenotazione,
    StatoSoggiorno,
    StatoCompliance,
    TipoComunicazione,
    StatoComunicazione,
    RuoloOspite
)

logger = logging.getLogger(__name__)


class SoggiornoService:
    """
    Soggiorno (Stay) Management Service

    Handles the operational aspects of guest stays including:
    - Creation from bookings
    - Data collection status
    - Check-in/check-out management
    - Compliance tracking
    """

    def __init__(self, db: Session):
        self.db = db

    def crea_soggiorno_da_prenotazione(self, prenotazione: Prenotazione) -> Soggiorno:
        """
        Create a Soggiorno from a confirmed Prenotazione.

        Called automatically when a booking is confirmed.
        Creates the operational stay record and initializes compliance tracking.

        Args:
            prenotazione: The confirmed booking

        Returns:
            Created Soggiorno
        """
        # Check if soggiorno already exists
        if prenotazione.soggiorno:
            logger.warning(f"Soggiorno already exists for prenotazione {prenotazione.id}")
            return prenotazione.soggiorno

        # Create soggiorno
        soggiorno = Soggiorno(
            prenotazione_id=prenotazione.id,
            unita_immobiliare_id=prenotazione.unita_immobiliare_id,
            data_checkin=prenotazione.data_checkin,
            data_checkout=prenotazione.data_checkout,
            numero_ospiti_previsti=prenotazione.numero_ospiti,
            stato=StatoSoggiorno.CREATO.value,
            valido=True
        )

        # Generate self-service token
        soggiorno.genera_token_self_service()

        self.db.add(soggiorno)
        self.db.commit()
        self.db.refresh(soggiorno)

        # Create police communication record (deadline: check-in + 24h)
        self._crea_comunicazione_polizia(soggiorno)

        logger.info(f"Created soggiorno {soggiorno.id} from prenotazione {prenotazione.id}")

        return soggiorno

    def _crea_comunicazione_polizia(self, soggiorno: Soggiorno) -> Comunicazione:
        """Create police communication record for a stay"""
        # Deadline is 24 hours after check-in (at midnight)
        checkin_dt = datetime.combine(
            soggiorno.data_checkin,
            datetime.min.time()
        ).replace(tzinfo=timezone.utc)
        scadenza = checkin_dt + timedelta(hours=24)

        comunicazione = Comunicazione(
            soggiorno_id=soggiorno.id,
            unita_immobiliare_id=soggiorno.unita_immobiliare_id,
            tipo=TipoComunicazione.POLIZIA.value,
            stato=StatoComunicazione.DA_PREPARARE.value,
            data_scadenza=scadenza,
            data_scadenza_legale=scadenza
        )

        self.db.add(comunicazione)
        self.db.commit()

        # Update soggiorno compliance status
        soggiorno.stato_polizia = StatoCompliance.IN_ATTESA.value
        self.db.commit()

        return comunicazione

    def registra_ospite(
        self,
        soggiorno_id: int,
        dati_ospite: Dict,
        principale: bool = False
    ) -> OspiteSoggiorno:
        """
        Register a guest for a stay.

        Args:
            soggiorno_id: Stay ID
            dati_ospite: Guest data dictionary
            principale: Whether this is the primary guest

        Returns:
            Created OspiteSoggiorno
        """
        soggiorno = self.db.query(Soggiorno).filter(
            Soggiorno.id == soggiorno_id
        ).first()

        if not soggiorno:
            raise ValueError(f"Soggiorno {soggiorno_id} non trovato")

        # If this is the first guest and no principale set, mark as principale
        if not soggiorno.ospiti and not principale:
            principale = True

        # Create guest record
        ospite = OspiteSoggiorno(
            soggiorno_id=soggiorno_id,
            principale=principale,
            ruolo=RuoloOspite.PRINCIPALE.value if principale else RuoloOspite.ACCOMPAGNATORE.value,
            cognome=dati_ospite.get("cognome", ""),
            nome=dati_ospite.get("nome", ""),
            data_nascita=dati_ospite.get("data_nascita"),
            luogo_nascita=dati_ospite.get("luogo_nascita"),
            provincia_nascita=dati_ospite.get("provincia_nascita"),
            stato_nascita=dati_ospite.get("stato_nascita", "ITALIA"),
            cittadinanza=dati_ospite.get("cittadinanza", "ITALIANA"),
            sesso=dati_ospite.get("sesso"),
            indirizzo_residenza=dati_ospite.get("indirizzo_residenza"),
            comune_residenza=dati_ospite.get("comune_residenza"),
            provincia_residenza=dati_ospite.get("provincia_residenza"),
            stato_residenza=dati_ospite.get("stato_residenza", "ITALIA"),
            email=dati_ospite.get("email"),
            telefono=dati_ospite.get("telefono"),
            tipo_documento=dati_ospite.get("tipo_documento"),
            numero_documento=dati_ospite.get("numero_documento"),
            ente_rilascio=dati_ospite.get("ente_rilascio"),
            data_rilascio=dati_ospite.get("data_rilascio"),
            data_scadenza=dati_ospite.get("data_scadenza"),
            stato_rilascio=dati_ospite.get("stato_rilascio"),
            consenso_privacy=dati_ospite.get("consenso_privacy", False),
            inserito_da_ospite=dati_ospite.get("inserito_da_ospite", False)
        )

        if ospite.consenso_privacy:
            ospite.data_consenso_privacy = datetime.now(timezone.utc)

        if ospite.inserito_da_ospite:
            ospite.data_inserimento_ospite = datetime.now(timezone.utc)

        self.db.add(ospite)

        # Update soggiorno counters
        soggiorno.numero_ospiti_registrati += 1
        soggiorno.aggiorna_stato_dati()

        self.db.commit()
        self.db.refresh(ospite)

        logger.info(f"Registered guest {ospite.id} ({ospite.nome_completo}) for soggiorno {soggiorno_id}")

        return ospite

    def esegui_checkin(
        self,
        soggiorno_id: int,
        numero_ospiti_effettivi: Optional[int] = None
    ) -> Soggiorno:
        """
        Execute check-in for a stay.

        Args:
            soggiorno_id: Stay ID
            numero_ospiti_effettivi: Actual guest count (if different from expected)

        Returns:
            Updated Soggiorno
        """
        soggiorno = self.db.query(Soggiorno).filter(
            Soggiorno.id == soggiorno_id
        ).first()

        if not soggiorno:
            raise ValueError(f"Soggiorno {soggiorno_id} non trovato")

        # Update status
        soggiorno.stato = StatoSoggiorno.CHECK_IN_EFFETTUATO.value
        soggiorno.data_ora_checkin_effettivo = datetime.now(timezone.utc)

        if numero_ospiti_effettivi:
            soggiorno.numero_ospiti_effettivi = numero_ospiti_effettivi

        self.db.commit()
        self.db.refresh(soggiorno)

        logger.info(f"Check-in executed for soggiorno {soggiorno_id}")

        return soggiorno

    def esegui_checkout(self, soggiorno_id: int) -> Soggiorno:
        """
        Execute check-out for a stay.

        Args:
            soggiorno_id: Stay ID

        Returns:
            Updated Soggiorno
        """
        soggiorno = self.db.query(Soggiorno).filter(
            Soggiorno.id == soggiorno_id
        ).first()

        if not soggiorno:
            raise ValueError(f"Soggiorno {soggiorno_id} non trovato")

        # Update status
        soggiorno.stato = StatoSoggiorno.CHECK_OUT_EFFETTUATO.value
        soggiorno.data_ora_checkout_effettivo = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(soggiorno)

        logger.info(f"Check-out executed for soggiorno {soggiorno_id}")

        return soggiorno

    def chiudi_soggiorno(self, soggiorno_id: int) -> Soggiorno:
        """
        Close a stay (archive after check-out).

        Args:
            soggiorno_id: Stay ID

        Returns:
            Updated Soggiorno
        """
        soggiorno = self.db.query(Soggiorno).filter(
            Soggiorno.id == soggiorno_id
        ).first()

        if not soggiorno:
            raise ValueError(f"Soggiorno {soggiorno_id} non trovato")

        soggiorno.stato = StatoSoggiorno.CHIUSO.value
        self.db.commit()
        self.db.refresh(soggiorno)

        logger.info(f"Soggiorno {soggiorno_id} closed")

        return soggiorno

    def get_soggiorni_che_richiedono_azione(self) -> List[Soggiorno]:
        """
        Get stays that require operator action.

        Returns stays where:
        - Check-in is today or past and data is incomplete
        - Police communication is pending
        - Notifiche non inviate
        """
        oggi = date.today()

        soggiorni = self.db.query(Soggiorno).filter(
            Soggiorno.valido == True,
            Soggiorno.stato.notin_([
                StatoSoggiorno.CHIUSO.value,
                StatoSoggiorno.ANNULLATO.value
            ]),
            or_(
                # Check-in today/past with incomplete data
                and_(
                    Soggiorno.data_checkin <= oggi,
                    Soggiorno.dati_ospiti_completi == False
                ),
                # Police communication pending
                Soggiorno.stato_polizia == StatoCompliance.IN_ATTESA.value,
                # Notification not sent for check-in today
                and_(
                    Soggiorno.data_checkin == oggi,
                    Soggiorno.notifica_checkin_inviata == False
                )
            )
        ).order_by(Soggiorno.data_checkin).all()

        return soggiorni

    def get_soggiorni_in_checkin_oggi(self) -> List[Soggiorno]:
        """Get stays with check-in today"""
        oggi = date.today()
        return self.db.query(Soggiorno).filter(
            Soggiorno.valido == True,
            Soggiorno.data_checkin == oggi,
            Soggiorno.stato.notin_([
                StatoSoggiorno.CHECK_IN_EFFETTUATO.value,
                StatoSoggiorno.IN_CORSO.value,
                StatoSoggiorno.CHECK_OUT_EFFETTUATO.value,
                StatoSoggiorno.CHIUSO.value,
                StatoSoggiorno.ANNULLATO.value
            ])
        ).all()

    def get_soggiorni_in_checkout_oggi(self) -> List[Soggiorno]:
        """Get stays with check-out today"""
        oggi = date.today()
        return self.db.query(Soggiorno).filter(
            Soggiorno.valido == True,
            Soggiorno.data_checkout == oggi,
            Soggiorno.stato.in_([
                StatoSoggiorno.CHECK_IN_EFFETTUATO.value,
                StatoSoggiorno.IN_CORSO.value
            ])
        ).all()

    def get_soggiorno_by_token(self, token: str) -> Optional[Soggiorno]:
        """Get soggiorno by self-service token"""
        return self.db.query(Soggiorno).filter(
            Soggiorno.token_self_service == token,
            Soggiorno.scadenza_token >= datetime.now(timezone.utc)
        ).first()

    def verifica_completezza_dati_polizia(self, soggiorno_id: int) -> Dict:
        """
        Verify if all data required for police communication is complete.

        Returns:
            Dict with completezza status and missing fields
        """
        soggiorno = self.db.query(Soggiorno).filter(
            Soggiorno.id == soggiorno_id
        ).first()

        if not soggiorno:
            raise ValueError(f"Soggiorno {soggiorno_id} non trovato")

        result = {
            "completo": False,
            "ospiti_registrati": soggiorno.numero_ospiti_registrati,
            "ospiti_previsti": soggiorno.numero_ospiti_previsti,
            "mancanti": []
        }

        if soggiorno.numero_ospiti_registrati < soggiorno.numero_ospiti_previsti:
            result["mancanti"].append(f"Mancano {soggiorno.numero_ospiti_previsti - soggiorno.numero_ospiti_registrati} ospiti")

        for ospite in soggiorno.ospiti:
            if not ospite.dati_completi_per_polizia:
                campi = []
                if not ospite.cognome:
                    campi.append("cognome")
                if not ospite.nome:
                    campi.append("nome")
                if not ospite.data_nascita:
                    campi.append("data_nascita")
                if not ospite.cittadinanza:
                    campi.append("cittadinanza")
                if ospite.eta >= 14:
                    if not ospite.tipo_documento:
                        campi.append("tipo_documento")
                    if not ospite.numero_documento:
                        campi.append("numero_documento")

                if campi:
                    result["mancanti"].append(f"Ospite {ospite.nome_completo}: {', '.join(campi)}")

        result["completo"] = len(result["mancanti"]) == 0

        # Update soggiorno status if complete
        if result["completo"]:
            soggiorno.dati_ospiti_completi = True
            # Update comunicazione to ready
            for com in soggiorno.comunicazioni:
                if com.tipo == TipoComunicazione.POLIZIA.value and com.stato == StatoComunicazione.DA_PREPARARE.value:
                    com.stato = StatoComunicazione.PRONTA.value
            self.db.commit()

        return result

    def invia_sollecito(self, soggiorno_id: int) -> bool:
        """
        Send a reminder for data collection.

        Updates solleciti_inviati counter and ultimo_sollecito timestamp.

        Returns:
            True if sollecito was sent (placeholder)
        """
        soggiorno = self.db.query(Soggiorno).filter(
            Soggiorno.id == soggiorno_id
        ).first()

        if not soggiorno:
            raise ValueError(f"Soggiorno {soggiorno_id} non trovato")

        soggiorno.solleciti_inviati += 1
        soggiorno.ultimo_sollecito = datetime.now(timezone.utc)
        self.db.commit()

        logger.info(f"Sollecito #{soggiorno.solleciti_inviati} sent for soggiorno {soggiorno_id}")

        # TODO: Integrate with notification service
        return True
