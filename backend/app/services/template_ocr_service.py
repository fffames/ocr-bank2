"""Template-based OCR service for Thai bank receipts."""
from typing import Dict, Any, Optional
from datetime import date, time
from decimal import Decimal
from PIL import Image

from .template_manager import TemplateManager
from .zone_extractor import ZoneExtractor
from .parsers.thai_date_parser import ThaiDateParser
from .parsers.thai_amount_parser import ThaiAmountParser
from .parsers.thai_name_parser import ThaiNameParser
from .parsers.thai_time_parser import ThaiTimeParser


class TemplateOCRService:
    """Template-based OCR service for Thai bank receipts."""

    def __init__(self):
        """Initialize template OCR service."""
        self.template_manager = TemplateManager()
        self.zone_extractor = ZoneExtractor()
        self.parsers = self._init_parsers()
        print("✅ TemplateOCRService initialized")

    def _init_parsers(self) -> Dict[str, Any]:
        """Initialize field parsers."""
        return {
            'thai_date': ThaiDateParser(),
            'thai_amount': ThaiAmountParser(),
            'thai_name': ThaiNameParser(),
            'time': ThaiTimeParser(),  # Use proper time parser
            'text': None,  # No parsing needed, return raw text
        }

    def extract_from_image(
        self,
        image_path: str,
        template_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract fields using template-based OCR.

        Args:
            image_path: Path to the receipt image
            template_id: Optional template ID (auto-detect if None)

        Returns:
            Dictionary containing extracted fields in the same format as current system

        Raises:
            ValueError: If template detection fails and no fallback available
            FileNotFoundError: If image doesn't exist
        """
        print(f"\n=== Processing: {image_path} ===")

        # 1. Detect or load template
        if not template_id:
            template_id = self.template_manager.detect_template(image_path)
            if template_id:
                print(f"  Auto-detected template: {template_id}")
            else:
                print("  ⚠️  Auto-detection failed, trying all available templates...")
                # Fallback: Try each available template
                template_id = self._try_all_templates(image_path)
                if template_id:
                    print(f"  ✅ Found working template: {template_id}")
                else:
                    raise ValueError(
                        "Could not auto-detect template. "
                        "Please specify template_id or create a matching template."
                    )

        template = self.template_manager.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        print(f"  Using template: {template.get('bank_name', template_id)}")

        # 2. Get image size
        try:
            image = Image.open(image_path)
            image_size = image.size
            print(f"  Image size: {image_size}")
        except Exception as e:
            raise FileNotFoundError(f"Could not open image: {e}")

        # 3. Extract text from each zone
        extracted = {}
        zones = template.get('zones', {})

        print(f"  Extracting {len(zones)} zones...")
        for field_name, zone_config in zones.items():
            print(f"\n  Processing '{field_name}':")
            try:
                text = self.zone_extractor.extract_zone_text(
                    image_path,
                    zone_config,
                    image_size
                )
                extracted[field_name] = text
            except Exception as e:
                print(f"  ❌ Error extracting '{field_name}': {e}")
                extracted[field_name] = None

        # 4. Parse extracted text
        print(f"\n  Parsing extracted text...")
        parsed = self._parse_fields(extracted, zones)

        # 5. Return in same format as current system
        result = self._format_result(parsed, extracted, template_id)
        print(f"\n=== Extraction Complete ===")
        print(f"  Date: {result.get('extracted_date')}")
        print(f"  Time: {result.get('extracted_time')}")
        print(f"  Sender: {result.get('sender')}")
        print(f"  Receiver: {result.get('receiver')}")
        print(f"  Amount: {result.get('amount')}")
        print(f"  Note: {result.get('note')}")
        print(f"========================\n")

        return result

    def _parse_fields(self, extracted: Dict[str, str], zones: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse extracted text using configured parsers.

        Args:
            extracted: Raw extracted text from each zone
            zones: Zone configurations with parser types

        Returns:
            Parsed field values
        """
        parsed = {}

        for field_name, text in extracted.items():
            if text is None:
                parsed[field_name] = None
                continue

            zone_config = zones.get(field_name, {})
            parser_type = zone_config.get('parser', 'text')

            # Get parser
            parser = self.parsers.get(parser_type)

            if parser:
                try:
                    parsed_value = parser.parse(text)
                    parsed[field_name] = parsed_value
                    print(f"    Parsed '{field_name}': {parsed_value}")
                except Exception as e:
                    print(f"    ⚠️  Error parsing '{field_name}': {e}")
                    parsed[field_name] = None  # Return None on error, not raw text
            else:
                # No parser, return raw text
                parsed[field_name] = text

        return parsed

    def _format_result(self, parsed: Dict[str, Any], raw: Dict[str, str], template_id: str) -> Dict[str, Any]:
        """
        Format result to match current system output format.

        Args:
            parsed: Parsed field values
            raw: Raw extracted text
            template_id: The template ID that was used

        Returns:
            Formatted result dictionary matching VLM/OCR service output
        """
        # Combine all raw text
        all_raw_text = ' | '.join([v for v in raw.values() if v])

        return {
            "raw_text": all_raw_text,
            "extracted_date": parsed.get('date'),
            "extracted_time": parsed.get('time'),
            "sender": parsed.get('sender_name'),
            "receiver": parsed.get('receiver_name'),
            "amount": parsed.get('amount'),
            "note": parsed.get('note'),
            "confidence_score": Decimal("0.95"),  # High confidence for template-based OCR
            "detected_template": template_id,
            "ocr_engine": "template"
        }

    def _try_all_templates(self, image_path: str) -> Optional[str]:
        """
        Try all available templates and return the first successful one.

        Args:
            image_path: Path to the receipt image

        Returns:
            First template_id that successfully extracts data, or None
        """
        available_templates = list(self.template_manager.templates.keys())

        for tid in available_templates:
            try:
                print(f"  🔧 Trying template: {tid}")
                # Try to extract with this template
                result = self._extract_with_template(image_path, tid)

                # Check if we got meaningful data (at least some fields)
                if result and self._is_valid_extraction(result):
                    print(f"  ✅ Template '{tid}' produced valid extraction")
                    return tid
                else:
                    print(f"  ⚠️  Template '{tid}' produced no valid data")
            except Exception as e:
                print(f"  ❌ Template '{tid}' failed: {e}")
                continue

        return None

    def _extract_with_template(self, image_path: str, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract using a specific template without auto-detection.

        Args:
            image_path: Path to the receipt image
            template_id: Template ID to use

        Returns:
            Extraction result or None if failed
        """
        try:
            template = self.template_manager.get_template(template_id)
            if not template:
                return None

            # Get image size
            from PIL import Image
            image = Image.open(image_path)
            image_size = image.size

            # Extract text from each zone
            extracted = {}
            zones = template.get('zones', {})

            for field_name, zone_config in zones.items():
                try:
                    text = self.zone_extractor.extract_zone_text(
                        image_path,
                        zone_config,
                        image_size
                    )
                    extracted[field_name] = text
                except Exception:
                    extracted[field_name] = None

            # Parse extracted text
            parsed = self._parse_fields(extracted, zones)

            # Return in same format as current system
            return self._format_result(parsed, extracted, template_id)

        except Exception as e:
            print(f"    Error during extraction: {e}")
            return None

    def _is_valid_extraction(self, result: Dict[str, Any]) -> bool:
        """
        Check if extraction produced valid data.

        Args:
            result: Extraction result

        Returns:
            True if result has meaningful data
        """
        # Check if we got at least some meaningful fields
        meaningful_fields = 0
        if result.get('amount'):
            meaningful_fields += 1
        if result.get('extracted_date'):
            meaningful_fields += 1
        if result.get('sender') or result.get('receiver'):
            meaningful_fields += 1

        return meaningful_fields >= 1


# Singleton instance
_template_ocr_service = None


def get_template_ocr_service() -> TemplateOCRService:
    """Get or create TemplateOCRService singleton."""
    global _template_ocr_service
    if _template_ocr_service is None:
        _template_ocr_service = TemplateOCRService()
    return _template_ocr_service
