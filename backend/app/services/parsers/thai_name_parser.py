"""Thai name parser for extracting names with titles."""
from typing import Optional
import re
from .base_parser import BaseParser


class ThaiNameParser(BaseParser):
    """Parse Thai names with title prefixes."""

    # Thai and English name title prefixes
    NAME_PREFIXES = [
        'นาย', 'นาง', 'นางสาว',  # Thai titles
        'Mr.', 'Mrs.', 'Ms.', 'Miss',  # English titles
        'ดร.', 'Dr.', 'ผศ.', 'Asst.Prof.', 'รศ.', 'Assoc.Prof.', 'ศ.', 'Prof.'
    ]

    # Keywords to remove from names
    CLEAN_PATTERNS = [
        r'^จาก\s*',      # "from" at the start
        r'^ไปยัง\s*',    # "to" at the start
        r'^ผู้ส่ง\s*',   # "sender" at the start
        r'^ผู้รับ\s*',   # "receiver" at the start
    ]

    def parse(self, text: str) -> Optional[str]:
        """
        Extract Thai name with title prefix.

        Args:
            text: OCR text containing a name

        Returns:
            Cleaned name or None if parsing fails
        """
        if not text:
            return None

        # Clean text
        cleaned = self.clean_text(text)

        # Remove common prefix patterns
        cleaned = self._remove_prefixes(cleaned)

        # Extract name with title
        name = self._extract_name_with_title(cleaned)
        if name:
            return name

        # If no title found, return cleaned text if it looks like a name
        if self._looks_like_name(cleaned):
            return cleaned

        return None

    def _remove_prefixes(self, text: str) -> str:
        """Remove common prefix patterns from text."""
        for pattern in self.CLEAN_PATTERNS:
            text = re.sub(pattern, '', text)
        return text.strip()

    def _extract_name_with_title(self, text: str) -> Optional[str]:
        """
        Extract name that has a title prefix.

        Returns the name with its title preserved.
        """
        for prefix in self.NAME_PREFIXES:
            if prefix in text:
                # Split by prefix and take the part after it
                parts = text.split(prefix, 1)
                if len(parts) > 1:
                    # Include the title in the result
                    name_with_title = prefix + parts[1].strip()
                    # Validate that it looks like a name
                    if self._looks_like_name(name_with_title):
                        return name_with_title

        return None

    def _looks_like_name(self, text: str) -> bool:
        """
        Check if text looks like a name.

        Criteria:
        - Length between 2 and 100 characters
        - Not mostly digits
        - Not mostly special characters
        - Contains at least some Thai or letters
        """
        if not text:
            return False

        # Length check
        if len(text) < 2 or len(text) > 100:
            return False

        # Count different character types
        total_chars = len(text)
        digit_count = sum(1 for c in text if c.isdigit())
        special_count = sum(1 for c in text if not c.isalnum() and not c.isspace())

        # Should not be mostly digits or special characters
        if digit_count / total_chars > 0.5:
            return False

        if special_count / total_chars > 0.3:
            return False

        # Should have at least some letters/Thai characters
        letter_count = sum(1 for c in text if c.isalpha() or ord(c) > 127)
        if letter_count < 2:
            return False

        return True
