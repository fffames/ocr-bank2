"""Thai date parser with Buddhist era conversion."""
from datetime import date
from typing import Optional
import re
from .base_parser import BaseParser


class ThaiDateParser(BaseParser):
    """Parse Thai dates with Buddhist era conversion."""

    # Thai month mappings
    THAI_MONTHS = {
        'มกราคม': 1, 'ม.ค.': 1, 'มค': 1,
        'กุมภาพันธ์': 2, 'ก.พ.': 2, 'กพ': 2,
        'มีนาคม': 3, 'มี.ค.': 3, 'มีค': 3,
        'เมษายน': 4, 'เม.ย.': 4, 'มย': 4,
        'พฤษภาคม': 5, 'พ.ค.': 5, 'พค': 5,
        'มิถุนายน': 6, 'มิ.ย.': 6, 'มย': 6,
        'กรกฎาคม': 7, 'ก.ค.': 7, 'กค': 7,
        'สิงหาคม': 8, 'ส.ค.': 8, 'สค': 8,
        'กันยายน': 9, 'ก.ย.': 9, 'กย': 9,
        'ตุลาคม': 10, 'ต.ค.': 10, 'ตค': 10,
        'พฤศจิกายน': 11, 'พ.ย.': 11, 'พย': 11,
        'ธันวาคม': 12, 'ธ.ค.': 12, 'ธค': 12
    }

    def parse(self, text: str) -> Optional[date]:
        """
        Parse Thai date formats.

        Supports:
        - "28 ม.ค. 69" (short year, Buddhist era)
        - "28 มกราคม 2567" (full year, Buddhist era)
        - "28/01/2024" (Christian era)
        - "28-01-2024" (Christian era)
        - OCR error correction for common misreads

        Args:
            text: OCR text containing a date

        Returns:
            Parsed date object or None if parsing fails
        """
        if not text:
            return None

        # Clean text first
        cleaned = self.clean_text(text)

        # Apply OCR error correction for Thai characters
        cleaned = self._correct_ocr_errors(cleaned)

        # Try different patterns
        result = self._try_thai_month_pattern(cleaned)
        if result:
            return result

        result = self._try_slash_pattern(cleaned)
        if result:
            return result

        return None

    def _correct_ocr_errors(self, text: str) -> str:
        """
        Correct common OCR errors in Thai text.

        Tesseract often misreads Thai characters as similar-looking Latin letters.
        This method fixes common misreads based on visual similarity.
        """
        # Common OCR misreads mapping (Latin → Thai)
        # Order matters: more specific patterns first
        ocr_corrections = {
            # February (ก.พ.) - commonly misread as n.w. due to visual similarity
            'n.w.': 'ก.พ.',
            'n w.': 'ก.พ.',
            'n.w': 'ก.พ.',
            'n w': 'ก.พ.',

            # January (ม.ค.)
            'm.w.': 'ม.ค.',
            'm w.': 'ม.ค.',
            'm.w': 'ม.ค.',
            'ม.c.': 'ม.ค.',
            'ม c': 'ม.ค.',

            # March (มี.ค.)
            'm.y.': 'มี.ค.',
            'm y.': 'มี.ค.',
            'm i.': 'มี.ค.',

            # April (เม.ย.)
            'a.y.': 'เม.ย.',
            'เ m.': 'เม.ย.',
            'เ m': 'เม.ย.',

            # May (พ.ค.)
            'p.c.': 'พ.ค.',
            'พ c': 'พ.ค.',

            # June (มิ.ย.)
            'm.c.': 'มิ.ย.',
            'm i.': 'มิ.ย.',
            'ม y.': 'มิ.ย.',

            # July (ก.ค.)
            'k.k.': 'ก.ค.',
            'k k.': 'ก.ค.',
            'ก k': 'ก.ค.',

            # August (ส.ค.)
            's.k.': 'ส.ค.',
            'ส c': 'ส.ค.',
            's k': 'ส.ค.',

            # September (ก.ย.)
            'k.y.': 'ก.ย.',
            'k y.': 'ก.ย.',
            'ก y': 'ก.ย.',

            # October (ต.ค.)
            't.k.': 'ต.ค.',
            'ต c': 'ต.ค.',
            't k': 'ต.ค.',

            # November (พ.ย.)
            'p.y.': 'พ.ย.',
            'พ y': 'พ.ย.',
            'พ y.': 'พ.ย.',

            # December (ธ.ค.)
            'th.k.': 'ธ.ค.',
            'ธ c': 'ธ.ค.',
            't k.': 'ธ.ค.',
        }

        corrected = text
        for wrong, right in ocr_corrections.items():
            corrected = corrected.replace(wrong, right)

        return corrected

    def _try_thai_month_pattern(self, text: str) -> Optional[date]:
        """
        Try parsing Thai date with month name.

        Pattern: DD Month YYYY (e.g., "28 ม.ค. 2567" or "28ม.ค.67")
        """
        # Pattern: DD Month YY/YYYY (with or without spaces)
        # Handle: "28 ม.ค. 69", "28ม.ค.69", "1เม.ย. 69"
        pattern = r'(\d{1,2})\s*([^\d\s,]+\.?)\s+(\d{2,4})'

        match = re.search(pattern, text)
        if not match:
            return None

        try:
            day = int(match.group(1))
            month_text = match.group(2)
            year = int(match.group(3))

            # Convert Thai month to number
            month = self.THAI_MONTHS.get(month_text)
            if not month:
                return None

            # Convert Buddhist era to Christian era if needed
            if year >= 2400:  # Full 4-digit Buddhist era
                year = year - 543
            elif year < 100:  # Two-digit year (likely Buddhist era for Thai receipts)
                # Assume Buddhist era: 69 = 2567, 67 = 2567, etc.
                year = 2500 + year - 543  # Convert to Christian era
            else:
                # Already in Christian era (3-digit years are unusual but handle them)
                year = year

            # Validate date
            if self._is_valid_date(day, month, year):
                return date(year, month, day)

        except (ValueError, AttributeError):
            pass

        return None

    def _try_slash_pattern(self, text: str) -> Optional[date]:
        """
        Try parsing date with slashes/dashes.

        Pattern: DD/MM/YYYY or DD-MM-YYYY
        """
        pattern = r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4}|\d{2})'

        match = re.search(pattern, text)
        if not match:
            return None

        try:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3))

            # Convert Buddhist era to Christian era if needed
            if year >= 2400:  # Buddhist era
                year = year - 543
            elif year < 100:  # Two-digit year
                year = 2000 + year

            # Validate date
            if self._is_valid_date(day, month, year):
                return date(year, month, day)

        except (ValueError, AttributeError):
            pass

        return None

    def _is_valid_date(self, day: int, month: int, year: int) -> bool:
        """Validate date components."""
        if not (1 <= month <= 12):
            return False
        if not (1 <= day <= 31):
            return False
        if year < 1900 or year > 2100:
            return False
        return True
