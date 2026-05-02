"""Thai amount parser for currency values."""
from decimal import Decimal, InvalidOperation
from typing import Optional
import re
from .base_parser import BaseParser


class ThaiAmountParser(BaseParser):
    """Parse Thai currency amounts."""

    def parse(self, text: str) -> Optional[Decimal]:
        """
        Parse amount from Thai currency format.

        Supports:
        - "1,234.56"
        - "1234.56 บาท"
        - "฿1,234.56"
        - "THB 1234.56"

        Args:
            text: OCR text containing an amount

        Returns:
            Parsed Decimal or None if parsing fails
        """
        if not text:
            return None

        # Clean text
        cleaned = self.clean_text(text)

        # Try different patterns
        result = self._try_currency_pattern(cleaned)
        if result is not None:
            return result

        result = self._try_number_pattern(cleaned)
        if result is not None:
            return result

        return None

    def _try_currency_pattern(self, text: str) -> Optional[Decimal]:
        """
        Try parsing with currency symbols/keywords.

        Pattern: [symbol] number [currency]
        """
        # Pattern: optional currency symbol/keyword, number with optional commas and decimals, optional currency
        patterns = [
            r'(?:฿|THB|บาท)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:บาท|THB|฿)?',
            r'(?:จำนวนเงิน|amount)?[\s:]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1)
                return self._clean_and_parse(amount_str)

        return None

    def _try_number_pattern(self, text: str) -> Optional[Decimal]:
        """
        Try parsing as plain number with commas.

        Pattern: 1,234.56 or 1234.56
        """
        # Look for number patterns with decimals
        patterns = [
            r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2}))\b',
            r'\b(\d+(?:\.\d{2})?)\b'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                amount_str = match.group(1)
                result = self._clean_and_parse(amount_str)
                if result is not None and result > 0:
                    return result

        return None

    def _clean_and_parse(self, amount_str: str) -> Optional[Decimal]:
        """
        Clean amount string and parse to Decimal.

        Args:
            amount_str: Raw amount string (e.g., "1,234.56")

        Returns:
            Parsed Decimal or None if parsing fails
        """
        try:
            # Remove commas, currency symbols, and whitespace
            cleaned = (
                amount_str
                .replace(',', '')
                .replace('฿', '')
                .replace('บาท', '')
                .replace('THB', '')
                .strip()
            )

            if not cleaned:
                return None

            # Parse to Decimal
            return Decimal(cleaned)

        except (InvalidOperation, ValueError):
            return None
