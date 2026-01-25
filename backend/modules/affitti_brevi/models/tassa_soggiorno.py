"""
TassaSoggiorno Model - Calculated Tourist Tax for a Stay

Stores the calculated tourist tax amount for a specific Soggiorno.
Tracks the calculation breakdown, exemptions, and payment status.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class StatoPagamentoTassa(str, enum.Enum):
    """Tax payment status"""
    NON_CALCOLATA = "NON_CALCOLATA"      # Not calculated yet
    CALCOLATA = "CALCOLATA"              # Calculated, awaiting payment
    PAGATA = "PAGATA"                    # Paid by guest
    ESENTE = "ESENTE"                    # Fully exempt
    VERSATA = "VERSATA"                  # Paid to municipality
    ANNULLATA = "ANNULLATA"              # Cancelled


class TassaSoggiorno(Base):
    """
    Calculated Tourist Tax for a Stay

    Stores the tourist tax calculation result for a specific stay.
    Created when Soggiorno data is complete and tax can be calculated.
    """
    __tablename__ = "ab_tasse_soggiorni"

    id = Column(Integer, primary_key=True, index=True)

    # Link to stay
    soggiorno_id = Column(
        Integer,
        ForeignKey("ab_soggiorni.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Configuration used for calculation
    config_id = Column(
        Integer,
        ForeignKey("ab_tasse_soggiorno_config.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Calculated amounts
    importo_totale = Column(Numeric(10, 2), nullable=False, default=0,
                           comment="Total tax amount due")
    importo_pagato = Column(Numeric(10, 2), nullable=True, default=0,
                           comment="Amount actually paid")

    # Calculation details
    numero_notti_totali = Column(Integer, nullable=False, default=0)
    numero_notti_tassabili = Column(Integer, nullable=False, default=0,
                                   comment="Taxable nights (after max nights rule)")
    numero_ospiti_totali = Column(Integer, nullable=False, default=0)
    numero_ospiti_tassabili = Column(Integer, nullable=False, default=0,
                                    comment="Taxable guests (after exemptions)")
    numero_ospiti_esenti = Column(Integer, nullable=False, default=0)

    # Calculation breakdown (JSON)
    dettaglio_calcolo = Column(Text, nullable=True,
                              comment="JSON with calculation breakdown")
    # Example dettaglio_calcolo:
    # {
    #   "tipo_calcolo": "FISSO",
    #   "importo_notte_persona": 2.50,
    #   "ospiti": [
    #     {"nome": "Mario Rossi", "notti": 3, "esente": false, "importo": 7.50},
    #     {"nome": "Bambino Rossi", "notti": 3, "esente": true, "motivo": "Minore", "importo": 0}
    #   ],
    #   "totale": 7.50
    # }

    # Exemptions detail (JSON)
    dettaglio_esenzioni = Column(Text, nullable=True,
                                comment="JSON with exemption details per guest")

    # Payment status
    stato = Column(String(30), default=StatoPagamentoTassa.NON_CALCOLATA.value,
                  nullable=False, index=True)
    data_calcolo = Column(DateTime(timezone=True), nullable=True)
    data_pagamento = Column(DateTime(timezone=True), nullable=True)
    data_versamento = Column(DateTime(timezone=True), nullable=True,
                            comment="Date paid to municipality")

    # Payment details
    metodo_pagamento = Column(String(50), nullable=True,
                             comment="CONTANTI, CARTA, BONIFICO, etc.")
    ricevuta_numero = Column(String(100), nullable=True)
    ricevuta_data = Column(DateTime(timezone=True), nullable=True)

    # Manual override
    importo_manuale = Column(Numeric(10, 2), nullable=True,
                            comment="Manual override amount")
    motivo_override = Column(Text, nullable=True,
                            comment="Reason for manual override")
    override_da_utente = Column(String(100), nullable=True,
                               comment="User who applied override")

    # Notes
    note = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    soggiorno = relationship(
        "Soggiorno",
        back_populates="tassa_soggiorno"
    )
    config = relationship(
        "TassaSoggiornoConfig"
    )

    def __repr__(self):
        return f"<TassaSoggiorno(id={self.id}, soggiorno={self.soggiorno_id}, importo={self.importo_totale})>"

    @property
    def importo_effettivo(self) -> 'Decimal':
        """Get effective amount (manual override or calculated)"""
        if self.importo_manuale is not None:
            return self.importo_manuale
        return self.importo_totale

    @property
    def importo_residuo(self) -> 'Decimal':
        """Get remaining amount to pay"""
        from decimal import Decimal
        pagato = self.importo_pagato or Decimal(0)
        return self.importo_effettivo - pagato

    @property
    def is_pagata(self) -> bool:
        """Check if tax is fully paid"""
        return self.stato in [
            StatoPagamentoTassa.PAGATA.value,
            StatoPagamentoTassa.VERSATA.value,
            StatoPagamentoTassa.ESENTE.value
        ]

    def get_dettaglio_calcolo(self) -> dict:
        """Parse calculation detail JSON"""
        if not self.dettaglio_calcolo:
            return {}
        import json
        try:
            return json.loads(self.dettaglio_calcolo)
        except:
            return {}

    def set_dettaglio_calcolo(self, detail: dict):
        """Set calculation detail from dict"""
        import json
        self.dettaglio_calcolo = json.dumps(detail, default=str)

    def mark_pagata(self, metodo: str = None, ricevuta_numero: str = None):
        """Mark tax as paid"""
        from datetime import datetime, timezone
        self.stato = StatoPagamentoTassa.PAGATA.value
        self.data_pagamento = datetime.now(timezone.utc)
        self.importo_pagato = self.importo_effettivo
        if metodo:
            self.metodo_pagamento = metodo
        if ricevuta_numero:
            self.ricevuta_numero = ricevuta_numero
            self.ricevuta_data = datetime.now(timezone.utc)

    def mark_versata(self):
        """Mark tax as paid to municipality"""
        from datetime import datetime, timezone
        self.stato = StatoPagamentoTassa.VERSATA.value
        self.data_versamento = datetime.now(timezone.utc)
