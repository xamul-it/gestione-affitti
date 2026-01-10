"""
Comunicazione Polizia Service

Helper service for managing police communications (Alloggiati Web).
Handles creation, submission tracking, and guest data preparation.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

# Add modules directory to path for cross-module imports
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

from affitti_brevi.models import (
    ComunicazionePolizia,
    StatoComunicazione,
    MetodoInvio,
    Prenotazione,
    OspitePrenotazione
)
from affitti_brevi.services.scadenza_generator import ScadenzaGenerator

logger = logging.getLogger(__name__)


class ComunicazionePoliziaService:
    """
    Police Communication Service

    Manages police communications for short-term rentals.
    """

    def __init__(self, db: Session):
        self.db = db
        self.scadenza_generator = ScadenzaGenerator(db)

    def create_for_booking(self, prenotazione_id: int) -> ComunicazionePolizia:
        """
        Create police communication for a booking

        Args:
            prenotazione_id: ID of booking

        Returns:
            Created ComunicazionePolizia

        Raises:
            ValueError: If booking not found or communication already exists
        """
        # Verify booking exists
        prenotazione = self.db.query(Prenotazione).filter(
            Prenotazione.id == prenotazione_id
        ).first()

        if not prenotazione:
            raise ValueError(f"Prenotazione {prenotazione_id} not found")

        # Check if communication already exists
        existing = self.db.query(ComunicazionePolizia).filter(
            ComunicazionePolizia.prenotazione_id == prenotazione_id
        ).first()

        if existing:
            raise ValueError(f"Communication already exists for booking {prenotazione_id}")

        # Create communication
        comunicazione = ComunicazionePolizia(
            prenotazione_id=prenotazione_id,
            stato=StatoComunicazione.DA_INVIARE,
            tentativi_invio=0
        )

        self.db.add(comunicazione)
        self.db.commit()
        self.db.refresh(comunicazione)

        logger.info(f"Police communication created for booking {prenotazione_id}")
        return comunicazione

    def prepare_guest_data(self, prenotazione_id: int) -> Dict[str, Any]:
        """
        Prepare guest data for police communication

        Extracts guest information from OspitePrenotazione records.

        Args:
            prenotazione_id: ID of booking

        Returns:
            Dict with guest data ready for submission
        """
        # Get booking
        prenotazione = self.db.query(Prenotazione).filter(
            Prenotazione.id == prenotazione_id
        ).first()

        if not prenotazione:
            raise ValueError(f"Prenotazione {prenotazione_id} not found")

        # Get guests
        ospiti = self.db.query(OspitePrenotazione).filter(
            OspitePrenotazione.prenotazione_id == prenotazione_id
        ).all()

        # Prepare data
        dati_ospiti = {
            "numero_ospiti": len(ospiti),
            "ospiti": []
        }

        for ospite in ospiti:
            # Get anagrafica data if available
            soggetto = ospite.soggetto_anagrafico if ospite.soggetto_anagrafico else None

            ospite_data = {
                "cognome": ospite.cognome,
                "nome": ospite.nome,
                "data_nascita": ospite.data_nascita.isoformat() if ospite.data_nascita else None,
                "luogo_nascita": soggetto.luogo_nascita if soggetto else None,
                "tipo_documento": ospite.tipo_documento,
                "numero_documento": ospite.numero_documento,
                "data_rilascio_documento": ospite.data_rilascio_documento.isoformat() if ospite.data_rilascio_documento else None,
                "luogo_rilascio_documento": ospite.luogo_rilascio_documento,
            }

            dati_ospiti["ospiti"].append(ospite_data)

        return dati_ospiti

    def mark_sent(
        self,
        comunicazione_id: int,
        metodo: MetodoInvio,
        numero_ricevuta: Optional[str] = None,
        codice_struttura: Optional[str] = None
    ) -> ComunicazionePolizia:
        """
        Mark communication as sent

        Also marks the associated deadline as completed.

        Args:
            comunicazione_id: ID of communication
            metodo: Method used to send
            numero_ricevuta: Receipt/protocol number from police system
            codice_struttura: Property code

        Returns:
            Updated ComunicazionePolizia

        Raises:
            ValueError: If communication not found
        """
        comunicazione = self.db.query(ComunicazionePolizia).filter(
            ComunicazionePolizia.id == comunicazione_id
        ).first()

        if not comunicazione:
            raise ValueError(f"Communication {comunicazione_id} not found")

        # Mark as sent
        comunicazione.mark_sent(metodo, numero_ricevuta)
        if codice_struttura:
            comunicazione.codice_struttura = codice_struttura

        # Prepare guest data if not already done
        if not comunicazione.dati_ospiti:
            try:
                comunicazione.dati_ospiti = self.prepare_guest_data(comunicazione.prenotazione_id)
            except Exception as e:
                logger.warning(f"Could not prepare guest data: {str(e)}")

        self.db.commit()
        self.db.refresh(comunicazione)

        # Mark deadline as completed
        note = f"Comunicazione inviata tramite {metodo.value}"
        if numero_ricevuta:
            note += f" - Ricevuta: {numero_ricevuta}"

        self.scadenza_generator.mark_police_deadline_completed(
            comunicazione.prenotazione_id,
            note=note
        )

        logger.info(f"Communication {comunicazione_id} marked as sent via {metodo.value}")
        return comunicazione

    def mark_confirmed(self, comunicazione_id: int) -> ComunicazionePolizia:
        """
        Mark communication as confirmed by police system

        Args:
            comunicazione_id: ID of communication

        Returns:
            Updated ComunicazionePolizia

        Raises:
            ValueError: If communication not found
        """
        comunicazione = self.db.query(ComunicazionePolizia).filter(
            ComunicazionePolizia.id == comunicazione_id
        ).first()

        if not comunicazione:
            raise ValueError(f"Communication {comunicazione_id} not found")

        comunicazione.mark_confirmed()
        self.db.commit()
        self.db.refresh(comunicazione)

        logger.info(f"Communication {comunicazione_id} marked as confirmed")
        return comunicazione

    def mark_error(
        self,
        comunicazione_id: int,
        errore_messaggio: str
    ) -> ComunicazionePolizia:
        """
        Mark communication as error

        Args:
            comunicazione_id: ID of communication
            errore_messaggio: Error message

        Returns:
            Updated ComunicazionePolizia

        Raises:
            ValueError: If communication not found
        """
        comunicazione = self.db.query(ComunicazionePolizia).filter(
            ComunicazionePolizia.id == comunicazione_id
        ).first()

        if not comunicazione:
            raise ValueError(f"Communication {comunicazione_id} not found")

        comunicazione.mark_error(errore_messaggio)
        self.db.commit()
        self.db.refresh(comunicazione)

        logger.error(f"Communication {comunicazione_id} marked as error: {errore_messaggio}")
        return comunicazione

    def get_pending_communications(self) -> List[ComunicazionePolizia]:
        """
        Get all pending communications (not yet sent)

        Returns:
            List of pending communications
        """
        comunicazioni = self.db.query(ComunicazionePolizia).filter(
            ComunicazionePolizia.stato.in_([
                StatoComunicazione.DA_INVIARE,
                StatoComunicazione.IN_PREPARAZIONE
            ])
        ).order_by(ComunicazionePolizia.created_at).all()

        return comunicazioni

    def get_overdue_communications(self) -> List[ComunicazionePolizia]:
        """
        Get communications where 24h deadline has passed

        Returns:
            List of overdue communications
        """
        comunicazioni = self.db.query(ComunicazionePolizia).filter(
            ComunicazionePolizia.stato.in_([
                StatoComunicazione.DA_INVIARE,
                StatoComunicazione.IN_PREPARAZIONE,
                StatoComunicazione.ERRORE
            ])
        ).all()

        overdue = [c for c in comunicazioni if c.is_invio_scaduto]
        return overdue

    def get_by_booking(self, prenotazione_id: int) -> Optional[ComunicazionePolizia]:
        """
        Get communication for a specific booking

        Args:
            prenotazione_id: Booking ID

        Returns:
            ComunicazionePolizia or None
        """
        comunicazione = self.db.query(ComunicazionePolizia).filter(
            ComunicazionePolizia.prenotazione_id == prenotazione_id
        ).first()

        return comunicazione

    def retry_failed_communication(self, comunicazione_id: int) -> ComunicazionePolizia:
        """
        Reset failed communication for retry

        Args:
            comunicazione_id: ID of communication to retry

        Returns:
            Updated ComunicazionePolizia

        Raises:
            ValueError: If communication not found
        """
        comunicazione = self.db.query(ComunicazionePolizia).filter(
            ComunicazionePolizia.id == comunicazione_id
        ).first()

        if not comunicazione:
            raise ValueError(f"Communication {comunicazione_id} not found")

        # Reset to DA_INVIARE
        comunicazione.stato = StatoComunicazione.DA_INVIARE
        comunicazione.errore_messaggio = None

        self.db.commit()
        self.db.refresh(comunicazione)

        logger.info(f"Communication {comunicazione_id} reset for retry")
        return comunicazione
