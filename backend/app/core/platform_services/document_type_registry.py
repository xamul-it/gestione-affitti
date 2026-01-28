"""
Document Type Registry - Sistema estensibile per tipologie documenti modulari.

Il registry viene popolato automaticamente dai manifest dei moduli durante il
caricamento dell'applicazione.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocumentTypeDefinition:
    """
    Definizione di una tipologia di documento.

    Attributes:
        codice: Codice univoco nel modulo (es: "CARTA_IDENTITA")
        nome: Nome visualizzato (es: "Carta d'Identità")
        categoria: Categoria logica (es: "identita", "contratto", "catastale")
        modulo_origine: Modulo che ha definito questo tipo
        richiede_scadenza: Se True, il documento ha una data di scadenza
        parsing_service: Nome del servizio di parsing (es: "mrz", "contract_parser")
        parsing_config: Configurazione specifica per il servizio di parsing
        inherits_from: Chiave completa di un tipo padre (es: "base.DOCUMENTO")
    """
    codice: str
    nome: str
    categoria: str
    modulo_origine: str
    richiede_scadenza: bool = False
    parsing_service: Optional[str] = None
    parsing_config: Optional[Dict] = field(default_factory=dict)
    inherits_from: Optional[str] = None

    @property
    def full_key(self) -> str:
        """Chiave completa: modulo.CODICE"""
        return f"{self.modulo_origine}.{self.codice}"

    def __post_init__(self):
        """Validazione post-inizializzazione"""
        if not self.codice:
            raise ValueError("codice è obbligatorio")
        if not self.nome:
            raise ValueError("nome è obbligatorio")
        if not self.modulo_origine:
            raise ValueError("modulo_origine è obbligatorio")

        # Validazione parsing_config
        if self.parsing_config is None:
            self.parsing_config = {}


class DocumentTypeRegistry:
    """
    Registry singleton per tipologie documenti.

    Gestisce la registrazione e il lookup di tipologie documenti dichiarate
    nei manifest dei moduli.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._types: Dict[str, DocumentTypeDefinition] = {}
            self._by_module: Dict[str, List[DocumentTypeDefinition]] = {}
            self._by_category: Dict[str, List[DocumentTypeDefinition]] = {}
            self._by_parsing_service: Dict[str, List[DocumentTypeDefinition]] = {}
            self._initialized = True

    def register_from_manifest(self, module_name: str, manifest: Dict) -> None:
        """
        Registra tipologie documenti dal manifest di un modulo.

        Args:
            module_name: Nome tecnico del modulo
            manifest: Dictionary del manifest

        Example manifest:
            {
                "document_types": [
                    {
                        "codice": "CARTA_IDENTITA",
                        "nome": "Carta d'Identità",
                        "categoria": "identita",
                        "richiede_scadenza": True,
                        "parsing_service": "mrz",
                        "parsing_config": {"mrz_format": "td1"}
                    }
                ]
            }
        """
        document_types = manifest.get("document_types", [])

        if not document_types:
            logger.debug(f"Modulo {module_name} non dichiara document_types")
            return

        logger.info(f"Registrazione {len(document_types)} tipologie da modulo {module_name}")

        for type_def in document_types:
            try:
                # Crea DocumentTypeDefinition
                doc_type = DocumentTypeDefinition(
                    codice=type_def["codice"],
                    nome=type_def["nome"],
                    categoria=type_def.get("categoria", "generic"),
                    modulo_origine=module_name,
                    richiede_scadenza=type_def.get("richiede_scadenza", False),
                    parsing_service=type_def.get("parsing_service"),
                    parsing_config=type_def.get("parsing_config", {}),
                    inherits_from=type_def.get("inherits_from")
                )

                # Registra con chiave completa
                full_key = doc_type.full_key
                if full_key in self._types:
                    logger.warning(
                        f"Tipo documento {full_key} già registrato, sovrascrittura"
                    )

                self._types[full_key] = doc_type

                # Indicizza per modulo
                if module_name not in self._by_module:
                    self._by_module[module_name] = []
                self._by_module[module_name].append(doc_type)

                # Indicizza per categoria
                if doc_type.categoria not in self._by_category:
                    self._by_category[doc_type.categoria] = []
                self._by_category[doc_type.categoria].append(doc_type)

                # Indicizza per parsing service
                if doc_type.parsing_service:
                    if doc_type.parsing_service not in self._by_parsing_service:
                        self._by_parsing_service[doc_type.parsing_service] = []
                    self._by_parsing_service[doc_type.parsing_service].append(doc_type)

                logger.debug(f"✓ Registrato tipo documento: {full_key}")

            except Exception as e:
                logger.error(f"Errore registrazione tipo documento da {module_name}: {e}")
                continue

        logger.info(f"✓ Modulo {module_name}: {len(document_types)} tipologie registrate")

    def get(self, full_key: str) -> Optional[DocumentTypeDefinition]:
        """
        Ottieni definizione per chiave completa.

        Args:
            full_key: Chiave completa (modulo.CODICE)

        Returns:
            DocumentTypeDefinition o None
        """
        return self._types.get(full_key)

    def get_by_codice(self, codice: str, modulo: Optional[str] = None) -> Optional[DocumentTypeDefinition]:
        """
        Cerca tipo per codice, opzionalmente filtrato per modulo.

        Args:
            codice: Codice tipo documento
            modulo: Nome modulo (opzionale)

        Returns:
            DocumentTypeDefinition o None
        """
        if modulo:
            full_key = f"{modulo}.{codice}"
            return self._types.get(full_key)

        # Cerca in tutti i moduli
        for doc_type in self._types.values():
            if doc_type.codice == codice:
                return doc_type

        return None

    def get_by_module(self, module_name: str) -> List[DocumentTypeDefinition]:
        """
        Ottieni tutti i tipi dichiarati da un modulo.

        Args:
            module_name: Nome del modulo

        Returns:
            Lista di DocumentTypeDefinition
        """
        return self._by_module.get(module_name, [])

    def get_by_category(self, categoria: str) -> List[DocumentTypeDefinition]:
        """
        Ottieni tutti i tipi di una categoria.

        Args:
            categoria: Nome categoria (es: "identita", "contratto")

        Returns:
            Lista di DocumentTypeDefinition
        """
        return self._by_category.get(categoria, [])

    def get_types_with_parsing(self) -> List[DocumentTypeDefinition]:
        """
        Ottieni tutti i tipi che supportano parsing automatico.

        Returns:
            Lista di DocumentTypeDefinition con parsing_service definito
        """
        return [dt for dt in self._types.values() if dt.parsing_service]

    def get_by_parsing_service(self, service_name: str) -> List[DocumentTypeDefinition]:
        """
        Ottieni tutti i tipi gestiti da un servizio di parsing.

        Args:
            service_name: Nome servizio (es: "mrz", "contract_parser")

        Returns:
            Lista di DocumentTypeDefinition
        """
        return self._by_parsing_service.get(service_name, [])

    def list_all(self) -> List[DocumentTypeDefinition]:
        """
        Ottieni tutti i tipi registrati.

        Returns:
            Lista di DocumentTypeDefinition
        """
        return list(self._types.values())

    def clear(self) -> None:
        """
        Svuota il registry (utile per testing).
        """
        self._types.clear()
        self._by_module.clear()
        self._by_category.clear()
        self._by_parsing_service.clear()
        logger.debug("Registry svuotato")

    def __len__(self) -> int:
        """Numero di tipi registrati"""
        return len(self._types)

    def __contains__(self, full_key: str) -> bool:
        """Verifica se una chiave è registrata"""
        return full_key in self._types


# Istanza singleton globale
document_type_registry = DocumentTypeRegistry()
