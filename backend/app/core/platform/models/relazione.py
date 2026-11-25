"""
Role relation between a soggetto and an object of a module (tenant table
core_relazioni). Only relation types with fonte CORE are stored here; MODULO
types are derived from the module tables (app.core.platform_services.relazioni_query).
"""
from fractions import Fraction
from typing import Optional

from sqlalchemy import (
    JSON, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, String, Text,
)
from sqlalchemy.sql import func

from app.core.database import Base


class Relazione(Base):
    __tablename__ = "core_relazioni"
    __table_args__ = (
        CheckConstraint(
            "(quota_numeratore IS NULL) = (quota_denominatore IS NULL) AND "
            "(quota_numeratore IS NULL OR (quota_numeratore > 0 AND quota_numeratore <= quota_denominatore))",
            name="ck_core_relazioni_quota",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    soggetto_id = Column(Integer, nullable=False, index=True)
    ruolo_id = Column(Integer, ForeignKey("core_ruoli_disponibili.id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    sottotipo = Column(String(100), nullable=True)
    data_inizio = Column(Date, nullable=True)
    data_fine = Column(Date, nullable=True)
    data_scadenza = Column(Date, nullable=True)
    scadenza_id = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    dati = Column(JSON, nullable=True)
    # Share as a fraction as written by the user ("2/4" stays 2/4).
    quota_numeratore = Column(Integer, nullable=True)
    quota_denominatore = Column(Integer, nullable=True)
    creato_da = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def quota(self) -> Optional[str]:
        if self.quota_numeratore is None:
            return None
        return f"{self.quota_numeratore}/{self.quota_denominatore}"

    @property
    def quota_frazione(self) -> Optional[Fraction]:
        if self.quota_numeratore is None:
            return None
        return Fraction(self.quota_numeratore, self.quota_denominatore)
