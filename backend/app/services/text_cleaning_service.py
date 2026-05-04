"""Text cleaning service for OCR post-processing.

This service is currently disabled/placeholder.
Original functionality would clean OCR-extracted text using LLM.
"""

from typing import Dict, Any, Optional


class TextCleaningService:
    """Service for cleaning OCR-extracted text data."""

    def clean_extracted_data(
        self,
        extracted_data: Dict[str, str],
        user_name: str,
        name_variations: list = None
    ) -> Dict[str, str]:
        """
        Clean OCR-extracted data using user name and variations.

        Args:
            extracted_data: Raw OCR extracted data
            user_name: User's actual name
            name_variations: List of name variations for fuzzy matching

        Returns:
            Cleaned data (same as input if cleaning is disabled)
        """
        # Currently disabled - return data as-is
        return extracted_data


# Singleton instance
_text_cleaning_service = None


def get_text_cleaning_service() -> TextCleaningService:
    """Get or create text cleaning service singleton."""
    global _text_cleaning_service
    if _text_cleaning_service is None:
        _text_cleaning_service = TextCleaningService()
    return _text_cleaning_service
