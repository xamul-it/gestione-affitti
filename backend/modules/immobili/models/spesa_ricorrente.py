"""
SpesaRicorrenteImmobile Model - recurring property-linked expenses/deadlines
(IMU, TARI, utility bills, ...).

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)

Design notes (see project memory "immobili-domain-model" for the full
domain rules this encodes):
- Links to EXACTLY ONE of unita_immobiliare_id / condominio_id: most
  expenses are per-unit (IMU, TARI), but a utility contract can be
  centralized at the building/complex level instead (condominio_id).
- `responsabile` records who is primarily liable (proprietario for
  ownership-linked/extraordinary items like IMU, conduttore for
  occupancy-linked/ordinary items like TARI and everyday utilities) — this
  is informational classification, not an access-control filter, and it
  never hides the proprietario: ownership is always still reachable via
  the linked unit's DirittoImmobile rows regardless of who is "responsabile"
  here, because an owner is jointly liable for a conduttore's unpaid bills.
- `tipo_spesa` is intentionally an open string, not a hardcoded enum with a
  fixed short list: IMU/TARI have a known calculation basis today, but the
  same tracking (importo, scadenza, pagato) needs to extend to utility
  bills and other recurring property expenses without a model change each
  time a new type shows up. TIPI_NOTI lists the ones the UI knows a label
  for; anything else is accepted as free text.
- Recurrence is manual ("duplicate for next period"), not auto-generated:
  amounts/rates for these expenses are set externally (comune, national
  government, utility provider) and can't be reliably predicted from the
  previous occurrence.
- Optionally linked to a core Scadenza (app.core.platform.models.Scadenza)
  for reminders/notifications, reusing the platform scadenzario instead of
  a second notification path.
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, Text, ForeignKey, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ResponsabileSpesa(str, enum.Enum):
    PROPRIETARIO = "PROPRIETARIO"
    CONDUTTORE = "CONDUTTORE"


# Known expense types the UI can offer as suggestions/labels. Not an
# exhaustive/enforced list — tipo_spesa accepts any string so a new
# recurring expense type doesn't require a migration.
TIPI_NOTI = ["IMU", "TARI", "UTENZA_LUCE", "UTENZA_GAS", "UTENZA_ACQUA", "ALTRO"]


class SpesaRicorrenteImmobile(Base):
    """A recurring property-linked expense/deadline instance (one period)."""
    __tablename__ = "immo_spese_ricorrenti"
    __table_args__ = (
        CheckConstraint(
            "(unita_immobiliare_id IS NOT NULL) != (condominio_id IS NOT NULL)",
            name="ck_spesa_ricorrente_unita_xor_condominio",
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True)

    # Exactly one of these two is set (see CheckConstraint above).
    unita_immobiliare_id = Column(
        Integer, ForeignKey("immo_unita_immobiliari.id", ondelete="CASCADE"), nullable=True, index=True
    )
    condominio_id = Column(
        Integer, ForeignKey("immo_condomini.id", ondelete="CASCADE"), nullable=True, index=True
    )

    tipo_spesa = Column(String(50), nullable=False, index=True)
    responsabile = Column(SQLEnum(ResponsabileSpesa), nullable=False, index=True)

    periodo = Column(String(50), nullable=False, comment="es. '2026', '2026-T2', label libera del periodo")
    rata = Column(String(50), nullable=True, comment="es. ACCONTO, SALDO, UNICA, o etichetta libera")
    importo = Column(Numeric(10, 2), nullable=False)
    data_scadenza = Column(Date, nullable=False, index=True)

    pagato = Column(Boolean, nullable=False, default=False, index=True)
    data_pagamento = Column(Date, nullable=True)
    note = Column(Text, nullable=True, comment="Testo libero, es. protocollo F24")

    # Linked core scadenzario row (reminders/notifications). Nullable so a
    # row survives if the linked Scadenza is deleted independently.
    scadenza_id = Column(
        Integer, ForeignKey("core_scadenze.id", ondelete="SET NULL"), nullable=True
    )

    unita_immobiliare = relationship(
        "UnitaImmobiliare", back_populates="spese_ricorrenti", foreign_keys=[unita_immobiliare_id]
    )
    condominio = relationship(
        "Condominio", back_populates="spese_ricorrenti", foreign_keys=[condominio_id]
    )

    def __repr__(self):
        target = f"unita={self.unita_immobiliare_id}" if self.unita_immobiliare_id else f"condominio={self.condominio_id}"
        return f"<SpesaRicorrenteImmobile {self.tipo_spesa}/{self.periodo}/{self.rata} {target} pagato={self.pagato}>"
