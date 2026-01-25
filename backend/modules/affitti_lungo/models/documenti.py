"""
Shim for Documento model.

Documento is owned by anagrafica_italiana to avoid cyclic dependencies.
"""
# Import from package root; use enum to keep Pydantic schema generation simple.
from anagrafica_italiana.models import Documento, EntityType, TipoDocumentoEnum

# Alias for backward compatibility within this module/package.
TipoDocumento = TipoDocumentoEnum

__all__ = ["Documento", "EntityType", "TipoDocumento", "TipoDocumentoEnum"]
