"""
TassaSoggiornoConfig Model - Tourist Tax Municipality Configuration

Per-municipality configuration for tourist tax calculation.
Supports multiple calculation types:
- FISSO: Fixed amount per night per person
- PERCENTUALE: Percentage of nightly rate
- SCAGLIONI: Tiered rates based on number of nights
- CATEGORIA: Based on property classification

Includes exemption rules based on age and other criteria.
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TipoCalcoloTassa(str, enum.Enum):
    """Tourist tax calculation type"""
    FISSO = "FISSO"                    # Fixed amount per night per person
    PERCENTUALE = "PERCENTUALE"        # Percentage of nightly rate
    SCAGLIONI = "SCAGLIONI"           # Tiered rates by night count
    CATEGORIA = "CATEGORIA"            # Based on property classification (stars, etc.)


class TassaSoggiornoConfig(Base):
    """
    Tourist Tax Configuration by Municipality

    Stores tax calculation rules per municipality.
    Each municipality can have different rates and exemptions.
    Supports historical configurations with date ranges.
    """
    __tablename__ = "ab_tasse_soggiorno_config"

    id = Column(Integer, primary_key=True, index=True)

    # Municipality reference
    comune_id = Column(
        Integer,
        ForeignKey("public.anag_comuni_italia.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK to comuni_italia (null for custom/test config)"
    )
    comune_nome = Column(String(200), nullable=False,
                        comment="Municipality name for display")
    comune_codice = Column(String(20), nullable=True,
                          comment="ISTAT code or other identifier")
    regione = Column(String(100), nullable=True)
    provincia = Column(String(2), nullable=True)

    # Calculation type
    tipo_calcolo = Column(String(30), default=TipoCalcoloTassa.FISSO.value,
                         nullable=False)

    # Fixed amount calculation (tipo_calcolo = FISSO)
    importo_fisso = Column(Numeric(10, 2), nullable=True,
                          comment="Fixed amount per night per person (e.g., €2.50)")

    # Percentage calculation (tipo_calcolo = PERCENTUALE)
    percentuale = Column(Numeric(5, 2), nullable=True,
                        comment="Percentage of nightly rate (e.g., 5.00 for 5%)")
    importo_massimo_percentuale = Column(Numeric(10, 2), nullable=True,
                                        comment="Max amount when using percentage")

    # Note: Tiered rates are in separate TassaSoggiornoScaglione table

    # Exemptions - Age based
    eta_minima_soggetta = Column(Integer, nullable=True, default=0,
                                comment="Minimum age subject to tax (children under exempt)")
    eta_massima_soggetta = Column(Integer, nullable=True,
                                 comment="Maximum age subject to tax (elderly over exempt)")

    # Exemptions - Night limit
    notti_max_tassabili = Column(Integer, nullable=True,
                                comment="Max taxable nights (e.g., only first 7 nights)")

    # Exemptions - Categories (stored as JSON array)
    categorie_esenti = Column(Text, nullable=True,
                             comment="JSON array of exempt categories (e.g., ['MINORI', 'OVER_70', 'DISABILI'])")

    # Configuration validity period
    data_inizio_validita = Column(Date, nullable=False,
                                 comment="Configuration start date")
    data_fine_validita = Column(Date, nullable=True,
                               comment="Configuration end date (NULL = active)")

    # Payment info
    metodo_pagamento = Column(Text, nullable=True,
                             comment="Payment methods accepted")
    iban_comune = Column(String(50), nullable=True)
    causale_pagamento = Column(String(200), nullable=True)

    # Reporting requirements
    periodicita_dichiarazione = Column(String(30), nullable=True,
                                      comment="MENSILE, TRIMESTRALE, ANNUALE")
    giorno_scadenza = Column(Integer, nullable=True,
                            comment="Day of month/quarter for declaration deadline")

    # Status
    attiva = Column(Boolean, default=True, nullable=False)

    # Notes
    note = Column(Text, nullable=True,
                 comment="Municipal regulation notes, special exemptions, etc.")
    url_regolamento = Column(String(500), nullable=True,
                            comment="Link to official municipal regulation")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scaglioni = relationship(
        "TassaSoggiornoScaglione",
        back_populates="config",
        cascade="all, delete-orphan",
        order_by="TassaSoggiornoScaglione.notte_da"
    )

    # Indexes
    __table_args__ = (
        Index('ix_ab_tassa_config_comune_validita',
              'comune_id', 'data_inizio_validita', 'data_fine_validita'),
    )

    def __repr__(self):
        return f"<TassaSoggiornoConfig(id={self.id}, comune={self.comune_nome}, tipo={self.tipo_calcolo})>"

    def is_active_for_date(self, check_date: 'Date') -> bool:
        """Check if configuration is active for a given date"""
        if not self.attiva:
            return False
        if check_date < self.data_inizio_validita:
            return False
        if self.data_fine_validita and check_date > self.data_fine_validita:
            return False
        return True

    def get_categorie_esenti_list(self) -> list:
        """Parse categorie_esenti JSON to list"""
        if not self.categorie_esenti:
            return []
        import json
        try:
            return json.loads(self.categorie_esenti)
        except:
            return []

    def set_categorie_esenti_list(self, categories: list):
        """Set categorie_esenti from list"""
        import json
        self.categorie_esenti = json.dumps(categories)
