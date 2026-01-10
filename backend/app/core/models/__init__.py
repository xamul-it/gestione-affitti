"""
Core platform models for Gestione Affitti.

These models provide shared, domain-agnostic functionality across all modules.

MIGRATION NOTICE:
Domain-specific models have been moved to their respective modules:

- SoggettoAnagrafico, TipoSoggetto -> modules/anagrafica_italiana
- CategoriaCatastale, ComuneItalia, TipoImmobileCategoriaMap -> modules/immobili
- UnitaImmobiliare, Condominio, Proprietario, etc. -> modules/immobili

Import from the appropriate module instead:
    from modules.anagrafica_italiana.models import SoggettoAnagrafico
    from modules.immobili.models import UnitaImmobiliare, CategoriaCatastale
"""
# Platform models - these remain in core as they are domain-agnostic
from .ruoli import RuoloDisponibile, SoggettoRuolo
from .tenant import Tenant, UserTenant, TenantModule

__all__ = [
    "RuoloDisponibile",
    "SoggettoRuolo",
    "Tenant",
    "UserTenant",
    "TenantModule",
]
