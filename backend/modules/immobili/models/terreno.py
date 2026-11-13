"""
Terreno - land parcel of the Catasto Terreni, specialisation of Bene.

Its id is the id of its Bene (immo_beni), which holds code, address and
cadastral identification; `sezione_catastale` is the bene's `sezione`.
Quality, class, surface and incomes live in its portions
(immo_terreni_porzioni); `superficie_mq` is their sum, kept by the server.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from decimal import Decimal

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, synonym

from .bene import Bene


class Terreno(Bene):
    """Land parcel: one or more portions with quality, class and incomes."""
    __tablename__ = "immo_terreni"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, ForeignKey("immo_beni.id", ondelete="CASCADE"), primary_key=True)
    nome = Column(String(255), nullable=True)
    tipologia_id = Column(
        Integer,
        ForeignKey("public.immo_tipologie_terreno.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    nazione = Column(String(100), nullable=True, default="Italia", server_default="Italia")
    superficie_mq = Column(Float, nullable=True)
    edificabile = Column(Boolean, nullable=False, default=False, server_default="false")
    esente_imu_montano = Column(Boolean, nullable=False, default=False, server_default="false")
    servitu = Column(Text, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "TERRENO"}

    sezione_catastale = synonym("sezione")

    tipologia = relationship("TipologiaTerreno", foreign_keys=[tipologia_id])
    porzioni = relationship(
        "TerrenoPorzione",
        back_populates="terreno",
        order_by="TerrenoPorzione.porzione",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def ricalcola_superficie(self) -> None:
        self.superficie_mq = sum(p.superficie_mq or 0 for p in self.porzioni)

    def _totale(self, campo):
        valori = [getattr(p, campo) for p in self.porzioni if getattr(p, campo) is not None]
        if not valori:
            return None
        return sum((Decimal(str(v)) for v in valori), Decimal("0"))

    @property
    def reddito_dominicale_totale(self):
        return self._totale("reddito_dominicale")

    @property
    def reddito_agrario_totale(self):
        return self._totale("reddito_agrario")

    def __repr__(self):
        return f"<Terreno(codice='{self.codice}', foglio={self.foglio}, particella={self.particella})>"
