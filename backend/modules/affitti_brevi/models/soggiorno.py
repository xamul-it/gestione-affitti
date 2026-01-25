"""
Soggiorno Model - Operational Stay

The central operational entity for short-term rental management.
Created from a Prenotazione, tracks the actual stay with:
- Check-in/check-out status and times
- Guest data collection status
- Document verification status
- Tourist tax calculation
- Compliance status (Police, ISTAT)

This separation allows:
- Multiple bookings (from different channels) → one Soggiorno
- Independent operational tracking from booking source
- Conflict resolution (choose which booking is the "valid" one)
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class StatoSoggiorno(str, enum.Enum):
    """Operational stay status"""
    CREATO = "CREATO"                           # Created from booking
    IN_ATTESA_DATI = "IN_ATTESA_DATI"          # Waiting for guest data
    DATI_PARZIALI = "DATI_PARZIALI"            # Some guest data collected
    DATI_COMPLETI = "DATI_COMPLETI"            # All guest data collected
    CHECK_IN_EFFETTUATO = "CHECK_IN_EFFETTUATO"  # Guest checked in
    IN_CORSO = "IN_CORSO"                       # Stay in progress
    CHECK_OUT_EFFETTUATO = "CHECK_OUT_EFFETTUATO"  # Guest checked out
    CHIUSO = "CHIUSO"                           # Stay closed (post-checkout, archived)
    ANNULLATO = "ANNULLATO"                     # Cancelled (booking cancelled)


class StatoCompliance(str, enum.Enum):
    """Compliance status for mandatory communications"""
    NON_RICHIESTO = "NON_RICHIESTO"     # Not yet required
    IN_ATTESA = "IN_ATTESA"             # Required, waiting
    INCOMPLETO = "INCOMPLETO"           # Partial data sent
    COMPLETATO = "COMPLETATO"           # All communications sent
    ERRORE = "ERRORE"                   # Error in communication


class Soggiorno(Base):
    """
    Operational Stay

    Represents the actual stay of guests in a property.
    This is the operational entity used for:
    - Guest data collection and verification
    - Check-in / check-out management
    - Tourist tax calculation
    - Compliance with legal requirements (Police, ISTAT)

    Created automatically when a Prenotazione is confirmed.
    In case of booking conflicts, only one Soggiorno is marked as 'valido'.
    """
    __tablename__ = "ab_soggiorni"

    id = Column(Integer, primary_key=True, index=True)

    # Link to booking
    prenotazione_id = Column(
        Integer,
        ForeignKey("ab_prenotazioni.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Property (denormalized for query convenience)
    unita_immobiliare_id = Column(
        Integer,
        ForeignKey("immo_unita_immobiliari.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Stay dates (can differ from booking if modified)
    data_checkin = Column(Date, nullable=False, index=True)
    data_checkout = Column(Date, nullable=False, index=True)
    ora_checkin_prevista = Column(String(5), nullable=True, default="15:00",
                                 comment="Expected check-in time (HH:MM)")
    ora_checkout_prevista = Column(String(5), nullable=True, default="10:00",
                                  comment="Expected check-out time (HH:MM)")

    # Actual check-in/out timestamps
    data_ora_checkin_effettivo = Column(DateTime(timezone=True), nullable=True)
    data_ora_checkout_effettivo = Column(DateTime(timezone=True), nullable=True)

    # Guest count
    numero_ospiti_previsti = Column(Integer, nullable=False, default=1)
    numero_ospiti_effettivi = Column(Integer, nullable=True,
                                    comment="Actual number of guests (after check-in)")

    # Operational status
    stato = Column(String(30), default=StatoSoggiorno.CREATO.value,
                  nullable=False, index=True)
    valido = Column(Boolean, default=True, nullable=False,
                   comment="False if this is a conflicting booking to be ignored")

    # Data collection status
    dati_ospiti_completi = Column(Boolean, default=False, nullable=False)
    documenti_completi = Column(Boolean, default=False, nullable=False)
    numero_ospiti_registrati = Column(Integer, default=0, nullable=False)

    # Compliance status
    stato_polizia = Column(String(30), default=StatoCompliance.NON_RICHIESTO.value,
                          nullable=False, index=True)
    stato_istat = Column(String(30), default=StatoCompliance.NON_RICHIESTO.value,
                        nullable=False)
    stato_tassa_soggiorno = Column(String(30), default=StatoCompliance.NON_RICHIESTO.value,
                                  nullable=False)

    # Notifications
    notifica_checkin_inviata = Column(Boolean, default=False, nullable=False)
    notifica_dati_inviata = Column(Boolean, default=False, nullable=False)
    solleciti_inviati = Column(Integer, default=0, nullable=False)
    ultimo_sollecito = Column(DateTime(timezone=True), nullable=True)

    # Self-service link for guest data collection
    token_self_service = Column(String(100), nullable=True, unique=True,
                               comment="Token for guest self-service data entry")
    scadenza_token = Column(DateTime(timezone=True), nullable=True)

    # Notes
    note_operative = Column(Text, nullable=True,
                           comment="Operational notes for staff")
    note_ospite = Column(Text, nullable=True,
                        comment="Notes from guest")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    prenotazione = relationship(
        "Prenotazione",
        back_populates="soggiorno"
    )
    unita_immobiliare = relationship(
        "UnitaImmobiliare",
        foreign_keys=[unita_immobiliare_id]
    )
    ospiti = relationship(
        "OspiteSoggiorno",
        back_populates="soggiorno",
        cascade="all, delete-orphan"
    )
    tassa_soggiorno = relationship(
        "TassaSoggiorno",
        back_populates="soggiorno",
        uselist=False
    )
    comunicazioni = relationship(
        "Comunicazione",
        back_populates="soggiorno",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index('ix_ab_soggiorni_immobile_date',
              'unita_immobiliare_id', 'data_checkin', 'data_checkout'),
        Index('ix_ab_soggiorni_stato_date',
              'stato', 'data_checkin'),
        Index('ix_ab_soggiorni_compliance',
              'stato_polizia', 'data_checkin'),
    )

    def __repr__(self):
        return f"<Soggiorno(id={self.id}, prenotazione={self.prenotazione_id}, stato={self.stato})>"

    @property
    def notti(self) -> int:
        """Calculate number of nights"""
        if self.data_checkin and self.data_checkout:
            return (self.data_checkout - self.data_checkin).days
        return 0

    @property
    def is_in_corso(self) -> bool:
        """Check if stay is currently in progress"""
        from datetime import date
        today = date.today()
        return (
            self.valido and
            self.stato not in [StatoSoggiorno.ANNULLATO.value, StatoSoggiorno.CHIUSO.value] and
            self.data_checkin <= today <= self.data_checkout
        )

    @property
    def is_futuro(self) -> bool:
        """Check if stay is in the future"""
        from datetime import date
        return self.valido and self.data_checkin > date.today()

    @property
    def is_passato(self) -> bool:
        """Check if stay is in the past"""
        from datetime import date
        return self.data_checkout < date.today()

    @property
    def richiede_azione(self) -> bool:
        """Check if this stay requires operator action"""
        if not self.valido:
            return False
        if self.stato == StatoSoggiorno.ANNULLATO.value:
            return False

        # Requires action if:
        # - Missing guest data and check-in is approaching
        # - Police communication pending and deadline approaching
        # - Check-in expected today
        from datetime import date
        today = date.today()

        if self.data_checkin <= today and not self.dati_ospiti_completi:
            return True

        if self.stato_polizia == StatoCompliance.IN_ATTESA.value:
            return True

        if self.data_checkin == today and self.stato in [
            StatoSoggiorno.CREATO.value,
            StatoSoggiorno.IN_ATTESA_DATI.value,
            StatoSoggiorno.DATI_PARZIALI.value
        ]:
            return True

        return False

    def genera_token_self_service(self):
        """Generate a self-service token for guest data entry"""
        import secrets
        from datetime import datetime, timezone, timedelta

        self.token_self_service = secrets.token_urlsafe(32)
        # Token valid until check-out + 1 day
        self.scadenza_token = datetime.combine(
            self.data_checkout,
            datetime.max.time()
        ).replace(tzinfo=timezone.utc) + timedelta(days=1)

        return self.token_self_service

    def aggiorna_stato_dati(self):
        """Update data collection status based on registered guests"""
        if self.numero_ospiti_registrati == 0:
            self.dati_ospiti_completi = False
            self.documenti_completi = False
        elif self.numero_ospiti_registrati < self.numero_ospiti_previsti:
            self.dati_ospiti_completi = False
        else:
            self.dati_ospiti_completi = True
            # Check documents
            if self.ospiti:
                self.documenti_completi = all(o.documento_verificato for o in self.ospiti)

        # Update stato
        if self.stato in [StatoSoggiorno.CREATO.value, StatoSoggiorno.IN_ATTESA_DATI.value]:
            if self.dati_ospiti_completi and self.documenti_completi:
                self.stato = StatoSoggiorno.DATI_COMPLETI.value
            elif self.numero_ospiti_registrati > 0:
                self.stato = StatoSoggiorno.DATI_PARZIALI.value
            else:
                self.stato = StatoSoggiorno.IN_ATTESA_DATI.value
