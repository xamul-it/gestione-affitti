"""
Modello PecUtenteAbilitato — utenti con accesso a una casella PEC.

Il campo user_id è un Integer semplice, senza FK reale, perché gli utenti
vivono nella public schema (core_users) ed è un legame cross-schema.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PecUtenteAbilitato(Base):
    __tablename__ = "pec_utenti_abilitati"

    id = Column(Integer, primary_key=True, index=True)
    casella_id = Column(
        Integer,
        ForeignKey("pec_caselle.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Intenzionalmente senza FK reale: cross-schema (public.core_users)
    user_id = Column(Integer, nullable=False, index=True)
    puo_rispondere = Column(Boolean, nullable=False, default=False)
    notifica_email = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    casella = relationship("PecCasella", backref="utenti_abilitati")

    __table_args__ = (
        UniqueConstraint(
            "casella_id", "user_id", name="uq_pec_utenti_abilitati_casella_user"
        ),
    )
