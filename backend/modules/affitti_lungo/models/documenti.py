"""
Shim for Documento model.

Documento is owned by anagrafica_italiana to avoid cyclic dependencies.
"""
from anagrafica_italiana.models.documento import Documento, EntityType, TipoDocumento

__all__ = ["Documento", "EntityType", "TipoDocumento"]
