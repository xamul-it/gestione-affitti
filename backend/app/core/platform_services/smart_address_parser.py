"""
Smart Address Parser - Intelligent Italian address parsing with GenAI fallback.

Strategy:
1. Try regex patterns (fast, free, offline)
2. If fails → Try GenAI (Groq API or Ollama)
3. Return best result with confidence score

Supports any address format through AI understanding.
"""
import re
import json
import logging
import requests
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ParserMethod(str, Enum):
    """Method used for parsing."""
    REGEX = "regex"
    GENAI_GROQ = "genai_groq"
    GENAI_OLLAMA = "genai_ollama"
    FALLBACK = "fallback"


@dataclass
class SmartAddressResult:
    """Result of smart address parsing."""
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    provincia: Optional[str] = None
    cap: Optional[str] = None
    piano: Optional[str] = None
    warnings: list = field(default_factory=list)
    success: bool = False
    confidence: float = 0.0  # 0.0 to 1.0
    method: ParserMethod = ParserMethod.FALLBACK


class SmartAddressParser:
    """
    Intelligent address parser with multiple strategies.

    Tries patterns in order of cost/speed:
    1. Regex (instant, free)
    2. Groq API (< 1sec, free)
    3. Ollama local (2-5sec, free)
    4. Keep original (fallback)

    Configuration via environment variables:
    - GROQ_API_KEY: Optional Groq API key
    - OLLAMA_BASE_URL: Default http://localhost:11434
    - ENABLE_GENAI_FALLBACK: Default True
    """

    # Existing regex patterns
    PATTERN_FULL = re.compile(
        r"^([A-ZÀ-ÿ\s']+)\s*\(([A-Z]{2})\)\s+(.+?)(?:\s+Piano\s+([^\s,]+))?$",
        re.IGNORECASE
    )

    PATTERN_SIMPLE = re.compile(
        r"^([A-Za-zÀ-ÿ\s']+?)\s+(Via|Viale|Corso|Piazza|Largo|Strada)\s+(.+?)(?:,\s*(\d+[A-Za-z]*))?$",
        re.IGNORECASE
    )

    # GenAI configuration
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    OLLAMA_API_URL = "http://localhost:11434/api/generate"
    GROQ_MODEL = "llama-3.3-70b-versatile"  # Fast and accurate
    OLLAMA_MODEL = "llama3"

    GENAI_TIMEOUT = 10  # seconds

    def __init__(self, groq_api_key: Optional[str] = None, enable_genai: bool = True):
        """
        Initialize smart parser.

        Args:
            groq_api_key: Optional Groq API key (free tier: 30 req/min)
            enable_genai: Enable GenAI fallback (default True)
        """
        self.groq_api_key = groq_api_key
        self.enable_genai = enable_genai

    def parse(self, raw_address: str) -> SmartAddressResult:
        """
        Parse address using best available method.

        Args:
            raw_address: Raw address string

        Returns:
            SmartAddressResult with parsed data and metadata
        """
        if not raw_address or not raw_address.strip():
            return SmartAddressResult(
                warnings=["Indirizzo vuoto"],
                success=False,
                confidence=0.0
            )

        raw_address = raw_address.strip()

        # Strategy 1: Try regex patterns (instant)
        result = self._try_regex(raw_address)
        if result.success and result.confidence >= 0.8:
            return result

        # Strategy 2: Try GenAI if enabled and regex failed
        if self.enable_genai:
            if self.groq_api_key:
                genai_result = self._try_groq(raw_address)
                if genai_result.success and genai_result.confidence > result.confidence:
                    return genai_result

            # Strategy 3: Try Ollama (local) if available
            ollama_result = self._try_ollama(raw_address)
            if ollama_result.success and ollama_result.confidence > result.confidence:
                return ollama_result

        # Fallback: Return regex result or original
        if not result.success:
            result.indirizzo = raw_address
            result.warnings.append("Formato non riconosciuto - GenAI non disponibile")
            result.method = ParserMethod.FALLBACK

        return result

    def _try_regex(self, raw: str) -> SmartAddressResult:
        """Try regex patterns (existing logic)."""
        result = SmartAddressResult()

        # Pattern 1: Full format
        match = self.PATTERN_FULL.match(raw)
        if match:
            result.citta = self._normalize_city(match.group(1))
            result.provincia = match.group(2).upper()
            result.indirizzo = match.group(3).strip()
            result.piano = match.group(4) if match.group(4) else None
            result.success = True
            result.confidence = 0.95
            result.method = ParserMethod.REGEX
            return result

        # Pattern 2: Simple format
        match = self.PATTERN_SIMPLE.match(raw)
        if match:
            result.citta = self._normalize_city(match.group(1))
            via_type = match.group(2).capitalize()
            via_name = match.group(3).strip()
            numero = match.group(4) if match.group(4) else ""
            result.indirizzo = f"{via_type} {via_name}" + (f", {numero}" if numero else "")
            result.success = True
            result.confidence = 0.85
            result.method = ParserMethod.REGEX
            return result

        # No pattern matched
        result.indirizzo = raw
        result.success = False
        result.confidence = 0.0
        return result

    def _try_groq(self, raw: str) -> SmartAddressResult:
        """
        Try parsing with Groq API (fast, free).

        Groq is extremely fast (< 1 second) and free tier allows 30 req/min.
        """
        if not self.groq_api_key:
            return SmartAddressResult(success=False)

        try:
            prompt = self._build_genai_prompt(raw)

            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,  # Low temperature for consistency
                "max_tokens": 200
            }

            response = requests.post(
                self.GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=self.GENAI_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Parse JSON response
            parsed = self._parse_genai_response(content)
            if parsed:
                parsed.method = ParserMethod.GENAI_GROQ
                parsed.confidence = 0.90  # High confidence for AI
                logger.info(f"Groq parsing successful for: {raw[:50]}")
                return parsed

        except Exception as e:
            logger.warning(f"Groq parsing failed: {e}")

        return SmartAddressResult(success=False)

    def _try_ollama(self, raw: str) -> SmartAddressResult:
        """
        Try parsing with Ollama (local, free, privacy-first).

        Requires Ollama running locally: ollama serve
        """
        try:
            prompt = self._build_genai_prompt(raw)

            payload = {
                "model": self.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            }

            response = requests.post(
                self.OLLAMA_API_URL,
                json=payload,
                timeout=self.GENAI_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            content = data.get("response", "")

            # Parse JSON response
            parsed = self._parse_genai_response(content)
            if parsed:
                parsed.method = ParserMethod.GENAI_OLLAMA
                parsed.confidence = 0.85  # Slightly lower than Groq
                logger.info(f"Ollama parsing successful for: {raw[:50]}")
                return parsed

        except requests.ConnectionError:
            logger.debug("Ollama not available (connection refused)")
        except Exception as e:
            logger.warning(f"Ollama parsing failed: {e}")

        return SmartAddressResult(success=False)

    def _build_genai_prompt(self, raw_address: str) -> str:
        """Build prompt for GenAI parsing."""
        return f"""Estrai i componenti da questo indirizzo italiano e rispondi SOLO con JSON valido:

Indirizzo: "{raw_address}"

Formato risposta (JSON valido senza markdown):
{{"citta": "nome città", "provincia": "sigla 2 lettere", "indirizzo": "via/viale nome, numero", "piano": "piano se presente", "cap": null}}

Esempi:
- "MILANO (MI) VIALE UMBRIA, 49 Piano 5" → {{"citta": "Milano", "provincia": "MI", "indirizzo": "VIALE UMBRIA, 49", "piano": "5", "cap": null}}
- "Via Roma 10 Torino" → {{"citta": "Torino", "provincia": null, "indirizzo": "Via Roma, 10", "piano": null, "cap": null}}

Rispondi SOLO con JSON, nessun testo aggiuntivo:"""

    def _parse_genai_response(self, content: str) -> Optional[SmartAddressResult]:
        """
        Parse GenAI JSON response.

        Handles various response formats (with/without markdown, etc.)
        """
        try:
            # Remove markdown code blocks if present
            content = content.strip()
            if content.startswith("```"):
                content = re.sub(r"```json?\n?", "", content)
                content = re.sub(r"```\n?$", "", content)

            # Parse JSON
            data = json.loads(content)

            result = SmartAddressResult()
            result.citta = data.get("citta")
            result.provincia = data.get("provincia")
            result.indirizzo = data.get("indirizzo")
            result.piano = data.get("piano")
            result.cap = data.get("cap")
            result.success = bool(result.citta or result.indirizzo)

            return result

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse GenAI JSON: {e}\nContent: {content[:200]}")
            return None

    def _normalize_city(self, city: str) -> str:
        """Normalize city name to title case."""
        city = " ".join(city.split())
        return city.title()


# Convenience function
def parse_address_smart(
    raw_address: str,
    groq_api_key: Optional[str] = None,
    enable_genai: bool = True
) -> SmartAddressResult:
    """
    Parse address with smart parser (convenience function).

    Args:
        raw_address: Raw address string
        groq_api_key: Optional Groq API key
        enable_genai: Enable GenAI fallback

    Returns:
        SmartAddressResult
    """
    parser = SmartAddressParser(groq_api_key=groq_api_key, enable_genai=enable_genai)
    return parser.parse(raw_address)
