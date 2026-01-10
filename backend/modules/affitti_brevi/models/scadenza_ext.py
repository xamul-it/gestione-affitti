"""
ScadenzaAffittiBrevi Extension Model

Extension table for affitti_brevi-specific scadenza metadata.
Links to core.scadenze via FK and adds module-specific fields.

This follows the platform pattern: use core models with optional extensions.
"""
from sqlalchemy import Column, Integer, String, Date, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class TipoScadenzaAffittiBrevi(str, enum.Enum):
    """Affitti Brevi specific deadline types"""
    COMUNICAZIONE_POLIZIA = "COMUNICAZIONE_POLIZIA"  # Police communication (within 24h)
    REPORT_ISTAT = "REPORT_ISTAT"                    # ISTAT monthly report
    ALTRO = "ALTRO"                                  # Custom deadline


class ScadenzaAffittiBrevi(Base):
    """
    Extension table for affitti_brevi-specific scadenza metadata.

    Links to core Scadenza model via FK and adds:
    - tipo_scadenza: Affitti Brevi specific types (Police, ISTAT, etc.)
    - ricorrente: Recurrence flag for monthly ISTAT reports
    - frequenza_giorni: Days between recurrences
    - prossima_ricorrenza: Next recurrence date

    Usage:
        1. Create core.Scadenza first
        2. Create ScadenzaAffittiBrevi linking to it
        3. Query joins both for complete data
    """
    __tablename__ = "scadenze_affitti_brevi_ext"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to core scadenze table
    scadenza_id = Column(
        Integer,
        ForeignKey("scadenze.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One-to-one relationship
        index=True,
        comment="FK to core scadenze table"
    )

    # Affitti Brevi specific metadata
    tipo_scadenza = Column(
        SQLEnum(TipoScadenzaAffittiBrevi),
        nullable=False,
        index=True,
        comment="Affitti Brevi deadline type"
    )

    # Recurrence support (for REPORT_ISTAT)
    ricorrente = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if recurring deadline"
    )
    frequenza_giorni = Column(
        Integer,
        nullable=True,
        comment="Days between recurrences (e.g., 30 for monthly)"
    )
    prossima_ricorrenza = Column(
        Date,
        nullable=True,
        comment="Next recurrence date"
    )

    # Relationship to core Scadenza
    # Note: This assumes core.Scadenza has been imported
    # We'll need to set up the relationship properly

    def __repr__(self):
        return f"<ScadenzaAffittiBrevi(id={self.id}, scadenza_id={self.scadenza_id}, tipo={self.tipo_scadenza.value})>"

    def generate_next_recurrence(self):
        """Generate next recurrence date for recurring deadlines"""
        from datetime import timedelta
        if not self.ricorrente or not self.frequenza_giorni:
            return None

        if self.prossima_ricorrenza:
            next_date = self.prossima_ricorrenza + timedelta(days=self.frequenza_giorni)
        else:
            # If no next recurrence set, calculate from scadenza's data_scadenza
            # This requires access to the scadenza relationship
            return None

        return next_date
