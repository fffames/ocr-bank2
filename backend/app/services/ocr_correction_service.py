"""OCR correction service for mapping incorrectly read text to correct text."""
import json
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class OCRCorrectionService:
    """Service to manage and apply OCR text corrections."""

    def __init__(self, corrections_file: str = "app/config/ocr_corrections.json"):
        """Initialize OCR correction service.

        Args:
            corrections_file: Path to JSON file containing correction mappings
        """
        self.corrections_file = Path(corrections_file)
        self.corrections: Dict[str, str] = {}
        self._load_corrections()

    def _load_corrections(self):
        """Load corrections from JSON file."""
        try:
            if self.corrections_file.exists():
                with open(self.corrections_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.corrections = data.get('corrections', {})
                logger.info(f"Loaded {len(self.corrections)} OCR corrections")
            else:
                self.corrections = {}
                logger.warning(f"Corrections file not found: {self.corrections_file}")
        except Exception as e:
            logger.error(f"Error loading corrections: {e}")
            self.corrections = {}

    def _save_corrections(self):
        """Save corrections to JSON file."""
        try:
            self.corrections_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.corrections_file, 'w', encoding='utf-8') as f:
                json.dump({'corrections': self.corrections}, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(self.corrections)} OCR corrections")
        except Exception as e:
            logger.error(f"Error saving corrections: {e}")
            raise

    def apply_corrections(self, text: str) -> str:
        """Apply correction mappings to text.

        Args:
            text: Original OCR text

        Returns:
            Corrected text
        """
        if not text:
            return text

        corrected = text
        # Sort by length (longest first) to prevent partial matches
        # e.g., "เน.ย." (length 5) should match before "น.ย." (length 4)
        sorted_corrections = sorted(self.corrections.items(), key=lambda x: len(x[0]), reverse=True)

        for wrong, right in sorted_corrections:
            corrected = corrected.replace(wrong, right)

        return corrected

    def add_correction(self, wrong_text: str, correct_text: str) -> Dict[str, str]:
        """Add a new correction mapping.

        Args:
            wrong_text: Incorrect text from OCR
            correct_text: Correct text to replace with

        Returns:
            Updated corrections dictionary
        """
        self.corrections[wrong_text] = correct_text
        self._save_corrections()
        logger.info(f"Added correction: '{wrong_text}' -> '{correct_text}'")
        return self.corrections

    def remove_correction(self, wrong_text: str) -> Dict[str, str]:
        """Remove a correction mapping.

        Args:
            wrong_text: Incorrect text to remove

        Returns:
            Updated corrections dictionary
        """
        if wrong_text in self.corrections:
            del self.corrections[wrong_text]
            self._save_corrections()
            logger.info(f"Removed correction: '{wrong_text}'")
        return self.corrections

    def get_corrections(self) -> Dict[str, str]:
        """Get all correction mappings.

        Returns:
            Dictionary of corrections
        """
        return self.corrections.copy()

    def clear_corrections(self) -> Dict[str, str]:
        """Clear all correction mappings.

        Returns:
            Empty corrections dictionary
        """
        self.corrections = {}
        self._save_corrections()
        logger.info("Cleared all corrections")
        return self.corrections

    def reload_corrections(self) -> Dict[str, str]:
        """Reload corrections from file.

        Returns:
            Updated corrections dictionary
        """
        self._load_corrections()
        logger.info(f"Reloaded {len(self.corrections)} OCR corrections from file")
        return self.corrections.copy()


# Global singleton instance
_correction_service: Optional[OCRCorrectionService] = None

def get_correction_service() -> OCRCorrectionService:
    """Get or create global OCR correction service instance.

    Returns:
        OCRCorrectionService instance
    """
    global _correction_service
    if _correction_service is None:
        _correction_service = OCRCorrectionService()
    return _correction_service
