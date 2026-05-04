"""Template-based OCR service for Thai bank receipts."""
from typing import Dict, Any, Optional
from datetime import date, time
from decimal import Decimal
from PIL import Image

from .template_manager import TemplateManager
from .zone_extractor import ZoneExtractor
from .ocr_correction_service import get_correction_service
from .parsers.thai_date_parser import ThaiDateParser
from .parsers.thai_amount_parser import ThaiAmountParser
from .parsers.thai_name_parser import ThaiNameParser
from .parsers.thai_time_parser import ThaiTimeParser
from ..config import settings


class TemplateOCRService:
    """Template-based OCR service for Thai bank receipts."""

    def __init__(self, ocr_engine: Optional[str] = None):
        """
        Initialize template OCR service.

        Args:
            ocr_engine: OCR engine to use ('tesseract', 'paddleocr', or None for auto-detect from settings)
        """
        self.template_manager = TemplateManager()

        # Determine OCR engine to use
        if ocr_engine is None:
            # Use settings from config.py (which reads from .env or defaults)
            ocr_engine = settings.ocr_engine

        self.zone_extractor = ZoneExtractor(ocr_engine=ocr_engine)
        self.parsers = self._init_parsers()
        print(f"✅ TemplateOCRService initialized with {ocr_engine}")

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
        Extract fields using template-based OCR with fallback support.

        Template Fallback Logic:
        1. Try main template (e.g., 'SCB')
        2. If any field is null, try backup templates (e.g., 'SCB_B', 'SCB_B2', ...)
        3. Merge results from each successful template
        4. If all templates exhausted and still have nulls, caller should use LLM fallback

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

        # 2. Get backup templates and try them in order
        template_chain = self._get_template_chain(template_id)
        print(f"  Template chain: {template_chain}")

        # Initialize result with all null fields
        merged_result = {
            "raw_text": "",
            "extracted_date": None,
            "extracted_time": None,
            "sender": None,
            "receiver": None,
            "amount": None,
            "note": None,
            "confidence_score": Decimal("0.95"),
            "detected_template": template_id,
            "ocr_engine": "template"
        }

        # Track which templates were successfully used
        used_templates = []

        # 3. Try each template in the chain
        for current_template_id in template_chain:
            print(f"\n  🎯 Trying template: {current_template_id}")

            try:
                # Extract with current template
                result = self._extract_with_template(image_path, current_template_id)

                if result:
                    # Merge non-null fields from this result
                    null_fields_before = self._count_null_fields(merged_result)

                    for key, value in result.items():
                        if value is not None and merged_result.get(key) is None:
                            merged_result[key] = value
                            print(f"    ✅ Filled '{key}': {value}")

                    null_fields_after = self._count_null_fields(merged_result)
                    filled_count = null_fields_before - null_fields_after

                    if filled_count > 0:
                        used_templates.append(current_template_id)
                        print(f"    ✓ Template '{current_template_id}' filled {filled_count} fields")

                    # Check if all fields are filled
                    if null_fields_after == 0:
                        print(f"\n  🎉 All fields filled! No need to try more templates.")
                        break
                else:
                    print(f"    ⚠️  Template '{current_template_id}' produced no results")

            except Exception as e:
                print(f"    ❌ Template '{current_template_id}' failed: {e}")
                continue

        # 4. Update metadata based on templates used
        if used_templates:
            if len(used_templates) == 1:
                merged_result["detected_template"] = used_templates[0]
                merged_result["ocr_engine"] = "template"
            else:
                # Multiple templates were used
                merged_result["detected_template"] = f"{used_templates[0]}+{len(used_templates)-1}"
                merged_result["ocr_engine"] = "template+fallback"
                # Lower confidence when using fallback templates
                merged_result["confidence_score"] = Decimal("0.85")

        # 5. Display final result
        print(f"\n=== Extraction Complete ===")
        print(f"  Templates used: {', '.join(used_templates) if used_templates else 'None'}")
        print(f"  Date: {merged_result.get('extracted_date')}")
        print(f"  Time: {merged_result.get('extracted_time')}")
        print(f"  Sender: {merged_result.get('sender')}")
        print(f"  Receiver: {merged_result.get('receiver')}")
        print(f"  Amount: {merged_result.get('amount')}")
        print(f"  Note: {merged_result.get('note')}")
        print(f"  Null fields remaining: {self._count_null_fields(merged_result)}")
        print(f"========================\n")

        return merged_result

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

        # Get OCR correction service
        correction_service = get_correction_service()

        for field_name, text in extracted.items():
            if text is None:
                parsed[field_name] = None
                continue

            zone_config = zones.get(field_name, {})
            parser_type = zone_config.get('parser', 'text')

            # Apply OCR corrections before parsing
            corrected_text = correction_service.apply_corrections(text)

            if corrected_text != text:
                print(f"    Applied corrections to '{field_name}': '{text}' -> '{corrected_text}'")

            # Get parser
            parser = self.parsers.get(parser_type)

            if parser:
                try:
                    parsed_value = parser.parse(corrected_text)
                    parsed[field_name] = parsed_value
                    print(f"    Parsed '{field_name}': {parsed_value}")
                except Exception as e:
                    print(f"    ⚠️  Error parsing '{field_name}': {e}")
                    parsed[field_name] = None  # Return None on error, not raw text
            else:
                # No parser, return corrected text
                parsed[field_name] = corrected_text

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

    def _get_template_chain(self, template_id: str) -> list[str]:
        """
        Get the chain of templates to try: main template + backup templates.

        Args:
            template_id: The main template ID (e.g., 'SCB')

        Returns:
            List of template IDs in order to try: ['SCB', 'SCB_B', 'SCB_B2', ...]
        """
        template_chain = [template_id]

        # Get all available templates
        all_templates = list(self.template_manager.templates.keys())

        # Find backup templates (same base name with _B, _B2, _B3, etc.)
        import re

        # Extract base name (remove any existing _B suffix)
        base_name = re.sub(r'_B\d*$', '', template_id)

        # Find all backup templates for this base name
        backup_pattern = re.compile(f'^{re.escape(base_name)}_B\\d*$')

        backup_templates = [t for t in all_templates if backup_pattern.match(t)]

        # Sort backup templates (_B, _B2, _B3, ...)
        def backup_sort_key(backup_id):
            match = re.search(r'_B(\d*)$', backup_id)
            if match:
                num = match.group(1)
                return int(num) if num else 0
            return 0

        backup_templates.sort(key=backup_sort_key)

        # Add to chain
        template_chain.extend(backup_templates)

        return template_chain

    def _count_null_fields(self, result: Dict[str, Any]) -> int:
        """
        Count how many key fields are null in the result.

        Args:
            result: Extraction result

        Returns:
            Number of null key fields
        """
        key_fields = ['extracted_date', 'extracted_time', 'sender', 'receiver', 'amount']
        null_count = 0

        for field in key_fields:
            if result.get(field) is None:
                null_count += 1

        return null_count


# Singleton instance
_template_ocr_service = None


def get_template_ocr_service() -> TemplateOCRService:
    """Get or create TemplateOCRService singleton."""
    global _template_ocr_service
    if _template_ocr_service is None:
        _template_ocr_service = TemplateOCRService()
    return _template_ocr_service
