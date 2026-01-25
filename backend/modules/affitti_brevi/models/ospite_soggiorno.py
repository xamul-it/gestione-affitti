"""
OspiteSoggiorno Model - Guest linked to Operational Stay

Represents a guest staying during a Soggiorno.
Contains personal data required for:
- Police communication (Alloggiati Web)
- Tourist tax calculation (age-based exemptions)
- ISTAT reporting

Each Soggiorno has one or more OspiteSoggiorno records.
One guest is marked as 'principale' (primary contact).
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class RuoloOspite(str, enum.Enum):
    """Guest role in the stay"""
    PRINCIPALE = "PRINCIPALE"       # Primary guest (booking contact)
    ACCOMPAGNATORE = "ACCOMPAGNATORE"  # Accompanying guest
    MINORE = "MINORE"               # Minor (child)


class StatoDocumento(str, enum.Enum):
    """Document verification status"""
    NON_INSERITO = "NON_INSERITO"       # Not entered
    IN_ATTESA = "IN_ATTESA"             # Waiting for verification
    VERIFICATO = "VERIFICATO"           # Verified
    SCADUTO = "SCADUTO"                 # Expired
    NON_VALIDO = "NON_VALIDO"           # Invalid


class OspiteSoggiorno(Base):
    """
    Guest linked to Operational Stay

    Stores guest personal data required for:
    - Police communication (mandatory within 24h of check-in)
    - Tourist tax exemptions (based on age)
    - ISTAT reporting

    Data fields follow Italian Police requirements (Alloggiati Web).
    """
    __tablename__ = "ab_ospiti_soggiorni"

    id = Column(Integer, primary_key=True, index=True)

    # Link to stay
    soggiorno_id = Column(
        Integer,
        ForeignKey("ab_soggiorni.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Optional link to existing SoggettoAnagrafico (if guest is already in registry)
    soggetto_anagrafico_id = Column(
        Integer,
        ForeignKey("anag_soggetti_anagrafici.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Link to registry if guest exists"
    )

    # Role in the stay
    ruolo = Column(String(30), default=RuoloOspite.ACCOMPAGNATORE.value,
                  nullable=False)
    principale = Column(Boolean, default=False, nullable=False,
                       comment="True if this is the primary guest")

    # Personal data (required for Police communication)
    cognome = Column(String(100), nullable=False)
    nome = Column(String(100), nullable=False)
    sesso = Column(String(1), nullable=True, comment="M/F")
    data_nascita = Column(Date, nullable=False)
    luogo_nascita = Column(String(200), nullable=True,
                          comment="City/place of birth")
    provincia_nascita = Column(String(2), nullable=True,
                              comment="Province code (IT) or EE for foreign")
    stato_nascita = Column(String(100), nullable=True,
                          comment="Country of birth")
    cittadinanza = Column(String(100), nullable=False, default="ITALIANA")

    # Residence
    indirizzo_residenza = Column(String(300), nullable=True)
    comune_residenza = Column(String(100), nullable=True)
    provincia_residenza = Column(String(2), nullable=True)
    stato_residenza = Column(String(100), nullable=True, default="ITALIA")

    # Contact info
    email = Column(String(200), nullable=True)
    telefono = Column(String(50), nullable=True)

    # Identity document (required for Police)
    tipo_documento = Column(String(50), nullable=True,
                           comment="CARTA_IDENTITA, PASSAPORTO, PATENTE, etc.")
    numero_documento = Column(String(50), nullable=True)
    ente_rilascio = Column(String(100), nullable=True,
                          comment="Issuing authority")
    data_rilascio = Column(Date, nullable=True)
    data_scadenza = Column(Date, nullable=True)
    stato_rilascio = Column(String(100), nullable=True,
                           comment="Country that issued the document")

    # Document verification
    stato_documento = Column(String(30), default=StatoDocumento.NON_INSERITO.value,
                            nullable=False)
    documento_verificato = Column(Boolean, default=False, nullable=False)
    file_documento_path = Column(String(500), nullable=True,
                                comment="Path to document scan/photo")
    note_documento = Column(Text, nullable=True)

    # Tourist tax exemption
    esente_tassa = Column(Boolean, default=False, nullable=False)
    motivo_esenzione = Column(String(100), nullable=True,
                             comment="Reason for tax exemption")

    # Privacy consent
    consenso_privacy = Column(Boolean, default=False, nullable=False)
    data_consenso_privacy = Column(DateTime(timezone=True), nullable=True)

    # Self-service data entry tracking
    inserito_da_ospite = Column(Boolean, default=False, nullable=False,
                               comment="True if data entered by guest via self-service")
    data_inserimento_ospite = Column(DateTime(timezone=True), nullable=True)

    # Notes
    note = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    soggiorno = relationship(
        "Soggiorno",
        back_populates="ospiti"
    )
    soggetto_anagrafico = relationship(
        "SoggettoAnagrafico",
        foreign_keys=[soggetto_anagrafico_id]
    )

    # Indexes
    __table_args__ = (
        Index('ix_ab_ospiti_soggiorno_soggetto',
              'soggiorno_id', 'soggetto_anagrafico_id'),
    )

    def __repr__(self):
        return f"<OspiteSoggiorno(id={self.id}, soggiorno={self.soggiorno_id}, nome={self.nome} {self.cognome})>"

    @property
    def nome_completo(self) -> str:
        """Full name"""
        return f"{self.cognome} {self.nome}"

    @property
    def eta(self) -> int:
        """Calculate age at time of stay"""
        from datetime import date
        if not self.data_nascita:
            return 0

        # Get check-in date from soggiorno if available
        if self.soggiorno:
            reference_date = self.soggiorno.data_checkin
        else:
            reference_date = date.today()

        age = reference_date.year - self.data_nascita.year
        if (reference_date.month, reference_date.day) < (self.data_nascita.month, self.data_nascita.day):
            age -= 1
        return age

    @property
    def is_minore(self) -> bool:
        """Check if guest is a minor (under 18)"""
        return self.eta < 18

    @property
    def is_documento_valido(self) -> bool:
        """Check if document is valid"""
        if self.stato_documento != StatoDocumento.VERIFICATO.value:
            return False

        if self.data_scadenza:
            from datetime import date
            return self.data_scadenza >= date.today()

        return True

    @property
    def dati_completi_per_polizia(self) -> bool:
        """Check if all data required for Police communication is present"""
        required_fields = [
            self.cognome,
            self.nome,
            self.data_nascita,
            self.cittadinanza,
        ]

        # Document required for adults (and some minors depending on age)
        if self.eta >= 14:
            required_fields.extend([
                self.tipo_documento,
                self.numero_documento,
            ])

        return all(required_fields)

    def calcola_esenzione_tassa(self, eta_minima: int = 0, eta_massima: int = None) -> bool:
        """
        Calculate if guest is exempt from tourist tax based on age

        Args:
            eta_minima: Minimum age subject to tax (children under are exempt)
            eta_massima: Maximum age subject to tax (elderly over are exempt)

        Returns:
            True if guest is exempt
        """
        if self.eta < eta_minima:
            self.esente_tassa = True
            self.motivo_esenzione = f"Minore di {eta_minima} anni"
            return True

        if eta_massima and self.eta > eta_massima:
            self.esente_tassa = True
            self.motivo_esenzione = f"Over {eta_massima} anni"
            return True

        self.esente_tassa = False
        self.motivo_esenzione = None
        return False

    def to_alloggiati_dict(self) -> dict:
        """
        Convert to dictionary format for Alloggiati Web submission

        Returns format compliant with Italian Police requirements.
        """
        return {
            "cognome": self.cognome,
            "nome": self.nome,
            "sesso": self.sesso,
            "data_nascita": self.data_nascita.isoformat() if self.data_nascita else None,
            "luogo_nascita": self.luogo_nascita,
            "provincia_nascita": self.provincia_nascita,
            "stato_nascita": self.stato_nascita,
            "cittadinanza": self.cittadinanza,
            "tipo_documento": self.tipo_documento,
            "numero_documento": self.numero_documento,
            "data_rilascio": self.data_rilascio.isoformat() if self.data_rilascio else None,
            "luogo_rilascio": self.ente_rilascio,
            "tipo_alloggiato": "OSPITE_SINGOLO" if self.principale else "FAMILIARE",
        }
