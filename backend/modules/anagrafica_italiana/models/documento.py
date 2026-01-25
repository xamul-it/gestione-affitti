"""
Documento model shared across modules.

Owned by anagrafica_italiana to avoid cyclic dependencies.
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, BigInteger, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class EntityType(str, enum.Enum):
    IMMOBILE = "IMMOBILE"
    AFFITTUARIO = "AFFITTUARIO"
    CONTRATTO = "CONTRATTO"
    SPESA = "SPESA"
    INCASSO = "INCASSO"
    TECNICO = "TECNICO"
    CERTIFICATO_ENERGETICO = "CERTIFICATO_ENERGETICO"
    PROPRIETARIO = "PROPRIETARIO"
    SOGGETTO_ANAGRAFICO = "SOGGETTO_ANAGRAFICO"


class TipoDocumentoEnum(str, enum.Enum):
    CERTIFICATO_ENERGETICO = "CERTIFICATO_ENERGETICO"
    VISURA_CATASTALE = "VISURA_CATASTALE"
    PLANIMETRIA = "PLANIMETRIA"
    CONTRATTO_AFFITTO = "CONTRATTO_AFFITTO"
    DOCUMENTO_IDENTITA = "DOCUMENTO_IDENTITA"
    CODICE_FISCALE = "CODICE_FISCALE"
    FATTURA = "FATTURA"
    RICEVUTA_PAGAMENTO = "RICEVUTA_PAGAMENTO"
    PERIZIA = "PERIZIA"
    FOTO = "FOTO"
    ALTRO = "ALTRO"


class Documento(Base):
    __tablename__ = "anag_documenti"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(SQLEnum(EntityType), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)

    tipo_documento = Column(SQLEnum(TipoDocumentoEnum), nullable=False)
    nome_file = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    dimensione = Column(BigInteger, nullable=True)

    descrizione = Column(String(500), nullable=True)
    note = Column(String(500), nullable=True)
    data_scadenza = Column(Date, nullable=True, index=True)

    tipo_documento_id = Column(Integer, ForeignKey("public.anag_tipi_documento.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Documento {self.nome_file} - {self.entity_type}:{self.entity_id}>"
