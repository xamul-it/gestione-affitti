"""
Conduttore Model - Occupant role specialization.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)

The "conduttore" role (whoever occupies/uses a property unit) is
independent of any rental contract: it also covers usufrutto, comodato
d'uso, or a proprietario who simply lives in their own unit. The affitti
module (when built) may create/close AssegnazioneConduttore rows to track
a lease's occupant, but this role and its per-unit assignment must exist
and be manageable without any rental module installed — see
docs' immobili domain-model notes on why "conduttore" != "affittuario".
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Conduttore(Base):
    """
    Tabella specializzazione per il ruolo di Conduttore.

    Contiene SOLO i dati specifici del ruolo di conduttore. I dati
    anagrafici sono centralizzati in anag_soggetti_anagrafici.

    Un soggetto può essere contemporaneamente proprietario, conduttore,
    affittuario (nel modulo affitti), tecnico, etc.
    """
    __tablename__ = "immo_conduttori"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    soggetto_id = Column(
        Integer,
        ForeignKey("anag_soggetti_anagrafici.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    note = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    soggetto = relationship("SoggettoAnagrafico", foreign_keys=[soggetto_id])
    assegnazioni = relationship("AssegnazioneConduttore", back_populates="conduttore", passive_deletes=True)

    def __repr__(self):
        return f"<Conduttore {self.id}: Soggetto {self.soggetto_id}>"
