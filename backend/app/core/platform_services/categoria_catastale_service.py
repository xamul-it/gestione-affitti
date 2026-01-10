import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), "../../../modules")
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

"""
Categoria Catastale Service - Infer cadastral categories from property types.

Automatically maps free-text property types (e.g., "appartamento", "box")
to official Italian cadastral categories (A/2, C/6, etc.).

Features:
- Database-backed mappings (learns over time)
- Keyword matching with defaults
- Fallback to generic category
- Auto-save inferred mappings

Usage:
    from app.core.platform_services import CategoriaCatastaleService

    service = CategoriaCatastaleService(db)
    categoria_id = service.infer_categoria_id("appartamento")
"""
from typing import Optional, Dict
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class CategoriaCatastaleService:
    """
    Infer and manage categoria catastale for immobili.

    Provides intelligent mapping from free-text property types to
    official cadastral categories using:
    1. Database mappings (TipoImmobileCategoriaMap)
    2. Keyword matching with defaults
    3. Fallback to generic category

    Default mappings based on Italian real estate conventions:
    - Residential: A/2 (standard apartment)
    - Luxury: A/1 (signorile), A/8 (villa)
    - Garages: C/6
    - Commercial: C/1 (shop), A/10 (office)
    """

    # Default tipo → categoria mappings
    # Based on most common Italian property types
    DEFAULT_TIPO_CATEGORIA: Dict[str, str] = {
        # Residential - Group A
        "appartamento": "A/2",
        "casa": "A/2",
        "villa": "A/8",
        "villino": "A/7",
        "attico": "A/1",
        "mansarda": "A/3",
        "loft": "A/2",
        "monolocale": "A/3",
        "bilocale": "A/2",
        "trilocale": "A/2",

        # Garages - Group C (order matters - most specific first)
        "box prima casa": "C/6",
        "box pertinenza": "C/6",
        "box": "C/6",
        "garage": "C/6",
        "autorimessa": "C/6",
        "posto auto": "C/6",

        # Storage - Group C
        "cantina": "C/2",
        "magazzino": "C/2",
        "deposito": "C/2",

        # Commercial - Group C and A
        "negozio": "C/1",
        "locale commerciale": "C/1",
        "bottega": "C/1",
        "ufficio": "A/10",
        "studio": "A/10",

        # Special
        "laboratorio": "C/3",
        "capannone": "D/1",
    }

    # Fallback categoria for unknown types
    FALLBACK_CATEGORIA = "A/2"  # Generic residential

    def __init__(self, db: Session):
        """
        Initialize categoria catastale service.

        Args:
            db: Database session
        """
        self.db = db

    def infer_categoria_id(self, tipo_immobile: Optional[str]) -> Optional[int]:
        """
        Infer categoria_catastale_id from tipo_immobile text.

        Logic cascade:
        1. Check database mapping (TipoImmobileCategoriaMap)
        2. Try keyword matching with defaults
        3. Return fallback categoria

        Args:
            tipo_immobile: Property type text (e.g., "appartamento", "box")

        Returns:
            categoria_catastale.id or None if categoria not found

        Examples:
            >>> categoria_id = service.infer_categoria_id("appartamento")
            >>> print(categoria_id)  # ID of A/2 categoria
            2
        """
        if not tipo_immobile or not tipo_immobile.strip():
            logger.debug("Empty tipo_immobile provided")
            return None

        tipo_normalized = tipo_immobile.lower().strip()
        logger.debug(f"Inferring categoria for tipo: {tipo_normalized}")

        # 1. Check database mapping
        from immobili.models import TipoImmobileCategoriaMap

        mapping = self.db.query(TipoImmobileCategoriaMap).filter(
            TipoImmobileCategoriaMap.tipo_immobile == tipo_normalized
        ).first()

        if mapping:
            logger.info(f"Found DB mapping: {tipo_normalized} → categoria_id={mapping.categoria_catastale_id}")
            return mapping.categoria_catastale_id

        # 2. Try keyword matching
        categoria_code = self._match_keyword(tipo_normalized)

        if not categoria_code:
            # 3. Use fallback
            categoria_code = self.FALLBACK_CATEGORIA
            logger.warning(f"No match found for '{tipo_normalized}', using fallback: {categoria_code}")

        # Get categoria_id from code
        from immobili.models import CategoriaCatastale

        categoria = self.db.query(CategoriaCatastale).filter(
            CategoriaCatastale.codice == categoria_code
        ).first()

        if not categoria:
            logger.error(f"Categoria code '{categoria_code}' not found in database")
            return None

        # Optionally save mapping for future
        self._save_inferred_mapping(tipo_normalized, categoria.id)

        logger.info(f"Inferred categoria: {tipo_normalized} → {categoria_code} (id={categoria.id})")
        return categoria.id

    def _match_keyword(self, tipo_normalized: str) -> Optional[str]:
        """
        Match tipo against keyword dictionary.

        Tries both exact match and partial match (contains).
        Prioritizes longer matches to avoid "casa" matching "box prima casa".

        Args:
            tipo_normalized: Normalized property type

        Returns:
            Categoria code or None
        """
        # Exact match
        if tipo_normalized in self.DEFAULT_TIPO_CATEGORIA:
            code = self.DEFAULT_TIPO_CATEGORIA[tipo_normalized]
            logger.debug(f"Exact keyword match: {tipo_normalized} → {code}")
            return code

        # Partial match (contains keyword) - prioritize longer matches
        matches = []
        for keyword, code in self.DEFAULT_TIPO_CATEGORIA.items():
            if keyword in tipo_normalized:
                matches.append((len(keyword), keyword, code))

        if matches:
            # Sort by keyword length descending (longest first)
            matches.sort(reverse=True, key=lambda x: x[0])
            keyword = matches[0][1]
            code = matches[0][2]
            logger.debug(f"Partial keyword match: {tipo_normalized} contains '{keyword}' → {code}")
            return code

        logger.debug(f"No keyword match found for: {tipo_normalized}")
        return None

    def _save_inferred_mapping(
        self,
        tipo_immobile: str,
        categoria_id: int
    ) -> None:
        """
        Save auto-inferred mapping to database for future reuse.

        Creates a TipoImmobileCategoriaMap record with:
        - confidence_score: 0.8 (auto-inferred, not user-defined)
        - is_user_defined: False

        Silently fails if mapping already exists (ignore duplicates).

        Args:
            tipo_immobile: Normalized property type
            categoria_id: Inferred categoria ID
        """
        from immobili.models import TipoImmobileCategoriaMap

        # Check if mapping already exists before creating
        existing = self.db.query(TipoImmobileCategoriaMap).filter(
            TipoImmobileCategoriaMap.tipo_immobile == tipo_immobile
        ).first()

        if existing:
            logger.debug(f"Mapping already exists: {tipo_immobile} → categoria_id={existing.categoria_catastale_id}")
            return

        try:
            mapping = TipoImmobileCategoriaMap(
                tipo_immobile=tipo_immobile,
                categoria_catastale_id=categoria_id,
                confidence_score=0.8,  # Auto-inferred confidence
                is_user_defined=False
            )
            self.db.add(mapping)
            self.db.flush()  # Flush but don't commit (let caller handle transaction)
            logger.debug(f"Saved inferred mapping: {tipo_immobile} → categoria_id={categoria_id}")
        except Exception as e:
            # Ignore errors - don't rollback the entire transaction
            logger.debug(f"Could not save mapping: {e}")
            # Don't rollback - just continue

    def get_or_create_user_mapping(
        self,
        tipo_immobile: str,
        categoria_code: str
    ) -> Optional[int]:
        """
        Create or update user-defined mapping.

        Used when user explicitly maps a property type to a categoria.
        Has higher confidence (1.0) than auto-inferred mappings.

        Args:
            tipo_immobile: Property type
            categoria_code: Cadastral code (e.g., "A/2")

        Returns:
            categoria_id or None if categoria not found

        Examples:
            >>> categoria_id = service.get_or_create_user_mapping("casa signorile", "A/1")
        """
        from immobili.models import CategoriaCatastale
        from immobili.models import TipoImmobileCategoriaMap

        tipo_normalized = tipo_immobile.lower().strip()

        # Get categoria by code
        categoria = self.db.query(CategoriaCatastale).filter(
            CategoriaCatastale.codice == categoria_code.upper()
        ).first()

        if not categoria:
            logger.error(f"Categoria code '{categoria_code}' not found")
            return None

        # Check if mapping exists
        mapping = self.db.query(TipoImmobileCategoriaMap).filter(
            TipoImmobileCategoriaMap.tipo_immobile == tipo_normalized,
            TipoImmobileCategoriaMap.categoria_catastale_id == categoria.id
        ).first()

        if mapping:
            # Update to user-defined
            mapping.is_user_defined = True
            mapping.confidence_score = 1.0
        else:
            # Create new mapping
            mapping = TipoImmobileCategoriaMap(
                tipo_immobile=tipo_normalized,
                categoria_catastale_id=categoria.id,
                confidence_score=1.0,
                is_user_defined=True
            )
            self.db.add(mapping)

        self.db.commit()
        logger.info(f"Created/updated user mapping: {tipo_normalized} → {categoria_code}")
        return categoria.id
