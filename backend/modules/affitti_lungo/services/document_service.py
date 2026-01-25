"""
Shim for DocumentService.

DocumentService is owned by anagrafica_italiana to avoid cyclic dependencies.
"""
from anagrafica_italiana.services.document_service import DocumentService

__all__ = ["DocumentService"]
