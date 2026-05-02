"""Thai time parser for time extraction."""
from datetime import time
from typing import Optional
import re
from .base_parser import BaseParser


class ThaiTimeParser(BaseParser):
    """Parse Thai time formats."""

    def parse(self, text: str) -> Optional[time]:
        """
        Parse Thai time formats.

        Supports:
        - "16:12" (24-hour format)
        - "04:30 PM" (12-hour format)
        - "16 นาฬิกา 12 นาที" (Thai text format)

        Args:
            text: OCR text containing a time

        Returns:
            Parsed time object or None if parsing fails
        """
        if not text:
            return None

        # Clean text
        cleaned = self.clean_text(text)

        # Try different patterns
        result = self._try_24hour_pattern(cleaned)
        if result:
            return result

        result = self._try_12hour_pattern(cleaned)
        if result:
            return result

        return None

    def _try_24hour_pattern(self, text: str) -> Optional[time]:
        """
        Try parsing 24-hour format.

        Pattern: HH:MM or HH.MM
        """
        pattern = r'(\d{1,2})[:\.](\d{2})'

        match = re.search(pattern, text)
        if not match:
            return None

        try:
            hour = int(match.group(1))
            minute = int(match.group(2))

            # Validate time
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour, minute)

        except (ValueError, AttributeError):
            pass

        return None

    def _try_12hour_pattern(self, text: str) -> Optional[time]:
        """
        Try parsing 12-hour format.

        Pattern: HH:MM AM/PM
        """
        pattern = r'(\d{1,2})[:\.](\d{2})\s*(?:AM|PM|am|pm)'

        match = re.search(pattern, text)
        if not match:
            return None

        try:
            hour = int(match.group(1))
            minute = int(match.group(2))

            # Convert to 24-hour format if PM
            if 'PM' in text.upper() or 'pm' in text:
                if hour != 12:
                    hour += 12
            elif 'AM' in text.upper() or 'am' in text:
                if hour == 12:
                    hour = 0

            # Validate time
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour, minute)

        except (ValueError, AttributeError):
            pass

        return None
