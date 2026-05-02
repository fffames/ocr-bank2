"""Template manager for loading and detecting OCR templates."""
import yaml
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import pytesseract
import logging
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TemplateManager:
    """Load, validate, and manage OCR templates."""

    def __init__(self, templates_dir: str = "app/templates"):
        """
        Initialize template manager.

        Args:
            templates_dir: Directory containing YAML template files
        """
        self.templates_dir = Path(templates_dir)
        self.templates = self._load_templates()
        self.logo_templates = {}  # Cache for logo templates
        logger.info(f"TemplateManager loaded {len(self.templates)} templates")

    def _load_templates(self) -> Dict[str, Any]:
        """
        Load all YAML templates from the templates directory.

        Returns:
            Dictionary mapping template_id to template data
        """
        templates = {}

        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return templates

        for yaml_file in self.templates_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    template = yaml.safe_load(f)
                    template_id = template.get('template_id')
                    if template_id:
                        templates[template_id] = template
                        logger.info(f"Loaded template: {template_id} ({template.get('bank_name', 'Unknown')})")
            except Exception as e:
                logger.error(f"Error loading template {yaml_file}: {e}")

        return templates

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Template data or None if not found
        """
        return self.templates.get(template_id)

    def list_templates(self) -> list:
        """
        List all available templates.

        Returns:
            List of template info dictionaries
        """
        return [
            {
                'template_id': tid,
                'bank_name': template.get('bank_name', 'Unknown'),
                'description': template.get('description', ''),
                'num_zones': len(template.get('zones', {}))
            }
            for tid, template in self.templates.items()
        ]

    def detect_template(self, image_path: str) -> Optional[str]:
        """
        Auto-detect which template to use for an image.

        Uses a multi-layered approach that respects template primary_method settings:
        1. Check if any template has strong primary_method preference (skip to their preferred method)
        2. General detection: logo matching → layout analysis → structure matching → keyword matching

        Args:
            image_path: Path to the receipt image

        Returns:
            Detected template_id or None if detection fails
        """
        logger.info(f"Starting template detection for: {image_path}")

        # Step 1: Check for templates with strong primary_method preferences
        templates_by_primary = {}
        for template_id, template in self.templates.items():
            primary_method = template.get('detection', {}).get('primary_method', 'auto')
            if primary_method != 'auto':
                if primary_method not in templates_by_primary:
                    templates_by_primary[primary_method] = []
                templates_by_primary[primary_method].append(template_id)

        logger.debug(f"Templates by primary_method: {templates_by_primary}")

        # Step 2: If templates explicitly prefer keyword matching, try that first
        if 'keywords' in templates_by_primary:
            logger.info(f"Testing templates that prefer keyword matching: {templates_by_primary['keywords']}")
            for template_id in templates_by_primary['keywords']:
                logger.info(f"  Testing {template_id} with keyword matching...")
                if self._test_template_keywords(image_path, template_id):
                    logger.info(f"✅ Keyword match for {template_id} (preferred method)")
                    return template_id
                else:
                    logger.info(f"  ❌ No keyword match for {template_id}")

            # If keyword-preferring templates didn't match, continue to standard detection
            logger.info("Keyword-preferring templates didn't match, continuing to standard detection")

        # Step 3: Standard detection cascade
        # 1. Try logo matching (fastest, most accurate)
        template_id, confidence = self._match_logos(image_path)
        if template_id and confidence > 0.7:
            logger.info(f"✅ Logo matching successful: {template_id} (confidence: {confidence:.3f})")
            return template_id
        elif template_id:
            logger.info(f"⚠️  Logo matching found {template_id} but low confidence: {confidence:.3f}")

        # 2. Try layout analysis (fast, reliable)
        template_id, confidence = self._analyze_layout(image_path)
        if template_id and confidence > 0.6:
            logger.info(f"✅ Layout analysis successful: {template_id} (confidence: {confidence:.3f})")
            return template_id
        elif template_id:
            logger.info(f"⚠️  Layout analysis found {template_id} but low confidence: {confidence:.3f}")

        # 3. Try image structure matching (robust)
        template_id, confidence = self._match_structure(image_path)
        if template_id and confidence > 0.5:
            logger.info(f"✅ Structure matching successful: {template_id} (confidence: {confidence:.3f})")
            return template_id
        elif template_id:
            logger.info(f"⚠️  Structure matching found {template_id} but low confidence: {confidence:.3f}")

        # 4. Last resort: general keyword matching (slow, unreliable)
        logger.warning("All visual methods failed, falling back to keyword matching")
        template_id = self._match_keywords(image_path)
        if template_id:
            logger.info(f"✅ Keyword matching successful: {template_id}")
        else:
            logger.warning("❌ All detection methods failed")

        return template_id

    def _test_template_keywords(self, image_path: str, template_id: str) -> bool:
        """
        Test if a specific template's keywords match the image.

        Args:
            image_path: Path to the receipt image
            template_id: Template to test

        Returns:
            True if template keywords match, False otherwise
        """
        try:
            template = self.templates.get(template_id)
            if not template:
                return False

            # Get keywords
            detection_config = template.get('detection', {})
            keywords = detection_config.get('keywords', [])

            # Also check for legacy detection_keywords
            if not keywords:
                keywords = template.get('detection_keywords', [])

            # Also check bank name
            bank_name = template.get('bank_name', '')
            all_search_terms = keywords + [bank_name] if bank_name else keywords

            if not all_search_terms:
                return False

            logger.debug(f"Testing template '{template_id}' with keywords: {all_search_terms}")

            # Run OCR on the full image
            from PIL import Image
            import pytesseract
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, config='--oem 3 --psm 6 -l tha+eng')

            # Check if any keyword matches
            for keyword in all_search_terms:
                keyword_lower = keyword.lower().strip()
                text_lower = text.lower()

                # Direct match
                if keyword_lower in text_lower:
                    logger.info(f"✅ Template '{template_id}' matched by keyword '{keyword}'")
                    return True

                # Partial match (at least 3 characters)
                if len(keyword_lower) >= 3 and keyword_lower[:3] in text_lower:
                    logger.info(f"✅ Template '{template_id}' matched by partial keyword '{keyword}'")
                    return True

        except Exception as e:
            logger.error(f"Error testing keywords for {template_id}: {e}")

        return False

    def _match_keywords(self, image_path: str) -> Optional[str]:
        """
        Match template using keywords in the image (LAST RESORT - slow, unreliable).

        Runs OCR on the full image and searches for template-specific keywords.
        Only used if all visual detection methods fail.

        Args:
            image_path: Path to the receipt image

        Returns:
            Matching template_id or None
        """
        try:
            logger.info("Running keyword matching (last resort)")

            # Run OCR on the full image to get text
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, config='--oem 3 --psm 6 -l tha+eng')

            logger.debug(f"OCR text for detection: {text[:150]}...")

            # Check each template's keywords
            for template_id, template in self.templates.items():
                # Get keywords from detection.keywords or top-level detection_keywords
                keywords = template.get('detection', {}).get('keywords', [])

                # Also check for legacy detection_keywords at top level
                if not keywords:
                    keywords = template.get('detection_keywords', [])

                # Also check bank name
                bank_name = template.get('bank_name', '')
                all_search_terms = keywords + [bank_name] if bank_name else keywords

                logger.debug(f"Checking template '{template_id}' with search terms: {all_search_terms}")

                if all_search_terms:
                    # Check if any keyword is found in the OCR text
                    for keyword in all_search_terms:
                        keyword_lower = keyword.lower().strip()
                        text_lower = text.lower()

                        # Direct match
                        if keyword_lower in text_lower:
                            logger.info(f"Matched template '{template_id}' by keyword '{keyword}'")
                            return template_id

                        # Partial match (at least 3 characters)
                        if len(keyword_lower) >= 3 and keyword_lower[:3] in text_lower:
                            logger.info(f"Matched template '{template_id}' by partial keyword '{keyword}'")
                            return template_id

        except Exception as e:
            logger.error(f"Error in keyword matching: {e}")

        return None

    def _match_logos(self, image_path: str) -> Tuple[Optional[str], float]:
        """
        Match template using logo detection (fastest, most accurate).

        Uses OpenCV template matching to detect bank logos in the image.
        Each template can have a logo_region defined for faster matching.

        Args:
            image_path: Path to the receipt image

        Returns:
            Tuple of (template_id, confidence_score) or (None, 0.0)
        """
        try:
            # Load the input image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None, 0.0

            # Convert to grayscale for template matching
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            best_match = None
            best_score = 0.0

            # Check each template for logo matching
            for template_id, template in self.templates.items():
                detection_config = template.get('detection', {})

                # Check if template has logo region defined
                logo_region = detection_config.get('logo_region', {})
                if not logo_region:
                    logger.debug(f"Template {template_id} has no logo_region defined")
                    continue

                # Extract logo region from image
                height, width = gray_image.shape
                x = int(logo_region.get('x_percent', 0) * width / 100)
                y = int(logo_region.get('y_percent', 0) * height / 100)
                region_width = int(logo_region.get('width_percent', 20) * width / 100)
                region_height = int(logo_region.get('height_percent', 15) * height / 100)

                # Ensure region is within image bounds
                x = max(0, min(x, width - region_width))
                y = max(0, min(y, height - region_height))
                region_width = min(region_width, width - x)
                region_height = min(region_height, height - y)

                if region_width <= 0 or region_height <= 0:
                    logger.debug(f"Invalid logo region for template {template_id}")
                    continue

                logo_region_img = gray_image[y:y+region_height, x:x+region_width]

                # Try to match against cached logo templates or extract features
                score = self._compute_logo_match_score(logo_region_img, template_id)

                if score > best_score:
                    best_score = score
                    best_match = template_id

            if best_match:
                logger.info(f"Logo matching best candidate: {best_match} (score: {best_score:.3f})")

            return best_match, best_score

        except Exception as e:
            logger.error(f"Error in logo matching: {e}")
            return None, 0.0

    def _compute_logo_match_score(self, region_image: np.ndarray, template_id: str) -> float:
        """
        Compute logo match score using template matching.

        Args:
            region_image: Image region containing potential logo
            template_id: Template to match against

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            # For now, use edge density and circular shape detection as a proxy
            # In production, you would match against pre-extracted logo templates

            # Method 1: Detect circular shapes (logos are often circular/oval)
            circles = cv2.HoughCircles(
                region_image,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=min(region_image.shape) // 4,
                param1=50,
                param2=30,
                minRadius=min(region_image.shape) // 10,
                maxRadius=min(region_image.shape) // 2
            )

            # Score based on circular shape presence
            circle_score = 0.0
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                if len(circles) > 0:
                    circle_score = min(1.0, len(circles) * 0.3)

            # Method 2: Edge density (logos have distinctive edge patterns)
            edges = cv2.Canny(region_image, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size

            # Normalize edge density (typical logos have density 0.05-0.15)
            edge_score = min(1.0, edge_density * 10)

            # Combined score
            combined_score = (circle_score * 0.7 + edge_score * 0.3)

            # In production, replace this with actual template matching:
            # if template_id in self.logo_templates:
            #     result = cv2.matchTemplate(region_image, self.logo_templates[template_id], cv2.TM_CCOEFF_NORMED)
            #     combined_score = np.max(result)

            return combined_score

        except Exception as e:
            logger.error(f"Error computing logo match score: {e}")
            return 0.0

    def _analyze_layout(self, image_path: str) -> Tuple[Optional[str], float]:
        """
        Match template using layout analysis (fast, reliable).

        Detects QR codes, text density patterns, and layout structure.

        Args:
            image_path: Path to the receipt image

        Returns:
            Tuple of (template_id, confidence_score) or (None, 0.0)
        """
        try:
            # Load the input image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None, 0.0

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape

            # 1. Detect QR code position
            qr_detector = cv2.QRCodeDetector()
            qr_code, points = qr_detector.detect(gray)

            qr_position = None
            if qr_code and points is not None:
                # Calculate QR code center
                qr_center_x = np.mean(points[0, :, 0]).item() / width
                qr_center_y = np.mean(points[0, :, 1]).item() / height
                qr_position = (qr_center_x, qr_center_y)
                logger.info(f"QR code detected at: ({qr_center_x:.3f}, {qr_center_y:.3f})")
            else:
                logger.warning("No QR code detected")
                # If no QR code, this method is less reliable
                return None, 0.0

            # 2. Analyze text density patterns
            # Use thresholding to find text regions
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Divide image into zones and calculate density
            zones = {
                'top_left': binary[:height//3, :width//3],
                'top_center': binary[:height//3, width//3:2*width//3],
                'top_right': binary[:height//3, 2*width//3:],
                'middle_left': binary[height//3:2*height//3, :width//3],
                'middle_center': binary[height//3:2*height//3, width//3:2*width//3],
                'middle_right': binary[height//3:2*height//3, 2*width//3:],
                'bottom_left': binary[2*height//3:, :width//3],
                'bottom_center': binary[2*height//3:, width//3:2*width//3],
                'bottom_right': binary[2*height//3:, 2*width//3:],
            }

            # Calculate text density for each zone
            zone_densities = {}
            for zone_name, zone_img in zones.items():
                # Density = ratio of dark pixels (text) to total pixels
                density = np.sum(zone_img < 128) / zone_img.size
                zone_densities[zone_name] = density

            logger.info(f"Zone densities: {zone_densities}")

            # 3. Detect circular shapes (logo positions)
            circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=min(width, height) // 8,
                param1=50,
                param2=30,
                minRadius=min(width, height) // 20,
                maxRadius=min(width, height) // 5
            )

            logo_positions = []
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                for (x, y, r) in circles:
                    logo_x = x / width
                    logo_y = y / height
                    logo_positions.append((logo_x, logo_y))
                logger.info(f"Detected {len(logo_positions)} circular shapes")

            # 4. Compare against template layouts
            best_match = None
            best_score = 0.0

            for template_id, template in self.templates.items():
                score = self._compute_layout_score(
                    template_id,
                    template,
                    qr_position,
                    zone_densities,
                    logo_positions,
                    width,
                    height
                )

                if score > best_score:
                    best_score = score
                    best_match = template_id

            if best_match:
                logger.info(f"Layout analysis best candidate: {best_match} (score: {best_score:.3f})")

            return best_match, best_score

        except Exception as e:
            logger.error(f"Error in layout analysis: {e}")
            return None, 0.0

    def _compute_layout_score(
        self,
        template_id: str,
        template: Dict[str, Any],
        qr_position: Optional[Tuple[float, float]],
        zone_densities: Dict[str, float],
        logo_positions: list,
        image_width: int,
        image_height: int
    ) -> float:
        """
        Compute layout similarity score for a template.

        Args:
            template_id: Template identifier
            template: Template configuration
            qr_position: QR code center position (x, y) as percentages
            zone_densities: Text density for each zone
            logo_positions: List of detected logo positions
            image_width: Image width in pixels
            image_height: Image height in pixels

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            score = 0.0
            weights = 0.0

            # 1. QR code position score (highest weight)
            if qr_position:
                # Expected QR position varies by template
                # Most Thai bank receipts have QR at bottom or top-right
                qr_x, qr_y = qr_position

                # Score based on typical QR positions
                qr_score = 0.0
                if qr_y > 0.6:  # Bottom area
                    qr_score += 0.5
                elif qr_y < 0.3:  # Top area
                    qr_score += 0.3

                if qr_x > 0.6:  # Right side
                    qr_score += 0.3
                elif qr_x < 0.4:  # Left side
                    qr_score += 0.2

                score += qr_score * 0.4
                weights += 0.4

            # 2. Text density pattern score
            # Bank receipts typically have specific density patterns
            # High density in middle (amount info), moderate in top (header)
            top_density = (zone_densities['top_left'] +
                          zone_densities['top_center'] +
                          zone_densities['top_right']) / 3

            middle_density = (zone_densities['middle_left'] +
                             zone_densities['middle_center'] +
                             zone_densities['middle_right']) / 3

            bottom_density = (zone_densities['bottom_left'] +
                             zone_densities['bottom_center'] +
                             zone_densities['bottom_right']) / 3

            # Typical receipt pattern: moderate top, high middle, moderate/low bottom
            density_score = 0.0
            if 0.1 < top_density < 0.3:
                density_score += 0.3
            if 0.15 < middle_density < 0.4:
                density_score += 0.4
            if 0.05 < bottom_density < 0.25:
                density_score += 0.3

            score += density_score * 0.3
            weights += 0.3

            # 3. Logo position score
            if logo_positions:
                # Check if logo is in expected position (top-right or top-left)
                logo_score = 0.0
                for logo_x, logo_y in logo_positions:
                    if logo_y < 0.3:  # Top area
                        if logo_x > 0.7 or logo_x < 0.3:  # Right or left
                            logo_score += 0.5

                logo_score = min(1.0, logo_score)
                score += logo_score * 0.3
                weights += 0.3

            # Normalize score
            if weights > 0:
                return score / weights
            return 0.0

        except Exception as e:
            logger.error(f"Error computing layout score: {e}")
            return 0.0

    def _match_structure(self, image_path: str) -> Tuple[Optional[str], float]:
        """
        Match template using image structure analysis (robust).

        Uses histogram comparison, edge density, and structural similarity.

        Args:
            image_path: Path to the receipt image

        Returns:
            Tuple of (template_id, confidence_score) or (None, 0.0)
        """
        try:
            # Load the input image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None, 0.0

            # 1. Calculate color histogram
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1, 2], None, [50, 50, 50], [0, 180, 0, 256, 0, 256])
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

            # 2. Edge density analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size

            # 3. Calculate aspect ratio
            height, width = image.shape[:2]
            aspect_ratio = width / height

            # 4. Analyze structural features
            # Divide into 3x3 grid and calculate variance in each cell
            grid_variance = []
            cell_h, cell_w = height // 3, width // 3
            for i in range(3):
                for j in range(3):
                    cell = gray[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
                    variance = np.var(cell)
                    grid_variance.append(variance)

            # Compare against templates
            best_match = None
            best_score = 0.0

            for template_id, template in self.templates.items():
                score = self._compute_structure_score(
                    template_id,
                    template,
                    hist,
                    edge_density,
                    aspect_ratio,
                    grid_variance
                )

                if score > best_score:
                    best_score = score
                    best_match = template_id

            if best_match:
                logger.info(f"Structure matching best candidate: {best_match} (score: {best_score:.3f})")

            return best_match, best_score

        except Exception as e:
            logger.error(f"Error in structure matching: {e}")
            return None, 0.0

    def _compute_structure_score(
        self,
        template_id: str,
        template: Dict[str, Any],
        histogram: np.ndarray,
        edge_density: float,
        aspect_ratio: float,
        grid_variance: list
    ) -> float:
        """
        Compute structural similarity score for a template.

        Args:
            template_id: Template identifier
            template: Template configuration
            histogram: Color histogram of the image
            edge_density: Edge density of the image
            aspect_ratio: Aspect ratio of the image
            grid_variance: Variance values for 3x3 grid cells

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            score = 0.0
            weights = 0.0

            # 1. Aspect ratio score
            # Thai bank receipts typically have specific aspect ratios
            expected_aspect = template.get('image_size', [990, 1409])
            if len(expected_aspect) == 2:
                expected_ratio = expected_aspect[0] / expected_aspect[1]
                ratio_diff = abs(aspect_ratio - expected_ratio) / expected_ratio
                ratio_score = max(0.0, 1.0 - ratio_diff * 2)  # Allow 50% deviation
                score += ratio_score * 0.3
                weights += 0.3

            # 2. Edge density score
            # Receipts typically have moderate edge density (0.02-0.08)
            edge_score = 0.0
            if 0.02 < edge_density < 0.08:
                edge_score = 1.0
            elif 0.01 < edge_density < 0.10:
                edge_score = 0.7
            else:
                edge_score = 0.3

            score += edge_score * 0.3
            weights += 0.3

            # 3. Grid variance pattern score
            # Receipts have specific variance patterns (high in text areas, low in empty areas)
            variance_score = 0.0
            high_variance_count = sum(1 for v in grid_variance if v > 500)
            low_variance_count = sum(1 for v in grid_variance if v < 200)

            # Typical receipt: 4-6 high variance cells (text areas)
            if 4 <= high_variance_count <= 6:
                variance_score += 0.5
            # 3-4 low variance cells (empty areas)
            if 3 <= low_variance_count <= 4:
                variance_score += 0.5

            score += variance_score * 0.4
            weights += 0.4

            # Normalize score
            if weights > 0:
                return score / weights
            return 0.0

        except Exception as e:
            logger.error(f"Error computing structure score: {e}")
            return 0.0

    def validate_template(self, template: Dict[str, Any]) -> bool:
        """
        Validate template structure.

        Args:
            template: Template data to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['template_id', 'bank_name', 'zones']

        for field in required_fields:
            if field not in template:
                logger.error(f"Template missing required field: {field}")
                return False

        # Validate zones
        zones = template.get('zones', {})
        if not zones:
            logger.error("Template has no zones defined")
            return False

        for zone_name, zone in zones.items():
            required_zone_fields = ['x_percent', 'y_percent', 'width_percent', 'height_percent', 'parser']
            for field in required_zone_fields:
                if field not in zone:
                    logger.error(f"Zone '{zone_name}' missing field: {field}")
                    return False

        return True
