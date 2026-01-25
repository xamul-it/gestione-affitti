"""
Seed data for Anagrafica Italiana module.
"""
from .seed_tipi_documento import seed_tipi_documento
from .seed_stati_documento import seed_stati_documento
from .seed_comuni_italia import seed_comuni_italia_minimal
from .seed_ruoli_azienda_tipi import seed_ruoli_azienda_tipi
from .seed_public import seed_public
from .seed_tenant import seed_tenant

__all__ = [
    "seed_tipi_documento",
    "seed_stati_documento",
    "seed_comuni_italia_minimal",
    "seed_ruoli_azienda_tipi",
    "seed_public",
    "seed_tenant",
]
