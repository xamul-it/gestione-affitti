"""
Codice Generator Service - Generate unique property codes.

Generates unique codes for UnitaImmobiliare with format: {PROVINCIA}{00001}

Examples:
- MI00001 (Milano)
- BO00042 (Bologna)
- FO00123 (Forlì)

Usage:
    from app.core.platform_services import CodiceGeneratorService

    service = CodiceGeneratorService(db)
    codice = service.generate_codice("MI", UnitaImmobiliare)
    print(codice)  # "MI00001"
"""
from typing import Type, Any, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class CodiceGeneratorService:
    """
    Generate unique codes for UnitaImmobiliare.

    Format: {PROVINCIA_SIGLA}{PROGRESSIVE_5_DIGITS}
    - Provincia: 2-character province code (uppercase)
    - Progressive: 5-digit zero-padded number

    Features:
    - Auto-increment per province
    - Collision detection and retry
    - Fallback to "XX" for missing province
    - Progressive calculation from last record
    """

    # Default provincia for records without province
    FALLBACK_PROVINCIA = "XX"

    # Number of digits for progressive part
    PROGRESSIVE_DIGITS = 5

    def __init__(self, db: Session):
        """
        Initialize codice generator service.

        Args:
            db: Database session
        """
        self.db = db
        # Track generated codes in current session to avoid duplicates in batch imports
        self._generated_cache = {}

    def generate_codice(
        self,
        provincia: Optional[str],
        model_class: Type[Any],
        max_attempts: int = 100
    ) -> str:
        """
        Generate unique codice for a property.

        Queries the database to find the last codice for the given provincia,
        increments the progressive number, and verifies uniqueness.

        Args:
            provincia: Province code (2 chars) - can be None
            model_class: SQLAlchemy model class (e.g., UnitaImmobiliare)
            max_attempts: Max collision resolution attempts

        Returns:
            Unique codice string (e.g., "MI00042")

        Raises:
            ValueError: If cannot generate unique code after max_attempts

        Examples:
            >>> codice = service.generate_codice("MI", UnitaImmobiliare)
            >>> print(codice)
            MI00001
        """
        # Validate and normalize provincia
        if not provincia or len(provincia.strip()) != 2:
            provincia = self.FALLBACK_PROVINCIA
            logger.warning(f"Invalid provincia, using fallback: {self.FALLBACK_PROVINCIA}")

        sigla = provincia.upper().strip()
        logger.debug(f"Generating codice for provincia: {sigla}")

        for attempt in range(max_attempts):
            # Get next progressive number
            progressive = self._get_next_progressive(sigla, model_class)
            codice = f"{sigla}{progressive:0{self.PROGRESSIVE_DIGITS}d}"

            logger.debug(f"Attempt {attempt + 1}: Generated codice {codice}")

            # Check uniqueness
            exists = self.db.query(model_class).filter(
                model_class.codice == codice
            ).first()

            if not exists:
                logger.info(f"Successfully generated unique codice: {codice}")
                return codice

            logger.warning(f"Codice collision detected: {codice}, retrying...")

        # If we get here, we exhausted all attempts
        error_msg = f"Cannot generate unique codice after {max_attempts} attempts for provincia {sigla}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    def _get_next_progressive(self, sigla: str, model_class: Type[Any]) -> int:
        """
        Get next progressive number for given province.

        Queries the last record with the same provincia prefix,
        extracts the numeric part, and increments by 1.
        Uses cache to track codes generated in current session for batch imports.

        Args:
            sigla: Province code (2 chars, uppercase)
            model_class: SQLAlchemy model class

        Returns:
            Next progressive number (integer)

        Examples:
            Last record: MI00042 → returns 43
            No records: returns 1
        """
        # Check if we've generated codes for this sigla in current session
        if sigla in self._generated_cache:
            # Increment from last generated
            next_num = self._generated_cache[sigla] + 1
            self._generated_cache[sigla] = next_num
            logger.debug(f"Using cached progressive for {sigla}: {next_num}")
            return next_num

        # Query last codice with same prefix from database
        last_record = self.db.query(model_class)\
            .filter(model_class.codice.like(f"{sigla}%"))\
            .order_by(model_class.codice.desc())\
            .first()

        if last_record:
            try:
                # Extract numeric part from codice
                # Example: "MI00042" → extract "00042" → convert to 42
                numeric_part = last_record.codice[len(sigla):]
                last_num = int(numeric_part)
                next_num = last_num + 1
                # Cache the starting progressive for this sigla
                self._generated_cache[sigla] = next_num
                logger.debug(f"Last codice for {sigla}: {last_record.codice}, next progressive: {next_num}")
                return next_num
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing last codice '{last_record.codice}': {e}, starting from 1")
                self._generated_cache[sigla] = 1
                return 1

        # No records found, start from 1
        logger.debug(f"No existing records for provincia {sigla}, starting from 1")
        self._generated_cache[sigla] = 1
        return 1

    def validate_codice_format(self, codice: str) -> bool:
        """
        Validate codice format.

        Args:
            codice: Codice to validate

        Returns:
            True if valid format, False otherwise

        Examples:
            >>> service.validate_codice_format("MI00001")
            True
            >>> service.validate_codice_format("invalid")
            False
        """
        if not codice or len(codice) != (2 + self.PROGRESSIVE_DIGITS):
            return False

        # First 2 chars should be letters
        if not codice[:2].isalpha():
            return False

        # Last 5 chars should be digits
        if not codice[2:].isdigit():
            return False

        return True
