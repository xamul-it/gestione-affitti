"""
Seeds for Immobili module.

Exports seed functions for public and tenant data.
"""
from .seed_public import seed_all_public, seed_categorie_catastali, seed_tipologie_terreno
from .seed_tenant import seed_tenant_data

__all__ = [
    "seed_all_public",
    "seed_categorie_catastali",
    "seed_tipologie_terreno",
    "seed_tenant_data",
]
