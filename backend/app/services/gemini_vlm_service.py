"""Gemini Vision Language Model service for OCR field extraction."""
import base64
from PIL import Image
import google.generativeai as genai
from typing import Dict, Any, Optional
from datetime import date, time
from decimal import Decimal
import json
from app.config import settings


class GeminiVLMService:
    """Gemini VLM service for direct image field extraction using Gemini API."""

    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini VLM service")

        # Configure Gemini API
        genai.configure(api_key=settings.gemini_api_key)
        # Use Gemini 1.5 Flash which has vision capabilities
        self.model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
        print("✅ GeminiVLMService initialized with Gemini 3.1 Flash Lite")

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract receipt fields directly from image using Gemini Vision.

        Args:
            image_path: Path to the receipt image

        Returns:
            Dictionary containing extracted fields
        """
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        # Encode image to base64
        base64_image = self._encode_image(image_path)

        # Create prompt for structured extraction
        prompt = """Extract information from this Thai bank receipt image and return ONLY a JSON object with this exact structure:
{
  "extracted_date": "YYYY-MM-DD (in Christian era, Buddhist year - 543, if it's Buddhist era, convert to Christian era)",
  "extracted_time": "HH:MM",
  "sender": "sender name or company",
  "receiver": "Thai receiver name (starts with นาย, นาง, or นางสาว)or company",
  "amount": "numeric amount (e.g., 3000.00)",
  "note": "additional notes if present"
}

Rules:
- For dates: Convert Buddhist era (พ.ศ.) to Christian era (subtract 543)
- For dates: Thai months: เมษายน=04, มิ.ย.=06, ธ.ค.=10, พ.ย.=11, etc.
- For names: Include titles like "นาย", "นาง", "นางสาว" if present
- For amount: Return only the number without currency symbol or spaces
- If any field is not found, use null
- Return ONLY the JSON, no other text

Extract the receipt data:"""

        try:
            # Prepare input with image
            image_part = {
                "mime_type": "image/jpeg",
                "data": base64_image
            }

            # Call Gemini API with vision model
            response = self.model.generate_content(
                [prompt, image_part],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent JSON output
                    max_output_tokens=1000,
                    response_mime_type="application/json"
                )
            )

            # Extract the response
            content = response.text.strip()
            print(f"=== Gemini VLM Response ===")
            print(f"Raw content: {content}")

            # Parse JSON response
            extracted_data = json.loads(content)

            # Validate and convert types
            result = {
                "raw_text": content,
                "extracted_date": self._parse_date(extracted_data.get("extracted_date")),
                "extracted_time": self._parse_time(extracted_data.get("extracted_time")),
                "sender": extracted_data.get("sender"),
                "receiver": extracted_data.get("receiver"),
                "amount": self._parse_amount(extracted_data.get("amount")),
                "note": extracted_data.get("note"),
                "confidence_score": Decimal("0.95")  # Gemini typically has high confidence
            }

            print(f"✅ Gemini extracted data: {result}")
            return result

        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"Content was: {content}")
            # Return empty data on JSON parse error
            return self._get_empty_result()
        except Exception as e:
            print(f"❌ Gemini VLM extraction error: {e}")
            import traceback
            traceback.print_exc()
            return self._get_empty_result()

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string."""
        if not date_str or date_str == "null":
            return None

        try:
            # Try YYYY-MM-DD format
            if "-" in date_str:
                parts = date_str.split("-")
                if len(parts) == 3:
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                    if self._is_valid_date(day, month, year):
                        return date(year, month, day)

            # Try other formats
            from datetime import datetime
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                try:
                    parsed_date = datetime.strptime(date_str, fmt).date()
                    return parsed_date
                except ValueError:
                    continue
        except Exception as e:
            print(f"Date parse error: {e}")

        return None

    def _parse_time(self, time_str: Optional[str]) -> Optional[time]:
        """Parse time string."""
        if not time_str or time_str == "null":
            return None

        try:
            # Try HH:MM format
            if ":" in time_str:
                parts = time_str.split(":")
                if len(parts) >= 2:
                    hour, minute = int(parts[0]), int(parts[1])
                    second = int(parts[2]) if len(parts) > 2 else 0
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return time(hour, minute, second)
        except Exception:
            pass

        return None

    def _parse_amount(self, amount_str: Optional[str]) -> Optional[Decimal]:
        """Parse amount string."""
        if not amount_str or amount_str == "null":
            return None

        try:
            # Remove any non-numeric characters except decimal point
            cleaned = str(amount_str).replace(",", "").replace("฿", "").replace("บาท", "").strip()
            if cleaned:
                return Decimal(cleaned)
        except Exception as e:
            print(f"Amount parse error: {e}")

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

    def _get_empty_result(self) -> Dict[str, Any]:
        """Return empty result structure."""
        return {
            "raw_text": "",
            "extracted_date": None,
            "extracted_time": None,
            "sender": None,
            "receiver": None,
            "amount": None,
            "note": None,
            "confidence_score": Decimal("0.0")
        }


# Singleton instance
_gemini_vlm_service = None


def get_gemini_vlm_service() -> GeminiVLMService:
    """Get or create Gemini VLM service singleton."""
    global _gemini_vlm_service
    if _gemini_vlm_service is None:
        _gemini_vlm_service = GeminiVLMService()
    return _gemini_vlm_service
