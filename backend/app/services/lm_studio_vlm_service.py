from openai import OpenAI
import base64
from PIL import Image
import io
from typing import Dict, Any, Optional
from datetime import date, time
from decimal import Decimal
import json
from app.config import settings


class LMStudioVLMService:
    """LM Studio Vision Language Model service for local image field extraction."""

    def __init__(self):
        if not settings.local_llm_url:
            raise ValueError("LOCAL_LLM_URL must be configured for LM Studio VLM service")

        # Initialize OpenAI client for LM Studio (LM Studio uses OpenAI-compatible API)
        self.client = OpenAI(
            base_url=settings.local_llm_url,
            api_key="not-needed"  # LM Studio doesn't require API key
        )
        # Vision model - use a model that supports vision
        # Common vision models available in LM Studio:
        # - llava-phi-3
        # - llava-v1.5-7b
        # - bakllava
        # - minigpt-4
        self.model = "llava-v1.5-7b"  # Default vision model, can be changed

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract receipt fields directly from image using local VLM.

        Args:
            image_path: Path to the receipt image

        Returns:
            Dictionary containing extracted fields
        """
        # Encode image to base64
        base64_image = self._encode_image(image_path)

        # Create prompt for structured extraction
        prompt = """You are a receipt data extractor. Extract information from this Thai bank receipt image and return ONLY a valid JSON object. Do not include any explanations, markdown formatting, or additional text.

Your response must be EXACTLY in this format (no deviations):
{
  "extracted_date": "YYYY-MM-DD",
  "extracted_time": "HH:MM",
  "sender": "sender name or company",
  "receiver": "receiver name or company",
  "amount": "3000.00",
  "note": "additional notes if present"
}

CRITICAL RULES:
1. Return ONLY the JSON object above, nothing else
2. For dates: Convert Buddhist era (พ.ศ. 2568 = 2025) by subtracting 543
3. For Thai dates: เม.ย.=04, มิ.ย.=06, ธ.ค.=12, พ.ย.=11
4. For amount: Return ONLY digits and decimal point (e.g., "3000.00"), no currency symbols
5. Include name titles (นาย, นาง, นางสาว) in sender/receiver fields
6. Use null for missing fields, do not make up values

Now extract the data from this receipt:"""

        try:
            # Call LM Studio API with vision model
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1,  # Low temperature for consistent JSON output
                max_tokens=1000
            )

            # Extract the response
            content = response.choices[0].message.content.strip()
            print(f"=== LM Studio VLM Response ===")
            print(f"Raw content: {content}")

            # Parse JSON response
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

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
                "confidence_score": Decimal("0.95")  # VLM typically has high confidence
            }

            print(f"✅ Extracted data: {result}")
            return result

        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"Content was: {content}")
            # Return empty data on JSON parse error
            return self._get_empty_result()
        except Exception as e:
            print(f"❌ LM Studio VLM extraction error: {e}")
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
_lm_studio_vlm_service = None


def get_lm_studio_vlm_service() -> LMStudioVLMService:
    """Get or create LM Studio VLM service singleton."""
    global _lm_studio_vlm_service
    if _lm_studio_vlm_service is None:
        _lm_studio_vlm_service = LMStudioVLMService()
    return _lm_studio_vlm_service
