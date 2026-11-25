"""
Collegamento tra beni: principal (bene_id) -> linked (bene_collegato_id),
e.g. dwelling -> its box. Types and rules: services/collegamenti_beni.py.
The DB removes links when either bene is deleted (ON DELETE CASCADE).

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CollegamentoBeni(Base):
    __tablename__ = "immo_beni_collegamenti"
    __table_args__ = (
        CheckConstraint("bene_id <> bene_collegato_id", name="immo_beni_collegamenti_non_se_stesso"),
        CheckConstraint(
            "data_fine IS NULL OR data_inizio IS NULL OR data_fine >= data_inizio",
            name="immo_beni_collegamenti_date",
        ),
        Index(
            "uq_immo_beni_collegamenti_aperto", "bene_id", "bene_collegato_id", "tipo",
            unique=True, postgresql_where=text("data_fine IS NULL"),
        ),
        Index(
            "uq_immo_beni_pertinenza_aperta", "bene_collegato_id",
            unique=True, postgresql_where=text("tipo = 'PERTINENZA' AND data_fine IS NULL"),
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True)
    bene_id = Column(Integer, ForeignKey("immo_beni.id", ondelete="CASCADE"), nullable=False, index=True)
    bene_collegato_id = Column(Integer, ForeignKey("immo_beni.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(30), nullable=False)
    data_inizio = Column(Date, nullable=True)
    data_fine = Column(Date, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    bene = relationship("Bene", foreign_keys=[bene_id])
    bene_collegato = relationship("Bene", foreign_keys=[bene_collegato_id])

    @property
    def aperto(self) -> bool:
        return self.data_fine is None
