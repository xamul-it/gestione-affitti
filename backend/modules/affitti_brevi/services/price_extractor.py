"""
Price Extractor Service

Extracts price information from iCal event descriptions using regex patterns.
Different booking platforms format prices differently in their iCal feeds.

Supported patterns:
- Booking.com: "Price: € 123.45" or "Total: EUR 123.45"
- Airbnb: "Total: $123.45" or "Nightly rate: $123"
- Vrbo: "Amount: £123.45" or "Total price: 123.45 EUR"
- Generic: "€123", "$123", "EUR 123", etc.
"""
import re
from typing import Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class PriceExtractor:
    """
    Extracts price information from iCal event text using platform-specific patterns
    """

    # Currency symbols and codes
    CURRENCY_SYMBOLS = {
        '€': 'EUR',
        '$': 'USD',
        '£': 'GBP',
        '¥': 'JPY',
        'CHF': 'CHF',
        'EUR': 'EUR',
        'USD': 'USD',
        'GBP': 'GBP',
    }

    def __init__(self):
        # Compile regex patterns for better performance
        self.patterns = [
            # Booking.com patterns
            (r'Price:\s*€\s*(\d+(?:[.,]\d{2})?)', 'EUR'),
            (r'Total:\s*EUR\s*(\d+(?:[.,]\d{2})?)', 'EUR'),
            (r'Prezzo:\s*€\s*(\d+(?:[.,]\d{2})?)', 'EUR'),

            # Airbnb patterns
            (r'Total:\s*\$\s*(\d+(?:[.,]\d{2})?)', 'USD'),
            (r'Nightly rate:\s*\$\s*(\d+(?:[.,]\d{2})?)', 'USD'),
            (r'Totale:\s*\$\s*(\d+(?:[.,]\d{2})?)', 'USD'),

            # Vrbo patterns
            (r'Amount:\s*£\s*(\d+(?:[.,]\d{2})?)', 'GBP'),
            (r'Total price:\s*(\d+(?:[.,]\d{2})?)\s*EUR', 'EUR'),
            (r'Importo:\s*€\s*(\d+(?:[.,]\d{2})?)', 'EUR'),

            # Generic patterns (fallback)
            (r'€\s*(\d+(?:[.,]\d{2})?)', 'EUR'),
            (r'\$\s*(\d+(?:[.,]\d{2})?)', 'USD'),
            (r'£\s*(\d+(?:[.,]\d{2})?)', 'GBP'),
            (r'EUR\s*(\d+(?:[.,]\d{2})?)', 'EUR'),
            (r'USD\s*(\d+(?:[.,]\d{2})?)', 'USD'),
            (r'GBP\s*(\d+(?:[.,]\d{2})?)', 'GBP'),

            # Number-only pattern (last resort)
            (r'\b(\d{2,5}(?:[.,]\d{2})?)\b', None),  # Match 2-5 digit numbers
        ]

        # Compile patterns
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), currency)
            for pattern, currency in self.patterns
        ]

    def extract_price(self, description: str, summary: str = "") -> Optional[Decimal]:
        """
        Extract price from event description and/or summary

        Args:
            description: Event DESCRIPTION field
            summary: Event SUMMARY field (optional)

        Returns:
            Extracted price as Decimal or None if not found
        """
        # Combine description and summary for searching
        text = f"{description} {summary}"

        if not text.strip():
            return None

        # Try each pattern in order (most specific first)
        for pattern, expected_currency in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                try:
                    # Extract price value
                    price_str = match.group(1)

                    # Normalize decimal separator (replace comma with dot)
                    price_str = price_str.replace(',', '.')

                    # Convert to Decimal
                    price = Decimal(price_str)

                    # Sanity check: price should be between 1 and 100000
                    if 1 <= price <= 100000:
                        logger.debug(f"Extracted price: {price} {expected_currency or 'unknown'}")
                        return price
                    else:
                        logger.debug(f"Price out of range: {price}")
                        continue

                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse price: {price_str} - {str(e)}")
                    continue

        logger.warning(f"No valid price found in text: {text[:100]}...")
        return None

    def extract_currency(self, description: str, summary: str = "") -> str:
        """
        Extract currency code from event description and/or summary

        Args:
            description: Event DESCRIPTION field
            summary: Event SUMMARY field (optional)

        Returns:
            Currency code (EUR, USD, GBP) or 'EUR' as default
        """
        text = f"{description} {summary}"

        # Look for currency symbols and codes
        for symbol, code in self.CURRENCY_SYMBOLS.items():
            if symbol in text:
                return code

        # Default to EUR
        return 'EUR'

    def extract_price_and_currency(self, description: str, summary: str = "") -> tuple[Optional[Decimal], str]:
        """
        Extract both price and currency from event text

        Args:
            description: Event DESCRIPTION field
            summary: Event SUMMARY field (optional)

        Returns:
            Tuple of (price, currency_code)
        """
        price = self.extract_price(description, summary)
        currency = self.extract_currency(description, summary) if price else 'EUR'
        return (price, currency)


# Convenience function for quick price extraction
def extract_price_from_text(text: str) -> Optional[Decimal]:
    """
    Quick price extraction from text

    Args:
        text: Text to extract price from

    Returns:
        Extracted price or None
    """
    extractor = PriceExtractor()
    return extractor.extract_price(text)
