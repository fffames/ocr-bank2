from paddleocr import PaddleOCR
from PIL import Image
import re
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, Dict, Any
import os
from app.config import settings


class OCRService:
    def __init__(self):
        # Initialize PaddleOCR with Thai language support
        # Note: PaddleOCR 3.0+ removed use_gpu and show_log parameters
        try:
            self.ocr = PaddleOCR(lang='th', det_model_dir=None, rec_model_dir=None)

            # Log model information
            print("=== PaddleOCR Model Information ===")
            print(f"Language: {settings.ocr_language}")
            print(f"Use Angle Classification: True")
            print(f"PaddleOCR Version: 3.x")
            print(f"Detection Model: PP-OCRv3 Detection (ch_PP-OCRv3_det)")
            print(f"Recognition Model: PP-OCRv3 Multilingual (supports Thai)")
            print("=====================================")

        except Exception as e:
            print(f"Error initializing PaddleOCR: {e}")
            # Fallback to minimal initialization
            self.ocr = PaddleOCR(lang=settings.ocr_language)

    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text and structured data from receipt image.

        Args:
            image_path: Path to the receipt image

        Returns:
            Dictionary containing:
                - raw_text: Full OCR text
                - extracted_date: Extracted date
                - extracted_time: Extracted time
                - sender: Sender name
                - receiver: Receiver name
                - amount: Transaction amount
                - note: Additional notes
                - confidence_score: Average OCR confidence
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Perform OCR
        # Note: PaddleOCR 3.0+ automatically uses angle classification if enabled during init
        result = self.ocr.ocr(image_path)

        # Extract text and confidence scores
        raw_text = []
        confidences = []

        try:
            # PaddleOCR 3.0+ format: result is a list with one dict containing 'rec_texts' and 'rec_scores'
            if result and len(result) > 0 and isinstance(result[0], dict):
                ocr_data = result[0]

                # Get extracted texts and scores
                if 'rec_texts' in ocr_data and 'rec_scores' in ocr_data:
                    rec_texts = ocr_data['rec_texts']
                    rec_scores = ocr_data['rec_scores']

                    for i, text_content in enumerate(rec_texts):
                        if text_content:
                            raw_text.append(str(text_content))
                            if i < len(rec_scores):
                                confidences.append(float(rec_scores[i]))

                    print(f"✅ Extracted {len(raw_text)} text lines from image")
                    for i, text in enumerate(raw_text[:10]):  # Print first 10
                        print(f"  [{i}] {text}")
                    if len(raw_text) > 10:
                        print(f"  ... and {len(raw_text) - 10} more lines")
                else:
                    print("⚠️  No 'rec_texts' or 'rec_scores' in OCR result")
            else:
                print("⚠️  Unexpected OCR result format")
                print(f"Result type: {type(result)}")
                print(f"Result: {result}")

        except Exception as e:
            print(f"Error parsing OCR result: {e}")
            import traceback
            traceback.print_exc()

        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # Combine all text
        full_text = "\n".join(raw_text) if raw_text else ""

        # Extract structured fields with error handling
        try:
            extracted_data = {
                "raw_text": full_text,
                "extracted_date": self._extract_date(full_text),
                "extracted_time": self._extract_time(full_text),
                "sender": self._extract_sender(full_text),
                "receiver": self._extract_receiver(full_text),
                "amount": self._extract_amount(full_text),
                "note": self._extract_note(full_text),
                "confidence_score": Decimal(str(avg_confidence))
            }
        except Exception as e:
            print(f"Error extracting fields: {e}")
            # Return minimal data on error
            extracted_data = {
                "raw_text": full_text,
                "extracted_date": None,
                "extracted_time": None,
                "sender": None,
                "receiver": None,
                "amount": None,
                "note": None,
                "confidence_score": Decimal(str(avg_confidence))
            }

        return extracted_data

    def _extract_date(self, text: str) -> Optional[date]:
        """Extract date from OCR text (supports Buddhist era and Thai months)."""
        if not text:
            return None

        # Thai month names
        thai_months = {
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

        try:
            # Pattern 1: DD Month YYYY (Thai month, Buddhist era)
            # e.g., "15 เมษายน 2567" or "15 พ.ค. 2567"
            pattern1 = r'(\d{1,2})\s+([^\d\s]+\.?)\s+(\d{4})'
            for match in re.finditer(pattern1, text):
                try:
                    day = int(match.group(1))
                    month_text = match.group(2)
                    year_be = int(match.group(3))

                    # Convert Thai month to number
                    month = thai_months.get(month_text)
                    if month:
                        # Convert Buddhist era to Christian era
                        year_ce = year_be - 543
                        if self._is_valid_date(day, month, year_ce):
                            return date(year_ce, month, day)
                except (ValueError, AttributeError, IndexError):
                    continue

            # Pattern 2: DD/MM/YYYY or DD-MM-YYYY format
            # e.g., "15/04/2567" or "15-04-2567"
            pattern2 = r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4}|\d{2})'
            for match in re.finditer(pattern2, text):
                try:
                    day = int(match.group(1))
                    month = int(match.group(2))
                    year = int(match.group(3))

                    # If year is in Buddhist era (>= 2400), convert to Christian era
                    if year >= 2400:
                        year = year - 543
                    elif year < 100:  # Two-digit year
                        year = 2000 + year

                    if self._is_valid_date(day, month, year):
                        return date(year, month, day)
                except (ValueError, AttributeError, IndexError):
                    continue

        except Exception as e:
            print(f"Error extracting date: {e}")

        return None

    def _extract_time(self, text: str) -> Optional[time]:
        """Extract time from OCR text."""
        if not text:
            return None

        # Time patterns (HH:MM:SS, HH:MM)
        time_patterns = [
            r'\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b',
        ]

        try:
            for pattern in time_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    try:
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        second = int(match.group(3)) if match.group(3) else 0

                        if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                            return time(hour, minute, second)
                    except (ValueError, AttributeError, IndexError):
                        continue
        except Exception as e:
            print(f"Error extracting time: {e}")

        return None

    def _extract_sender(self, text: str) -> Optional[str]:
        """Extract sender name from OCR text."""
        if not text:
            return None

        try:
            lines = text.split('\n')

            # Keywords that indicate a name (title prefix)
            name_prefixes = ['นาย', 'นาง', 'นางสาว', 'Mr.', 'Mrs.', 'Ms.', 'ดร.', 'Dr.']

            # First, look for "จาก" (from) keyword
            for i, line in enumerate(lines):
                if 'จาก' in line:
                    # Get the rest of the line after "จาก"
                    parts = line.split('จาก', 1)
                    if len(parts) > 1:
                        potential_name = parts[1].strip()
                        if potential_name:
                            return potential_name

                    # If name is on the next line
                    if i + 1 < len(lines) and lines[i + 1].strip():
                        next_line = lines[i + 1].strip()
                        if any(prefix in next_line for prefix in name_prefixes) or len(next_line.split()) <= 5:
                            return next_line
                    break

            # If no "จาก" keyword found, extract the first name-like entity
            # Look for lines with name prefixes
            for line in lines:
                line = line.strip()
                if any(prefix in line for prefix in name_prefixes):
                    # Extract the name (usually after the prefix)
                    for prefix in name_prefixes:
                        if prefix in line:
                            parts = line.split(prefix, 1)
                            if len(parts) > 1:
                                return parts[1].strip()

            # If no name prefix found, return the first short line (likely a name)
            for line in lines:
                line = line.strip()
                # Skip empty lines, very long lines (descriptions), or single characters
                if 2 < len(line) < 50 and not any(char.isdigit() for char in line):
                    # Check if it looks like a name (mostly Thai/letters)
                    words = line.split()
                    if len(words) <= 5:  # Names usually have at most 5 words
                        return line

        except Exception as e:
            print(f"Error extracting sender: {e}")

        return None

    def _extract_receiver(self, text: str) -> Optional[str]:
        """Extract receiver name from OCR text."""
        if not text:
            return None

        try:
            lines = text.split('\n')

            # Keywords that indicate a name (title prefix)
            name_prefixes = ['นาย', 'นาง', 'นางสาว', 'Mr.', 'Mrs.', 'Ms.', 'ดร.', 'Dr.']

            # First, look for "ไปยัง" (to) keyword
            for i, line in enumerate(lines):
                if 'ไปยัง' in line:
                    # Get the rest of the line after "ไปยัง"
                    parts = line.split('ไปยัง', 1)
                    if len(parts) > 1:
                        potential_name = parts[1].strip()
                        if potential_name:
                            return potential_name

                    # If name is on the next line
                    if i + 1 < len(lines) and lines[i + 1].strip():
                        next_line = lines[i + 1].strip()
                        if any(prefix in next_line for prefix in name_prefixes) or len(next_line.split()) <= 5:
                            return next_line
                    break

            # If no "ไปยัง" keyword found, extract the last name-like entity
            # Collect all potential names
            potential_names = []

            # Look for lines with name prefixes
            for line in lines:
                line = line.strip()
                if any(prefix in line for prefix in name_prefixes):
                    # Extract the name (usually after the prefix)
                    for prefix in name_prefixes:
                        if prefix in line:
                            parts = line.split(prefix, 1)
                            if len(parts) > 1:
                                potential_names.append(parts[1].strip())

            # If found names with prefixes, return the last one
            if potential_names:
                return potential_names[-1]

            # If no name prefix found, return the last short line (likely a name)
            last_short_line = None
            for line in lines:
                line = line.strip()
                # Skip empty lines, very long lines (descriptions), or single characters
                if 2 < len(line) < 50 and not any(char.isdigit() for char in line):
                    # Check if it looks like a name
                    words = line.split()
                    if len(words) <= 5:  # Names usually have at most 5 words
                        last_short_line = line

            if last_short_line:
                return last_short_line

        except Exception as e:
            print(f"Error extracting receiver: {e}")

        return None

    def _extract_amount(self, text: str) -> Optional[Decimal]:
        """Extract transaction amount from OCR text."""
        if not text:
            return None

        # Amount patterns with Thai currency and decimal formats
        amount_patterns = [
            r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:บาท|THB|฿)\b',
            r'\b(?:จำนวนเงิน|amount)[\s:]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',
        ]

        try:
            for pattern in amount_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        if match.group(1):
                            amount_str = match.group(1).replace(',', '')
                            return Decimal(amount_str)
                    except (ValueError, AttributeError, IndexError):
                        continue
        except Exception as e:
            print(f"Error extracting amount: {e}")

        return None

    def _extract_note(self, text: str) -> Optional[str]:
        """Extract additional notes from OCR text."""
        if not text:
            return None

        try:
            # Look for common note patterns
            lines = text.split('\n')
            note_lines = []

            # Keywords that indicate note content
            note_keywords = ['หมายเหตุ', 'note', 'memo', 'ข้อความ']

            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in note_keywords):
                    # Collect subsequent lines as note content
                    if ':' in line:
                        note_content = line.split(':', 1)[1].strip() if len(line.split(':', 1)) > 1 else ''
                        if note_content:
                            note_lines.append(note_content)

                        # Add next few lines as part of the note
                        for j in range(i + 1, min(i + 4, len(lines))):
                            if lines[j].strip():
                                note_lines.append(lines[j].strip())
                            else:
                                break
                    break

            return ' '.join(note_lines) if note_lines else None
        except Exception as e:
            print(f"Error extracting note: {e}")
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


# Singleton instance
_ocr_service = None


def get_ocr_service() -> OCRService:
    """Get or create OCR service singleton."""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
