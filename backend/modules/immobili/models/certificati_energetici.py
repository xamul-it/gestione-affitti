from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ClasseEnergetica(str, enum.Enum):
    A4 = "A4"
    A3 = "A3"
    A2 = "A2"
    A1 = "A1"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class CertificatoEnergetico(Base):
    __tablename__ = "certificati_energetici"

    id = Column(Integer, primary_key=True, index=True)
    unita_immobiliare_id = Column(Integer, ForeignKey("unita_immobiliari.id"), nullable=False)
    tecnico_id = Column(Integer, ForeignKey("tecnici.id"), nullable=False)

    classe_energetica = Column(SQLEnum(ClasseEnergetica), nullable=False)
    indice_prestazione_energetica = Column(Float, nullable=True)  # kWh/m²anno

    data_emissione = Column(Date, nullable=False)
    data_scadenza = Column(Date, nullable=False)
    numero_protocollo = Column(String(100), nullable=True)

    file_path = Column(String(500), nullable=True)  # Path al PDF del certificato
    note = Column(String(500), nullable=True)

    # Relationships
    unita_immobiliare = relationship("UnitaImmobiliare", back_populates="certificati_energetici")
    tecnico = relationship("Tecnico")

    def __repr__(self):
        return f"<CertificatoEnergetico UnitaImmobiliare:{self.unita_immobiliare_id} Classe:{self.classe_energetica.value}>"
