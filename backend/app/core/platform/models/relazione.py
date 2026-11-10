"""
Role relation between a soggetto and an object of a module (tenant table
core_relazioni). Only relation types with fonte CORE are stored here; MODULO
types are derived from the module tables (app.core.platform_services.relazioni_query).
"""
from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Relazione(Base):
    __tablename__ = "core_relazioni"

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
    creato_da = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
