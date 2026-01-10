"""
ComunicazionePolizia Model - Police Communication Tracking

Tracks communications to Police (Alloggiati Web) for short-term rental guests.
Italian law requires reporting guests within 24 hours of check-in.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

# Add modules directory to path for cross-module imports
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)


class StatoComunicazione(str, enum.Enum):
    """Communication status"""
    DA_INVIARE = "DA_INVIARE"              # To be sent
    IN_PREPARAZIONE = "IN_PREPARAZIONE"    # Being prepared
    INVIATA = "INVIATA"                    # Sent
    CONFERMATA = "CONFERMATA"              # Confirmed by police system
    ERRORE = "ERRORE"                      # Error during submission


class MetodoInvio(str, enum.Enum):
    """Submission method"""
    ALLOGGIATI_WEB = "ALLOGGIATI_WEB"      # Alloggiati Web portal
    SCHEDINE_CARTACEE = "SCHEDINE_CARTACEE" # Paper forms (deprecated)
    API = "API"                            # API integration (if available)
    ALTRO = "ALTRO"                        # Other method


class ComunicazionePolizia(Base):
    """
    Police Communication Tracking

    Tracks guest communications to Police for legal compliance.
    Required within 24 hours of check-in for all guests.
    """
    __tablename__ = "comunicazioni_polizia"

    id = Column(Integer, primary_key=True, index=True)

    # Link to booking
    prenotazione_id = Column(Integer, ForeignKey("prenotazioni.id"),
                            nullable=False, index=True,
                            comment="Prenotazione per cui si comunica")

    # Communication details
    stato = Column(SQLEnum(StatoComunicazione),
                  default=StatoComunicazione.DA_INVIARE,
                  nullable=False, index=True)
    metodo_invio = Column(SQLEnum(MetodoInvio), nullable=True,
                         comment="Metodo utilizzato per l'invio")

    # Submission tracking
    data_invio = Column(DateTime(timezone=True), nullable=True, index=True,
                       comment="Data e ora invio comunicazione")
    data_conferma = Column(DateTime(timezone=True), nullable=True,
                          comment="Data e ora conferma da sistema polizia")

    # Reference numbers
    numero_ricevuta = Column(String(100), nullable=True,
                            comment="Numero ricevuta/protocollo dal sistema polizia")
    codice_struttura = Column(String(50), nullable=True,
                              comment="Codice struttura ricettiva")

    # Guest data summary (JSON for flexibility)
    dati_ospiti = Column(JSON, nullable=True,
                        comment="Riepilogo dati ospiti comunicati")

    # Example dati_ospiti structure:
    # {
    #   "numero_ospiti": 2,
    #   "ospiti": [
    #     {
    #       "cognome": "Rossi",
    #       "nome": "Mario",
    #       "data_nascita": "1980-05-15",
    #       "luogo_nascita": "Roma",
    #       "tipo_documento": "CI",
    #       "numero_documento": "AB123456"
    #     }
    #   ]
    # }

    # Error tracking
    errore_messaggio = Column(Text, nullable=True,
                             comment="Messaggio di errore se stato=ERRORE")
    tentativi_invio = Column(Integer, default=0, nullable=False,
                            comment="Numero di tentativi di invio")

    # Notes
    note = Column(Text, nullable=True,
                 comment="Note libere sulla comunicazione")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    prenotazione = relationship("Prenotazione", back_populates="comunicazioni_polizia")

    def __repr__(self):
        return f"<ComunicazionePolizia(id={self.id}, prenotazione_id={self.prenotazione_id}, stato={self.stato.value})>"

    @property
    def is_invio_scaduto(self):
        """Check if 24h deadline has passed"""
        from datetime import datetime, timezone, timedelta
        if self.stato in [StatoComunicazione.INVIATA, StatoComunicazione.CONFERMATA]:
            return False

        # Get check-in date from prenotazione
        if not self.prenotazione:
            return False

        checkin = self.prenotazione.data_checkin
        # Convert date to datetime at midnight
        from datetime import datetime as dt
        checkin_datetime = dt.combine(checkin, dt.min.time()).replace(tzinfo=timezone.utc)
        deadline = checkin_datetime + timedelta(hours=24)

        return datetime.now(timezone.utc) > deadline

    @property
    def ore_rimanenti(self):
        """Calculate hours remaining until 24h deadline"""
        from datetime import datetime, timezone, timedelta
        if self.stato in [StatoComunicazione.INVIATA, StatoComunicazione.CONFERMATA]:
            return None

        if not self.prenotazione:
            return None

        checkin = self.prenotazione.data_checkin
        from datetime import datetime as dt
        checkin_datetime = dt.combine(checkin, dt.min.time()).replace(tzinfo=timezone.utc)
        deadline = checkin_datetime + timedelta(hours=24)

        now = datetime.now(timezone.utc)
        if now > deadline:
            return 0

        delta = deadline - now
        return delta.total_seconds() / 3600  # Convert to hours

    def mark_sent(self, metodo: MetodoInvio, numero_ricevuta: str = None):
        """Mark communication as sent"""
        from datetime import datetime, timezone
        self.stato = StatoComunicazione.INVIATA
        self.metodo_invio = metodo
        self.data_invio = datetime.now(timezone.utc)
        self.numero_ricevuta = numero_ricevuta
        self.tentativi_invio += 1

    def mark_confirmed(self):
        """Mark communication as confirmed by police system"""
        from datetime import datetime, timezone
        self.stato = StatoComunicazione.CONFERMATA
        self.data_conferma = datetime.now(timezone.utc)

    def mark_error(self, errore_messaggio: str):
        """Mark communication as error"""
        self.stato = StatoComunicazione.ERRORE
        self.errore_messaggio = errore_messaggio
        self.tentativi_invio += 1
