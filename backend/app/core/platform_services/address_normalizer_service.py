import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), "../../../modules")
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

"""
Address Normalizer Service - Platform service for Italian address parsing.

Provides intelligent address normalization for Italian addresses:
- Parse composite addresses (e.g., "MILANO (MI) VIA UMBRIA, 49")
- Extract city, province, street, floor
- Lookup CAP (postal code) from database
- Fail-safe: warnings don't block import

Usage:
    from app.core.platform_services import AddressNormalizerService

    service = AddressNormalizerService(db)
    result = service.normalize_address("MILANO (MI) VIALE UMBRIA, 49 Piano 5")

    if result.success:
        print(f"City: {result.citta}, CAP: {result.cap}")
"""
from typing import Optional, List
from dataclasses import dataclass, field
import re
import unicodedata
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


@dataclass
class AddressParseResult:
    """
    Result of address parsing operation.

    Attributes:
        indirizzo: Extracted street address
        citta: City name (normalized)
        provincia: Province code (2 chars, uppercase)
        cap: Postal code
        piano: Floor number/description
        warnings: List of warning messages
        success: True if parsing was successful
    """
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    provincia: Optional[str] = None
    cap: Optional[str] = None
    piano: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    success: bool = False


class AddressNormalizerService:
    """
    Platform service for Italian address normalization.

    Capabilities:
    - Parse composite addresses with multiple regex patterns
    - Extract city, province, street, CAP, floor
    - Lookup CAP from comuni_italia database
    - Fail-safe: warnings don't block import
    - Support for various Italian address formats

    Supported formats:
    1. Full: "CITTÀ (PROV) VIA NOME, NUMERO Piano X"
    2. Simple: "Città Via Nome, Numero"
    3. Fallback: Keep original for manual review
    """

    # Regex patterns for Italian addresses
    # Pattern 1: Full format with province - "MILANO (MI) VIALE UMBRIA, 49 Piano 5-S1"
    PATTERN_FULL = re.compile(
        r"^([A-ZÀ-ÿ\s']+)\s*\(([A-Z]{2})\)\s+(.+?)(?:\s+Piano\s+([^\s,]+))?$",
        re.IGNORECASE
    )

    # Pattern 2: Simple format - "Milano Via Roma, 1"
    PATTERN_SIMPLE = re.compile(
        r"^([A-Za-zÀ-ÿ\s']+?)\s+(Via|Viale|Corso|Piazza|Largo|Strada|Str\.?|V\.le)\s+(.+?)(?:,\s*(\d+[A-Za-z]*))?$",
        re.IGNORECASE
    )

    def __init__(self, db: Session):
        """
        Initialize address normalizer service.

        Args:
            db: Database session for CAP lookups
        """
        self.db = db

    def normalize_address(
        self,
        raw_address: str,
        existing_citta: Optional[str] = None,
        existing_provincia: Optional[str] = None,
        existing_cap: Optional[str] = None
    ) -> AddressParseResult:
        """
        Main normalization method.

        Parses a raw address string and enriches it with database lookups.
        Existing values take priority over parsed values (don't overwrite good data).

        Args:
            raw_address: Raw address string from CSV
            existing_citta: Already populated city field (has priority)
            existing_provincia: Already populated province field (has priority)
            existing_cap: Already populated CAP field (has priority)

        Returns:
            AddressParseResult with extracted/inferred data and warnings

        Examples:
            >>> result = service.normalize_address("MILANO (MI) VIALE UMBRIA, 49")
            >>> print(result.citta, result.provincia, result.indirizzo)
            Milano MI VIALE UMBRIA, 49
        """
        result = AddressParseResult()

        if not raw_address or not raw_address.strip():
            result.warnings.append("Indirizzo vuoto")
            logger.debug("Empty address provided")
            return result

        raw_address = raw_address.strip()
        logger.debug(f"Normalizing address: {raw_address}")

        # Try parsing with patterns
        parsed = self._parse_with_patterns(raw_address)

        # Merge with existing data (existing has priority)
        result.indirizzo = parsed.indirizzo if not existing_citta else raw_address
        result.citta = existing_citta if existing_citta else parsed.citta
        result.provincia = existing_provincia if existing_provincia else parsed.provincia
        result.cap = existing_cap if existing_cap else parsed.cap
        result.piano = parsed.piano

        # Attempt CAP lookup if missing
        if not result.cap and result.citta:
            logger.debug(f"Attempting CAP lookup for city: {result.citta}")
            cap_lookup = self._lookup_cap(result.citta, result.provincia)
            if cap_lookup:
                result.cap = cap_lookup
                logger.info(f"CAP found: {cap_lookup} for {result.citta}")
            else:
                warning = f"Impossibile determinare CAP per {result.citta}"
                result.warnings.append(warning)
                logger.warning(warning)

        # Validate provincia format
        if result.provincia and len(result.provincia) != 2:
            warning = f"Provincia '{result.provincia}' non valida (deve essere 2 caratteri)"
            result.warnings.append(warning)
            logger.warning(warning)
            result.provincia = None

        # Mark success if we extracted something useful
        result.success = bool(result.indirizzo or result.citta)
        result.warnings.extend(parsed.warnings)

        logger.debug(f"Normalization result - Success: {result.success}, Warnings: {len(result.warnings)}")
        return result

    def _parse_with_patterns(self, raw: str) -> AddressParseResult:
        """
        Try multiple regex patterns to extract address components.

        Args:
            raw: Raw address string

        Returns:
            AddressParseResult with extracted components
        """
        result = AddressParseResult()

        # Pattern 1: Full format "CITTÀ (PROV) VIA X, N Piano Y"
        match = self.PATTERN_FULL.match(raw)
        if match:
            result.citta = self._normalize_city_name(match.group(1))
            result.provincia = match.group(2).upper()
            result.indirizzo = match.group(3).strip()
            result.piano = match.group(4) if match.group(4) else None
            result.success = True
            logger.debug(f"Matched PATTERN_FULL: città={result.citta}, prov={result.provincia}")
            return result

        # Pattern 2: Simple format "Città Via Nome, Numero"
        match = self.PATTERN_SIMPLE.match(raw)
        if match:
            result.citta = self._normalize_city_name(match.group(1))
            via_type = match.group(2).capitalize()
            via_name = match.group(3).strip()
            numero = match.group(4) if match.group(4) else ""
            result.indirizzo = f"{via_type} {via_name}" + (f", {numero}" if numero else "")
            result.success = True
            logger.debug(f"Matched PATTERN_SIMPLE: città={result.citta}")
            return result

        # Fallback: keep original
        result.indirizzo = raw
        result.warnings.append("Formato indirizzo non riconosciuto - mantenuto originale")
        logger.info(f"No pattern matched for: {raw}")

        return result

    def _normalize_city_name(self, city: str) -> str:
        """
        Normalize city name to proper case.

        Args:
            city: Raw city name

        Returns:
            Normalized city name (Title Case, trimmed)
        """
        # Remove extra whitespace
        city = " ".join(city.split())
        # Convert to title case
        city = city.title()
        # Handle apostrophes correctly
        city = city.replace("'", "'")
        return city

    def _lookup_cap(self, citta: str, provincia: Optional[str] = None) -> Optional[str]:
        """
        Lookup CAP (postal code) from comuni_italia table.

        Uses normalized city name for fuzzy matching.
        Province code used for disambiguation when provided.

        Args:
            citta: City name
            provincia: Province code (optional, for disambiguation)

        Returns:
            CAP string or None if not found
        """
        from anagrafica_italiana.models import ComuneItalia

        citta_norm = self._normalize_for_lookup(citta)

        query = self.db.query(ComuneItalia).filter(
            ComuneItalia.nome_normalized == citta_norm
        )

        if provincia:
            query = query.filter(ComuneItalia.provincia_sigla == provincia.upper())

        comune = query.first()

        return comune.cap if comune else None

    def _normalize_for_lookup(self, text: str) -> str:
        """
        Normalize text for database lookup.

        Converts to lowercase and removes accents for fuzzy matching.

        Args:
            text: Text to normalize

        Returns:
            Normalized text (lowercase, no accents)
        """
        text = text.lower().strip()
        # Remove accents using Unicode NFD normalization
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        return text
