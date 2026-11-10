"""
Relation providers of the immobili module (relation types with fonte MODULO,
spec docs/superpowers/specs/2026-11-10-relazioni-ruoli-soggetti-design.md).

Each provider returns a composable select with exactly the columns
soggetto_id, entity_type, entity_id, descrizione, data_inizio, data_fine,
record_id - or None when the module tables are missing in the tenant.
"""
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from .models import AssegnazioneConduttore, Conduttore, DirittoImmobile, Proprietario, UnitaImmobiliare

_DIRITTI = {
    "PROPRIETARIO": "Proprietà", "COMPROPRIETARIO": "Comproprietà", "USUFRUTTUARIO": "Usufrutto",
    "NUDA_PROPRIETA": "Nuda proprietà", "USO": "Uso", "ABITAZIONE": "Abitazione",
    "SUPERFICIE": "Superficie", "ENFITEUSI": "Enfiteusi", "ALTRO": "Altro diritto",
}


def _has_tables(db: Session, schema: str, *tables: str) -> bool:
    inspector = inspect(db.get_bind())
    return all(inspector.has_table(t, schema=schema) for t in tables)


def _iso_date(col):
    """
    Dates stored as 'YYYY-MM-DD' strings: anything else, including impossible
    calendar dates such as 2024-02-30, becomes NULL instead of failing the
    whole query. Nested CASEs because PostgreSQL does not short-circuit AND.
    """
    primo_del_mese = sa.cast(sa.func.concat(sa.func.substr(col, 1, 7), "-01"), sa.Date)
    giorni_del_mese = sa.extract("day", primo_del_mese + sa.text("interval '1 month - 1 day'"))
    giorno = sa.cast(sa.func.substr(col, 9, 2), sa.Integer)
    return sa.case(
        (col.op("~")(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"),
         sa.case((giorno <= giorni_del_mese, sa.cast(col, sa.Date)), else_=None)),
        else_=None,
    )


def _indirizzo(u):
    return sa.func.concat_ws(", ", u.indirizzo, u.citta)


def proprietari(db: Session, tenant_schema: str) -> Optional[sa.Select]:
    if not _has_tables(db, tenant_schema, "immo_proprietari", "immo_diritti_immobile", "immo_unita_immobiliari"):
        return None
    p, d, u = Proprietario.__table__.c, DirittoImmobile.__table__.c, UnitaImmobiliare.__table__.c
    tipo = sa.case(*[(sa.cast(d.tipo_diritto, sa.String) == k, v) for k, v in _DIRITTI.items()], else_=None)
    quota = sa.case(
        (d.quota_percentuale.isnot(None),
         sa.func.concat(" ", sa.func.rtrim(sa.func.rtrim(sa.cast(d.quota_percentuale, sa.String), "0"), "."), "%")),
        else_="",
    )
    descrizione = sa.case(
        (d.id.isnot(None), sa.func.concat(_indirizzo(u), " — ", tipo, quota)),
        else_=None,
    )
    return (
        sa.select(
            p.soggetto_id.label("soggetto_id"),
            sa.case((d.id.isnot(None), "IMMOBILE"), else_=None).label("entity_type"),
            d.unita_immobiliare_id.label("entity_id"),
            descrizione.label("descrizione"),
            _iso_date(d.data_inizio).label("data_inizio"),
            _iso_date(d.data_fine).label("data_fine"),
            p.id.label("record_id"),
        )
        .select_from(
            Proprietario.__table__
            .outerjoin(DirittoImmobile.__table__, d.proprietario_id == p.id)
            .outerjoin(UnitaImmobiliare.__table__, u.id == d.unita_immobiliare_id)
        )
        .where(p.soggetto_id.isnot(None))
    )


def conduttori(db: Session, tenant_schema: str) -> Optional[sa.Select]:
    if not _has_tables(db, tenant_schema, "immo_conduttori", "immo_assegnazioni_conduttore", "immo_unita_immobiliari"):
        return None
    c, a, u = Conduttore.__table__.c, AssegnazioneConduttore.__table__.c, UnitaImmobiliare.__table__.c
    return (
        sa.select(
            c.soggetto_id.label("soggetto_id"),
            sa.case((a.id.isnot(None), "IMMOBILE"), else_=None).label("entity_type"),
            a.unita_immobiliare_id.label("entity_id"),
            sa.case((a.id.isnot(None), _indirizzo(u)), else_=None).label("descrizione"),
            a.data_inizio.label("data_inizio"),
            a.data_fine.label("data_fine"),
            c.id.label("record_id"),
        )
        .select_from(
            Conduttore.__table__
            .outerjoin(AssegnazioneConduttore.__table__, a.conduttore_id == c.id)
            .outerjoin(UnitaImmobiliare.__table__, u.id == a.unita_immobiliare_id)
        )
        .where(c.soggetto_id.isnot(None))
    )
