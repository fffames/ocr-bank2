"""Zone extractor for cropping and OCR processing of image regions."""
import pytesseract
from paddleocr import PaddleOCR
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, Dict, Any
import os
import numpy as np


class ZoneExtractor:
    """Crop image zones and run OCR using Tesseract or PaddleOCR."""

    def __init__(self, ocr_engine: str = "paddleocr"):
        """
        Initialize zone extractor with specified OCR engine.

        Args:
            ocr_engine: OCR engine to use ('tesseract' or 'paddleocr')
        """
        self.ocr_engine = ocr_engine.lower()

        if self.ocr_engine == "paddleocr":
            # Initialize PaddleOCR for Thai (same as old working code)
            self.ocr = PaddleOCR(lang='th', det_model_dir=None, rec_model_dir=None)
            print("✅ ZoneExtractor initialized with PaddleOCR (Thai)")
        else:
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

    def preprocess_for_tesseract(self, image: Image.Image, method: str = "grayscale") -> Image.Image:
        """
        Preprocess image for Tesseract OCR.

        Args:
            image: PIL Image to preprocess
            method: Preprocessing method ('grayscale', 'threshold', 'enhanced', 'none')

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

        elif method == "enhanced":
            # Enhanced preprocessing for difficult OCR
            # 1. Convert to grayscale
            image = image.convert('L')

            # 2. Upscale 2x for better OCR
            original_size = image.size
            image = image.resize((original_size[0] * 2, original_size[1] * 2), Image.Resampling.LANCZOS)

            # 3. Enhance contrast
            image = ImageEnhance.Contrast(image).enhance(3.0)

            # 4. Apply sharpening
            image = ImageEnhance.Sharpness(image).enhance(3.0)

            # 5. Convert to pure black/white (binarize)
            image = image.point(lambda x: 0 if x < 140 else 255, '1')

            # 6. Remove noise with median filter
            image = image.filter(ImageFilter.MinFilter(size=3))

            # 7. Downscale back to original size
            image = image.resize(original_size, Image.Resampling.LANCZOS)

        elif method == "none":
            # No preprocessing
            pass

        return image

    def preprocess_for_paddleocr(self, image: Image.Image, method: str = "grayscale") -> Image.Image:
        """
        Preprocess image for PaddleOCR.

        Note: PaddleOCR works best with RGB or grayscale images.
        Avoid '1' mode (boolean) as it causes OpenCV errors.

        Args:
            image: PIL Image to preprocess
            method: Preprocessing method ('grayscale', 'enhanced', 'none')

        Returns:
            Preprocessed PIL Image
        """
        if method == "grayscale":
            # Convert to grayscale and enhance
            image = image.convert('L')
            image = ImageEnhance.Contrast(image).enhance(2.0)
            image = ImageEnhance.Sharpness(image).enhance(2.0)
            # Convert back to RGB for PaddleOCR
            image = image.convert('RGB')

        elif method == "enhanced":
            # Enhanced preprocessing for PaddleOCR
            # 1. Convert to grayscale
            image = image.convert('L')

            # 2. Upscale 2x for better OCR
            original_size = image.size
            image = image.resize((original_size[0] * 2, original_size[1] * 2), Image.Resampling.LANCZOS)

            # 3. Enhance contrast
            image = ImageEnhance.Contrast(image).enhance(3.0)

            # 4. Apply sharpening
            image = ImageEnhance.Sharpness(image).enhance(3.0)

            # 5. Downscale back to original size
            image = image.resize(original_size, Image.Resampling.LANCZOS)

            # Convert to RGB for PaddleOCR (NOT '1' mode)
            image = image.convert('RGB')

        elif method == "none":
            # Ensure RGB mode for PaddleOCR
            if image.mode != 'RGB':
                image = image.convert('RGB')

        return image

    def ocr_zone_tesseract(self, image: Image.Image) -> str:
        """Run Tesseract OCR on cropped zone."""
        try:
            # Run Tesseract OCR
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            cleaned_text = text.strip()
            print(f"  OCR result (Tesseract): '{cleaned_text[:50]}...' " if len(cleaned_text) > 50 else f"  OCR result (Tesseract): '{cleaned_text}'")
            return cleaned_text
        except Exception as e:
            print(f"  ❌ Tesseract OCR error: {e}")
            return ""

    def ocr_zone_paddleocr(self, image: Image.Image) -> str:
        """Run PaddleOCR on cropped zone.

        IMPORTANT: PaddleOCR works best with file paths, not numpy arrays.
        This saves the cropped image to a temp file and passes the path.
        """
        try:
            # Save cropped image to temp file
            # PaddleOCR handles image loading and preprocessing internally
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                # Ensure image is in RGB mode before saving
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                image.save(tmp.name)
                tmp_path = tmp.name

            # Run PaddleOCR with file path (like the old working code)
            result = self.ocr.ocr(tmp_path)

            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass

            if not result or not result[0]:
                print("  OCR result (PaddleOCR): '' (no text detected)")
                return ""

            # Extract text - handle both old and new PaddleOCR formats (like old working code)
            texts = []

            # Try new PaddleOCR 3.0+ format (dict with 'rec_texts')
            if result and len(result) > 0 and isinstance(result[0], dict):
                ocr_data = result[0]

                if 'rec_texts' in ocr_data and 'rec_scores' in ocr_data:
                    rec_texts = ocr_data['rec_texts']
                    rec_scores = ocr_data['rec_scores']

                    for i, text_content in enumerate(rec_texts):
                        if text_content:
                            texts.append(str(text_content))

                    print(f"  ✅ Extracted {len(texts)} text lines from image")
                    for i, text in enumerate(texts[:10]):
                        print(f"    [{i}] {text}")
                    if len(texts) > 10:
                        print(f"    ... and {len(texts) - 10} more lines")
                else:
                    print("  ⚠️  No 'rec_texts' or 'rec_scores' in OCR result")

            # Try old format (list of [[bbox, (text, confidence)], ...])
            elif result and len(result) > 0 and isinstance(result[0], list):
                for line in result[0]:
                    if line and len(line) > 1:
                        text_info = line[1]
                        if text_info and len(text_info) > 0:
                            text = text_info[0]
                            if text:
                                texts.append(text)
            else:
                print("  ⚠️  Unexpected OCR result format")
                print(f"  Result type: {type(result)}")

            cleaned_text = ' '.join(texts).strip()
            if cleaned_text:
                print(f"  OCR result (PaddleOCR): '{cleaned_text[:50]}...' " if len(cleaned_text) > 50 else f"  OCR result (PaddleOCR): '{cleaned_text}'")
            return cleaned_text

        except Exception as e:
            print(f"  ❌ PaddleOCR error: {e}")
            import traceback
            traceback.print_exc()
            return ""

    def ocr_zone(self, image: Image.Image) -> str:
        """
        Run OCR on cropped zone using selected engine.

        Args:
            image: PIL Image to OCR

        Returns:
            Extracted text
        """
        if self.ocr_engine == "paddleocr":
            return self.ocr_zone_paddleocr(image)
        else:
            return self.ocr_zone_tesseract(image)

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

            # Preprocess based on OCR engine
            preprocessor = zone.get('preprocessor', 'grayscale')
            if self.ocr_engine == "paddleocr":
                preprocessed = self.preprocess_for_paddleocr(cropped, preprocessor)
            else:
                preprocessed = self.preprocess_for_tesseract(cropped, preprocessor)

            # OCR
            text = self.ocr_zone(preprocessed)

            return text

        except Exception as e:
            print(f"❌ Error extracting zone: {e}")
            return ""
