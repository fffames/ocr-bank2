"""Zone extractor for cropping and OCR processing of image regions."""
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, Dict, Any
import os


class ZoneExtractor:
    """Crop image zones and run OCR using Tesseract."""

    def __init__(self):
        """Initialize zone extractor with Tesseract configuration."""
        # Configure Tesseract for Thai + English
        # OEM 3 = Default, based on what is available
        # PSM 6 = Assume a single uniform block of text
        self.tesseract_config = r'--oem 3 --psm 6 -l tha+eng'
        print("✅ ZoneExtractor initialized with Tesseract (Thai+English)")

    def crop_zone(
        self,
        image_path: str,
        zone: Dict[str, Any],
        image_size: Tuple[int, int]
    ) -> Image.Image:
        """
        Crop specific zone from image using percentage coordinates.

        Args:
            image_path: Path to the image file
            zone: Zone dictionary with x_percent, y_percent, width_percent, height_percent
            image_size: Tuple of (width, height) of the image

        Returns:
            Cropped PIL Image

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If zone coordinates are invalid
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        width, height = image_size

        # Convert percentages to pixels
        x = int(zone['x_percent'] / 100 * width)
        y = int(zone['y_percent'] / 100 * height)
        w = int(zone['width_percent'] / 100 * width)
        h = int(zone['height_percent'] / 100 * height)

        # Validate coordinates
        if x < 0 or y < 0 or w <= 0 or h <= 0:
            raise ValueError(f"Invalid zone coordinates: x={x}, y={y}, w={w}, h={h}")

        if x + w > width or y + h > height:
            raise ValueError(
                f"Zone extends beyond image bounds: "
                f"image_size=({width}, {height}), zone=({x}, {y}, {x + w}, {y + h})"
            )

        # Open and crop image
        image = Image.open(image_path)
        cropped = image.crop((x, y, x + w, y + h))

        print(f"  Cropped zone: x={x}, y={y}, w={w}, h={h}")
        return cropped

    def preprocess_image(self, image: Image.Image, method: str = "grayscale") -> Image.Image:
        """
        Preprocess image for better OCR accuracy.

        Args:
            image: PIL Image to preprocess
            method: Preprocessing method ('grayscale', 'threshold', 'none')

        Returns:
            Preprocessed PIL Image
        """
        if method == "grayscale":
            # Convert to grayscale and enhance contrast
            image = image.convert('L')
            image = ImageEnhance.Contrast(image).enhance(2.0)
            image = ImageEnhance.Sharpness(image).enhance(2.0)

        elif method == "threshold":
            # Convert to grayscale and apply threshold
            image = image.convert('L')
            # Apply binary threshold
            image = image.point(lambda x: 0 if x < 180 else 255, '1')
            # Denoise
            image = image.filter(ImageFilter.MedianFilter())

        elif method == "none":
            # No preprocessing
            pass

        return image

    def ocr_zone(self, image: Image.Image) -> str:
        """
        Run Tesseract OCR on cropped zone.

        Args:
            image: PIL Image to OCR

        Returns:
            Extracted text
        """
        try:
            # Run Tesseract OCR
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            cleaned_text = text.strip()
            print(f"  OCR result: '{cleaned_text[:50]}...' " if len(cleaned_text) > 50 else f"  OCR result: '{cleaned_text}'")
            return cleaned_text
        except Exception as e:
            print(f"  ❌ OCR error: {e}")
            return ""

    def extract_zone_text(
        self,
        image_path: str,
        zone: Dict[str, Any],
        image_size: Tuple[int, int]
    ) -> str:
        """
        Complete pipeline: crop, preprocess, and OCR a zone.

        Args:
            image_path: Path to the image file
            zone: Zone dictionary with coordinates and preprocessing config
            image_size: Tuple of (width, height) of the image

        Returns:
            Extracted text from the zone
        """
        try:
            # Crop zone
            cropped = self.crop_zone(image_path, zone, image_size)

            # Preprocess
            preprocessor = zone.get('preprocessor', 'grayscale')
            preprocessed = self.preprocess_image(cropped, preprocessor)

            # OCR
            text = self.ocr_zone(preprocessed)

            return text

        except Exception as e:
            print(f"❌ Error extracting zone: {e}")
            return ""
