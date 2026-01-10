"""
Seed data for Anagrafica Italiana module.
"""
from .seed_tipi_documento import seed_tipi_documento
from .seed_stati_documento import seed_stati_documento
from .seed_comuni_italia import seed_comuni_italia_minimal

__all__ = [
    "seed_tipi_documento",
    "seed_stati_documento",
    "seed_comuni_italia_minimal",
]
