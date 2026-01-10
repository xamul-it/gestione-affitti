"""
Modello per gestire i ruoli delle persone fisiche all'interno delle aziende (persone giuridiche).
Relazione N-M tra PERSONA_FISICA e PERSONA_GIURIDICA con attributi sul ruolo.
"""
from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class RuoloAzienda(Base):
    """
    Associazione tra una persona fisica e un'azienda (persona giuridica) con un ruolo specifico.

    Esempi di ruoli: Amministratore Delegato, Segretaria, Tecnico, Responsabile, etc.
    """
    __tablename__ = "ruoli_azienda"

    id = Column(Integer, primary_key=True, index=True)

    # Persona fisica (dipendente, collaboratore, etc.)
    persona_fisica_id = Column(Integer, ForeignKey('soggetti_anagrafici.id', ondelete='CASCADE'), nullable=False)

    # Azienda (persona giuridica)
    persona_giuridica_id = Column(Integer, ForeignKey('soggetti_anagrafici.id', ondelete='CASCADE'), nullable=False)

    # Ruolo: supporta due modalità (backward compatible)
    # 1. Nuovo sistema: FK a ruolo_azienda_tipo (normalizzato, con autocomplete)
    ruolo_tipo_id = Column(Integer, ForeignKey('public.ruoli_azienda_tipi.id', ondelete='SET NULL'), nullable=True)
    # 2. Vecchio sistema: testo libero (per backward compatibility)
    ruolo = Column(String(100), nullable=True)  # Ora nullable, usato solo se ruolo_tipo_id è NULL

    # Date del ruolo (opzionali)
    data_inizio = Column(Date, nullable=True)  # Data di inizio del ruolo
    data_fine = Column(Date, nullable=True)     # Data di fine del ruolo (null se attivo)

    # Audit timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    persona_fisica = relationship(
        "SoggettoAnagrafico",
        foreign_keys=[persona_fisica_id],
        back_populates="ruoli_in_aziende"
    )

    persona_giuridica = relationship(
        "SoggettoAnagrafico",
        foreign_keys=[persona_giuridica_id],
        back_populates="persone_associate"
    )

    ruolo_tipo = relationship(
        "RuoloAziendaTipo",
        foreign_keys=[ruolo_tipo_id]
    )

    def get_ruolo_nome(self):
        """Ottieni il nome del ruolo (da ruolo_tipo se presente, altrimenti da ruolo text)"""
        if self.ruolo_tipo_id and self.ruolo_tipo:
            return self.ruolo_tipo.nome
        return self.ruolo or ""

    def __repr__(self):
        ruolo_nome = self.get_ruolo_nome()
        return f"<RuoloAzienda(id={self.id}, persona={self.persona_fisica_id}, azienda={self.persona_giuridica_id}, ruolo='{ruolo_nome}')>"

    def to_dict(self):
        """Serializza il ruolo in un dizionario"""
        return {
            'id': self.id,
            'persona_fisica_id': self.persona_fisica_id,
            'persona_giuridica_id': self.persona_giuridica_id,
            'ruolo_tipo_id': self.ruolo_tipo_id,
            'ruolo': self.get_ruolo_nome(),  # Sempre il nome corretto
            'data_inizio': self.data_inizio.isoformat() if self.data_inizio else None,
            'data_fine': self.data_fine.isoformat() if self.data_fine else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
