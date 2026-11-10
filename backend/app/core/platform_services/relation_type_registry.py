"""
Relation types ("tipi di relazione") declared by the modules in their manifest
(`relation_types`): a soggetto is linked to an object of a module through a
role relation (spec docs/superpowers/specs/2026-11-10-relazioni-ruoli-soggetti-design.md).

fonte CORE   -> relations stored in the tenant table core_relazioni
fonte MODULO -> relations derived from the module's own tables by `provider`
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

FONTI = ("CORE", "MODULO")


def valid_relation_scadenza(scadenza) -> bool:
    if not isinstance(scadenza, dict):
        return False
    if scadenza == {"manuale": True}:
        return True
    mesi = scadenza.get("mesi")
    return (
        set(scadenza) == {"mesi", "da"}
        and isinstance(mesi, int) and not isinstance(mesi, bool) and mesi > 0
        and scadenza["da"] == "data_inizio"
    )


@dataclass
class RelationTypeDefinition:
    codice: str
    nome: str
    modulo: str
    descrizione: Optional[str] = None
    entity_types: Optional[List[str]] = None
    fonte: str = "CORE"
    provider: Optional[str] = None
    scadenza: Optional[Dict] = None
    promemoria_giorni: Optional[List[int]] = None
    sottotipi_fonte: Optional[str] = None
    unico_per_oggetto: bool = False
    permesso_oggetto: Optional[str] = None

    def __post_init__(self):
        if not self.codice or not self.nome or not self.modulo:
            raise ValueError("codice, nome e modulo sono obbligatori")
        if self.fonte not in FONTI:
            raise ValueError(f"{self.codice}: fonte '{self.fonte}' non valida ({', '.join(FONTI)})")
        if self.entity_types is not None:
            from app.core.platform.models.documento import EntityType
            valid = {e.value for e in EntityType}
            unknown = [e for e in self.entity_types if e not in valid]
            if unknown:
                raise ValueError(f"{self.codice}: entity_types sconosciuti {unknown}")
        if self.fonte == "MODULO" and not self.provider:
            raise ValueError(f"{self.codice}: un tipo con fonte MODULO richiede un provider")
        if self.scadenza is not None:
            if self.fonte == "MODULO":
                raise ValueError(f"{self.codice}: la scadenza vale solo per i tipi con fonte CORE")
            if not valid_relation_scadenza(self.scadenza):
                raise ValueError(
                    f"{self.codice}: scadenza deve essere null, {{'manuale': true}} "
                    f"o {{'mesi': n>0, 'da': 'data_inizio'}}"
                )
