"""
CertificatoEnergetico Model - Energy performance certificate.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
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
    """
    Energy performance certificate (APE - Attestato di Prestazione Energetica).

    Links to a property unit and a technician who certified it.
    """
    __tablename__ = "immo_certificati_energetici"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    unita_immobiliare_id = Column(Integer, ForeignKey("immo_unita_immobiliari.id"), nullable=False)
    # Cross-module reference (affitti_lungo); keep as plain int to avoid FK errors
    # when the tecnici table is not present in this tenant.
    tecnico_id = Column(Integer, nullable=False)

    classe_energetica = Column(SQLEnum(ClasseEnergetica), nullable=False)
    indice_prestazione_energetica = Column(Float, nullable=True)  # kWh/m²anno

    data_emissione = Column(Date, nullable=False)
    data_scadenza = Column(Date, nullable=False)
    numero_protocollo = Column(String(100), nullable=True)

    file_path = Column(String(500), nullable=True)  # Path al PDF del certificato
    note = Column(String(500), nullable=True)

    # Relationships
    unita_immobiliare = relationship("UnitaImmobiliare", back_populates="certificati_energetici")
    tecnico = relationship(
        "Tecnico",
        primaryjoin="CertificatoEnergetico.tecnico_id==Tecnico.id",
        foreign_keys=[tecnico_id],
    )

    def __repr__(self):
        return f"<CertificatoEnergetico UnitaImmobiliare:{self.unita_immobiliare_id} Classe:{self.classe_energetica.value}>"
