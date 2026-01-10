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
    SOGGETTO_ANAGRAFICO = "SOGGETTO_ANAGRAFICO"  # For anagrafica documents


class TipoDocumento(str, enum.Enum):
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
    __tablename__ = "documenti"

    id = Column(Integer, primary_key=True, index=True)

    # Relazione polimorfa
    entity_type = Column(SQLEnum(EntityType), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)

    # Metadata documento
    tipo_documento = Column(SQLEnum(TipoDocumento), nullable=False)
    nome_file = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    dimensione = Column(BigInteger, nullable=True)  # in bytes

    # Info aggiuntive
    descrizione = Column(String(500), nullable=True)
    note = Column(String(500), nullable=True)

    # Scadenza (per documenti di identità, certificati, etc.)
    data_scadenza = Column(Date, nullable=True, index=True)

    # Optional: Link to TipoDocumento table (for anagrafica module)
    # This allows using the flexible tipo_documento table from anagrafica_italiana
    tipo_documento_id = Column(Integer, ForeignKey("tipi_documento.id"), nullable=True)

    # Metadata sistema
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Documento {self.nome_file} - {self.entity_type}:{self.entity_id}>"
