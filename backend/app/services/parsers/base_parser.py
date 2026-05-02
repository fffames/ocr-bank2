"""Base parser class for OCR field extraction."""
from abc import ABC, abstractmethod
from typing import Any, Optional
import re


class BaseParser(ABC):
    """Base parser for extracted text fields."""

    @abstractmethod
    def parse(self, text: str) -> Optional[Any]:
        """
        Parse extracted text into structured data.

        Args:
            text: Raw OCR text from a zone

        Returns:
            Parsed and validated data, or None if parsing fails
        """
        pass

    def clean_text(self, text: str, patterns: list = None) -> str:
        """
        Clean text by removing specified patterns.

        Args:
            text: Text to clean
            patterns: List of regex patterns to remove (default: common whitespace)

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Default patterns to remove
        default_patterns = [r'\s+', r'\n+', r'\t+']
        patterns_to_remove = patterns or default_patterns

        cleaned = text
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, ' ', cleaned)

        return cleaned.strip()

    def extract_with_regex(self, text: str, pattern: str, group: int = 0) -> Optional[str]:
        """
        Extract text using regex pattern.

        Args:
            text: Text to search
            pattern: Regex pattern
            group: Capture group to return (default: 0 for entire match)

        Returns:
            Extracted text or None if not found
        """
        if not text:
            return None

        match = re.search(pattern, text)
        if match:
            return match.group(group) if group < len(match.groups()) + 1 else match.group(0)
        return None
