"""
Similarity Matching Service

Implements fuzzy matching algorithm to find similar SoggettoAnagrafico records
and prevent duplicate registrations.

Algorithm:
1. Codice Fiscale exact match → 100% score (definitive match)
2. Levenshtein distance on nome/cognome + data_nascita → 0-99% score
3. Threshold filtering (>= 50% for candidates)
4. Ranking by similarity score DESC

Dependencies:
    - python-Levenshtein: pip install python-Levenshtein
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)


class SimilarityMatchingService:
    """
    Service for finding similar SoggettoAnagrafico records.

    Use Cases:
        - Prevent duplicate registrations when creating from document
        - Suggest existing anagrafiche when uploading documents
        - Detect potential data entry errors
        - Merge duplicate records

    Scoring:
        - 1.0 (100%): Codice Fiscale exact match → Same person
        - 0.85-0.99: Very likely same person (nome+cognome+DOB similar)
        - 0.70-0.84: Possible match (nome+cognome similar, DOB different)
        - 0.50-0.69: Low confidence (show with warning)
        - < 0.50: Different person (filtered out)
    """

    # Similarity thresholds
    THRESHOLD_MIN = 0.50  # Minimum score to show as candidate
    THRESHOLD_HIGH = 0.85  # High confidence match
    THRESHOLD_PERFECT = 1.0  # Perfect match (CF exact)

    # Weights for composite score
    WEIGHT_NOME = 0.3
    WEIGHT_COGNOME = 0.3
    WEIGHT_DATA_NASCITA = 0.4

    def __init__(self, db: Session):
        self.db = db

    def find_similar(
        self,
        codice_fiscale: Optional[str] = None,
        nome: Optional[str] = None,
        cognome: Optional[str] = None,
        data_nascita: Optional[date] = None,
        exclude_id: Optional[int] = None,
        threshold: float = THRESHOLD_MIN
    ) -> List[Dict[str, Any]]:
        """
        Find similar SoggettoAnagrafico records.

        Args:
            codice_fiscale: Optional CF for exact matching
            nome: First name for fuzzy matching
            cognome: Last name for fuzzy matching
            data_nascita: Birth date for exact matching
            exclude_id: Exclude this soggetto_id from results
            threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of candidates sorted by similarity_score DESC:
            [
                {
                    "soggetto_id": 45,
                    "similarity_score": 1.0,
                    "match_reason": "Codice fiscale identico",
                    "match_fields": ["codice_fiscale"],
                    "soggetto": {...}  # Full soggetto data
                }
            ]
        """
        from ..models import SoggettoAnagrafico

        candidates = []

        # Strategy 1: Codice Fiscale exact match
        if codice_fiscale:
            cf_matches = self.db.query(SoggettoAnagrafico).filter(
                SoggettoAnagrafico.codice_fiscale == codice_fiscale.upper()
            )
            if exclude_id:
                cf_matches = cf_matches.filter(SoggettoAnagrafico.id != exclude_id)

            for soggetto in cf_matches.all():
                candidates.append({
                    "soggetto_id": soggetto.id,
                    "similarity_score": self.THRESHOLD_PERFECT,
                    "match_reason": "Codice fiscale identico",
                    "match_fields": ["codice_fiscale"],
                    "soggetto": self._soggetto_to_dict(soggetto)
                })

            # If CF exact match found, return immediately (no need for fuzzy)
            if candidates:
                logger.info(f"[Similarity] CF exact match: {len(candidates)} candidates")
                return candidates

        # Strategy 2: Fuzzy matching on nome/cognome
        if nome or cognome:
            # Build query
            query = self.db.query(SoggettoAnagrafico).filter(
                SoggettoAnagrafico.attivo == True
            )

            if exclude_id:
                query = query.filter(SoggettoAnagrafico.id != exclude_id)

            # Filter by partial nome/cognome to reduce search space
            if nome:
                nome_pattern = f"%{nome[:3]}%"  # First 3 chars
                query = query.filter(
                    SoggettoAnagrafico.nome.ilike(nome_pattern)
                )

            if cognome:
                cognome_pattern = f"%{cognome[:3]}%"  # First 3 chars
                query = query.filter(
                    SoggettoAnagrafico.cognome.ilike(cognome_pattern)
                )

            # Limit results for performance
            potential_matches = query.limit(100).all()

            logger.debug(
                f"[Similarity] Fuzzy search: {len(potential_matches)} potential matches "
                f"(nome={nome}, cognome={cognome})"
            )

            # Calculate similarity for each potential match
            for soggetto in potential_matches:
                score = self._calculate_similarity(
                    nome=nome,
                    cognome=cognome,
                    data_nascita=data_nascita,
                    soggetto=soggetto
                )

                if score >= threshold:
                    match_fields = []
                    match_reasons = []

                    # Determine match reason
                    if score >= 0.95:
                        match_reasons.append("Nome, cognome e data nascita molto simili")
                        match_fields = ["nome", "cognome", "data_nascita"]
                    elif score >= 0.85:
                        match_reasons.append("Nome e cognome molto simili")
                        match_fields = ["nome", "cognome"]
                    elif score >= 0.70:
                        match_reasons.append("Nome e cognome simili")
                        match_fields = ["nome", "cognome"]
                    else:
                        match_reasons.append("Possibile corrispondenza parziale")
                        match_fields = []

                    # Add data_nascita match detail
                    if data_nascita and soggetto.data_nascita:
                        if data_nascita == soggetto.data_nascita:
                            match_reasons.append("Data di nascita identica")
                        else:
                            match_reasons.append(
                                f"Data di nascita diversa "
                                f"({data_nascita.isoformat()} vs {soggetto.data_nascita.isoformat()})"
                            )

                    candidates.append({
                        "soggetto_id": soggetto.id,
                        "similarity_score": round(score, 3),
                        "match_reason": " - ".join(match_reasons),
                        "match_fields": match_fields,
                        "soggetto": self._soggetto_to_dict(soggetto)
                    })

        # Sort by similarity score DESC
        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)

        logger.info(
            f"[Similarity] Found {len(candidates)} candidates "
            f"(threshold={threshold}, nome={nome}, cognome={cognome})"
        )

        return candidates

    def _calculate_similarity(
        self,
        nome: Optional[str],
        cognome: Optional[str],
        data_nascita: Optional[date],
        soggetto
    ) -> float:
        """
        Calculate similarity score between input data and existing soggetto.

        Algorithm:
            nome_score = levenshtein_ratio(nome, soggetto.nome)
            cognome_score = levenshtein_ratio(cognome, soggetto.cognome)
            birth_score = 1.0 if exact match else 0.0

            final_score = (
                nome_score * WEIGHT_NOME +
                cognome_score * WEIGHT_COGNOME +
                birth_score * WEIGHT_DATA_NASCITA
            )

        Args:
            nome: Input first name
            cognome: Input last name
            data_nascita: Input birth date
            soggetto: Existing SoggettoAnagrafico

        Returns:
            Similarity score 0.0-1.0
        """
        nome_score = 0.0
        cognome_score = 0.0
        birth_score = 0.0

        # Nome similarity
        if nome and soggetto.nome:
            nome_score = self._levenshtein_ratio(
                nome.upper().strip(),
                soggetto.nome.upper().strip()
            )

        # Cognome similarity
        if cognome and soggetto.cognome:
            cognome_score = self._levenshtein_ratio(
                cognome.upper().strip(),
                soggetto.cognome.upper().strip()
            )

        # Data nascita exact match
        if data_nascita and soggetto.data_nascita:
            birth_score = 1.0 if data_nascita == soggetto.data_nascita else 0.0

        # Weighted average
        final_score = (
            nome_score * self.WEIGHT_NOME +
            cognome_score * self.WEIGHT_COGNOME +
            birth_score * self.WEIGHT_DATA_NASCITA
        )

        logger.debug(
            f"[Similarity] Score calculation: "
            f"nome={nome_score:.2f}, cognome={cognome_score:.2f}, birth={birth_score:.2f} "
            f"→ final={final_score:.2f}"
        )

        return final_score

    def _levenshtein_ratio(self, s1: str, s2: str) -> float:
        """
        Calculate Levenshtein similarity ratio (0.0-1.0).

        Uses python-Levenshtein library for efficiency.
        Falls back to simple difflib if Levenshtein not available.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity ratio 0.0 (completely different) to 1.0 (identical)
        """
        if not s1 or not s2:
            return 0.0

        try:
            import Levenshtein
            return Levenshtein.ratio(s1, s2)
        except ImportError:
            # Fallback to difflib if Levenshtein not installed
            logger.warning(
                "[Similarity] python-Levenshtein not installed, using difflib (slower). "
                "Install with: pip install python-Levenshtein"
            )
            from difflib import SequenceMatcher
            return SequenceMatcher(None, s1, s2).ratio()

    def _soggetto_to_dict(self, soggetto) -> Dict[str, Any]:
        """Convert SoggettoAnagrafico to dictionary"""
        return {
            "id": soggetto.id,
            "tipo_soggetto": soggetto.tipo_soggetto.value if soggetto.tipo_soggetto else None,
            "nome": soggetto.nome,
            "cognome": soggetto.cognome,
            "ragione_sociale": soggetto.ragione_sociale,
            "codice_fiscale": soggetto.codice_fiscale,
            "partita_iva": soggetto.partita_iva,
            "data_nascita": soggetto.data_nascita.isoformat() if soggetto.data_nascita else None,
            "luogo_nascita": soggetto.luogo_nascita,
            "email": soggetto.email,
            "telefono": soggetto.telefono,
            "cellulare": soggetto.cellulare,
            "indirizzo": soggetto.indirizzo,
            "citta": soggetto.citta,
            "cap": soggetto.cap,
            "provincia": soggetto.provincia,
            "attivo": soggetto.attivo,
            "created_at": soggetto.created_at.isoformat() if soggetto.created_at else None
        }

    def get_match_quality(self, score: float) -> str:
        """
        Get human-readable match quality description.

        Args:
            score: Similarity score 0.0-1.0

        Returns:
            Quality description: "perfect", "high", "medium", "low"
        """
        if score >= self.THRESHOLD_PERFECT:
            return "perfect"
        elif score >= self.THRESHOLD_HIGH:
            return "high"
        elif score >= 0.70:
            return "medium"
        elif score >= self.THRESHOLD_MIN:
            return "low"
        else:
            return "none"

    def get_recommended_action(self, score: float) -> str:
        """
        Get recommended action based on similarity score.

        Args:
            score: Similarity score 0.0-1.0

        Returns:
            Action: "USE_EXISTING", "REVIEW_MANUALLY", "CREATE_NEW"
        """
        if score >= self.THRESHOLD_PERFECT:
            return "USE_EXISTING"  # Same person (CF match)
        elif score >= self.THRESHOLD_HIGH:
            return "REVIEW_MANUALLY"  # Very likely same person
        elif score >= 0.70:
            return "REVIEW_MANUALLY"  # Possible match
        else:
            return "CREATE_NEW"  # Probably different person
