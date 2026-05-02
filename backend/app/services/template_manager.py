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
        self.color_profiles = {}  # Cache for color histograms
        self.icon_templates = {}  # Cache for SIFT/ORB descriptors
        self.spacing_profiles = {}  # Cache for spacing profiles
        self._load_template_assets()  # Load logo templates, color profiles, etc.
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

    def _load_template_assets(self):
        """Load logo templates, color profiles, icon templates, and spacing profiles."""
        templates_dir = Path(self.templates_dir)

        # Create subdirectories for assets if they don't exist
        logos_dir = templates_dir / "logos"
        icons_dir = templates_dir / "icons"

        # Load logo templates for real template matching
        if logos_dir.exists():
            for logo_file in logos_dir.glob("*.png"):
                template_id = logo_file.stem  # filename without extension = template_id
                try:
                    logo_img = cv2.imread(str(logo_file), cv2.IMREAD_GRAYSCALE)
                    if logo_img is not None:
                        self.logo_templates[template_id] = logo_img
                        logger.info(f"Loaded logo template: {template_id}")
                except Exception as e:
                    logger.error(f"Error loading logo template {logo_file}: {e}")

        # Load icon templates for SIFT/ORB feature matching
        if icons_dir.exists():
            for icon_file in icons_dir.glob("*.png"):
                # Icon files should be named: template_id_icon_type.png
                parts = icon_file.stem.split('_')
                if len(parts) >= 2:
                    template_id = parts[0]
                    icon_type = '_'.join(parts[1:])  # Handle names with underscores
                    try:
                        icon_img = cv2.imread(str(icon_file), cv2.IMREAD_GRAYSCALE)
                        if icon_img is not None:
                            # Extract SIFT features
                            sift = cv2.SIFT_create()
                            kp, des = sift.detectAndCompute(icon_img, None)
                            if des is not None:
                                if template_id not in self.icon_templates:
                                    self.icon_templates[template_id] = {}
                                self.icon_templates[template_id][icon_type] = {
                                    'image': icon_img,
                                    'keypoints': kp,
                                    'descriptors': des
                                }
                                logger.info(f"Loaded icon template: {template_id}/{icon_type} ({len(kp)} features)")
                    except Exception as e:
                        logger.error(f"Error loading icon template {icon_file}: {e}")

        # Pre-compute color profiles for templates that have them
        for template_id, template in self.templates.items():
            color_profile = template.get('detection', {}).get('color_profile')
            if color_profile and 'dominant_colors' in color_profile:
                self.color_profiles[template_id] = color_profile
                logger.debug(f"Loaded color profile for {template_id}")

            spacing_profile = template.get('detection', {}).get('spacing_profile')
            if spacing_profile:
                self.spacing_profiles[template_id] = spacing_profile
                logger.debug(f"Loaded spacing profile for {template_id}")

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
        Auto-detect which template to use for an image using parallel multi-method detection.

        Implements 5 independent detection methods with Bayesian confidence fusion:
        1. Logo Template Matching (35% weight) - cv2.matchTemplate() with multi-scale
        2. Enhanced Layout Analysis (25% weight) - 5x5 density grid, QR patterns
        3. Color Histogram Matching (15% weight) - HSV comparison, dominant colors
        4. Icon/Feature Detection (15% weight) - SIFT/ORB matching
        5. Spacing Pattern Analysis (10% weight) - Text spacing, alignment metrics

        Args:
            image_path: Path to the receipt image

        Returns:
            Detected template_id or None if detection fails
        """
        logger.info(f"Starting parallel multi-method template detection for: {image_path}")

        # Load image once for all methods
        image = cv2.imread(str(image_path))
        if image is None:
            logger.error(f"Failed to load image: {image_path}")
            return None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        height, width = gray.shape

        # Run all 5 detection methods in parallel (conceptually - sequential in Python)
        method_results = {}

        # Method 1: Logo Template Matching (60% weight - increased for better matching)
        logo_scores = self._match_logos_multiscale(gray, width, height)
        method_results['logo'] = (logo_scores, 0.60)  # Increased from 0.35
        logger.info(f"Logo matching scores: {logo_scores}")

        # Method 2: Enhanced Layout Analysis (15% weight - decreased)
        layout_scores = self._analyze_layout_enhanced(image, gray, width, height)
        method_results['layout'] = (layout_scores, 0.15)  # Decreased from 0.25
        logger.info(f"Enhanced layout scores: {layout_scores}")

        # Method 3: Color Histogram Matching (10% weight - decreased)
        color_scores = self._match_colors(hsv, width, height)
        method_results['color'] = (color_scores, 0.10)  # Decreased from 0.15
        logger.info(f"Color histogram scores: {color_scores}")

        # Method 4: Icon/Feature Detection (10% weight - decreased)
        icon_scores = self._match_icons(gray, width, height)
        method_results['icon'] = (icon_scores, 0.10)  # Decreased from 0.15
        logger.info(f"Icon detection scores: {icon_scores}")

        # Method 5: Spacing Pattern Analysis (5% weight - decreased)
        spacing_scores = self._analyze_spacing(gray, width, height)
        method_results['spacing'] = (spacing_scores, 0.05)  # Decreased from 0.10
        logger.info(f"Spacing analysis scores: {spacing_scores}")

        # Bayesian confidence fusion
        final_scores = self._fuse_confidences(method_results)

        # Get best template
        if final_scores:
            best_template_id = max(final_scores, key=final_scores.get)
            best_score = final_scores[best_template_id]
            logger.info(f"✅ Best match: {best_template_id} (final confidence: {best_score:.3f})")

            if best_score > 0.2:  # Lowered threshold for better matching (was 0.5)
                return best_template_id
            else:
                logger.warning(f"Best match {best_template_id} has low confidence: {best_score:.3f}")
        else:
            logger.warning("No template matched")

        # Fallback to keyword matching if all methods fail
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

    def _match_logos_multiscale(self, gray_image: np.ndarray, width: int, height: int) -> Dict[str, float]:
        """
        Match logos using real cv2.matchTemplate() with multi-scale matching.

        Args:
            gray_image: Grayscale image
            width: Image width
            height: Image height

        Returns:
            Dictionary mapping template_id to confidence score
        """
        scores = {}

        for template_id, template in self.templates.items():
            detection_config = template.get('detection', {})

            # Check if template has logo region defined
            logo_region = detection_config.get('logo_region', {})
            if not logo_region:
                # Try logo_template config
                logo_template_config = detection_config.get('logo_template', {})
                if not logo_template_config:
                    logger.debug(f"Template {template_id} has no logo_region/logo_template defined")
                    continue

            # Extract logo region from image
            if logo_region:
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
                    continue

                region_image = gray_image[y:y+region_height, x:x+region_width]
            else:
                region_image = gray_image

            # If we have a pre-extracted logo template, use real template matching
            if template_id in self.logo_templates:
                logo_template = self.logo_templates[template_id]

                # Multi-scale matching
                scales = [0.8, 0.9, 1.0, 1.1, 1.2]
                best_match_score = 0.0

                for scale in scales:
                    try:
                        # Resize region image
                        if scale != 1.0:
                            scaled_region = cv2.resize(region_image, None, fx=scale, fy=scale,
                                                      interpolation=cv2.INTER_AREA)
                        else:
                            scaled_region = region_image

                        # Ensure template is smaller than region
                        if (logo_template.shape[0] > scaled_region.shape[0] or
                            logo_template.shape[1] > scaled_region.shape[1]):
                            continue

                        # Perform template matching
                        result = cv2.matchTemplate(scaled_region, logo_template, cv2.TM_CCOEFF_NORMED)
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                        best_match_score = max(best_match_score, max_val)
                    except Exception as e:
                        logger.debug(f"Error at scale {scale} for {template_id}: {e}")
                        continue

                scores[template_id] = best_match_score
            else:
                # Fallback to proxy methods (circular shapes, edge density)
                score = self._compute_logo_match_score(region_image, template_id)
                scores[template_id] = score

        return scores

    def _analyze_layout_enhanced(self, image: np.ndarray, gray: np.ndarray,
                                 width: int, height: int) -> Dict[str, float]:
        """
        Enhanced layout analysis with 5x5 density grid and QR patterns.

        Args:
            image: Original BGR image
            gray: Grayscale image
            width: Image width
            height: Image height

        Returns:
            Dictionary mapping template_id to confidence score
        """
        scores = {}

        # 1. Detect QR code position
        qr_detector = cv2.QRCodeDetector()
        qr_code, points = qr_detector.detect(gray)

        qr_position = None
        qr_content = None
        if qr_code and points is not None:
            qr_center_x = np.mean(points[0, :, 0]).item() / width
            qr_center_y = np.mean(points[0, :, 1]).item() / height
            qr_position = (qr_center_x, qr_center_y)

            # Try to decode QR content
            decoded_text, points, straight_qr = qr_detector.detectAndDecode(gray)
            if decoded_text:
                qr_content = decoded_text

        # 2. Enhanced 5x5 grid density analysis
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Divide into 5x5 grid
        zones = {}
        for i in range(5):
            for j in range(5):
                y_start = i * height // 5
                y_end = (i + 1) * height // 5
                x_start = j * width // 5
                x_end = (j + 1) * width // 5
                zone_name = f'zone_{i}_{j}'
                zone_img = binary[y_start:y_end, x_start:x_end]
                zones[zone_name] = np.sum(zone_img < 128) / zone_img.size

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

        # 4. Calculate scores for each template
        for template_id, template in self.templates.items():
            score = self._compute_layout_score_enhanced(
                template_id,
                template,
                qr_position,
                qr_content,
                zones,
                logo_positions,
                width,
                height
            )
            scores[template_id] = score

        return scores

    def _match_colors(self, hsv: np.ndarray, width: int, height: int) -> Dict[str, float]:
        """
        Match templates using HSV color histogram comparison.

        Args:
            hsv: HSV image
            width: Image width
            height: Image height

        Returns:
            Dictionary mapping template_id to confidence score
        """
        scores = {}

        # Compute 3D HSV histogram for the image
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [180, 256, 256], [0, 180, 0, 256, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

        # Compare against templates that have color profiles
        for template_id, template in self.templates.items():
            color_profile = template.get('detection', {}).get('color_profile')

            if not color_profile or template_id not in self.color_profiles:
                # If no color profile, give neutral score
                scores[template_id] = 0.5
                continue

            # If template has pre-computed histogram, use it
            if 'histogram' in self.color_profiles[template_id]:
                template_hist = self.color_profiles[template_id]['histogram']
                correlation = cv2.compareHist(hist, template_hist, cv2.HISTCMP_CORREL)
                # Map correlation from [-1, 1] to [0, 1]
                scores[template_id] = (correlation + 1) / 2
            else:
                # Compute dominant color matching
                dominant_colors = color_profile.get('dominant_colors', [])
                if dominant_colors:
                    match_score = self._match_dominant_colors(hsv, dominant_colors)
                    scores[template_id] = match_score
                else:
                    scores[template_id] = 0.5

        return scores

    def _match_dominant_colors(self, hsv: np.ndarray, dominant_colors: list) -> float:
        """
        Match dominant colors in HSV image.

        Args:
            hsv: HSV image
            dominant_colors: List of expected dominant colors with h, s, v, percentage

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            # Sample pixels from the image
            pixels = hsv.reshape(-1, 3)

            # For each expected dominant color, find matching pixels
            total_match = 0.0
            total_weight = 0.0

            for color_def in dominant_colors:
                h = color_def.get('h', 0)
                s = color_def.get('s', 0)
                v = color_def.get('v', 0)
                percentage = color_def.get('percentage', 0.0)

                # Define color range (with some tolerance)
                h_tolerance = 15
                s_tolerance = 50
                v_tolerance = 50

                # Find pixels within range
                h_mask = np.abs(pixels[:, 0] - h) <= h_tolerance
                s_mask = np.abs(pixels[:, 1] - s) <= s_tolerance
                v_mask = np.abs(pixels[:, 2] - v) <= v_tolerance

                match_ratio = np.sum(h_mask & s_mask & v_mask) / len(pixels)

                # Compare with expected percentage
                diff = abs(match_ratio - percentage)
                color_match = max(0.0, 1.0 - diff * 10)  # Allow 10% deviation

                total_match += color_match * percentage
                total_weight += percentage

            if total_weight > 0:
                return total_match / total_weight
            return 0.5

        except Exception as e:
            logger.error(f"Error matching dominant colors: {e}")
            return 0.5

    def _match_icons(self, gray: np.ndarray, width: int, height: int) -> Dict[str, float]:
        """
        Match icons/features using SIFT/ORB feature matching.

        Args:
            gray: Grayscale image
            width: Image width
            height: Image height

        Returns:
            Dictionary mapping template_id to confidence score
        """
        scores = {}

        # Initialize SIFT detector
        sift = cv2.SIFT_create()

        # Detect keypoints and descriptors in the image
        kp_image, des_image = sift.detectAndCompute(gray, None)

        if des_image is None:
            # No features detected in image
            for template_id in self.templates:
                scores[template_id] = 0.0
            return scores

        # Match against templates that have icon templates
        for template_id in self.icon_templates:
            scores[template_id] = 0.0

            for icon_type, icon_data in self.icon_templates[template_id].items():
                try:
                    des_template = icon_data['descriptors']

                    # Use BFMatcher to match features
                    bf = cv2.BFMatcher()
                    matches = bf.knnMatch(des_template, des_image, k=2)

                    # Apply Lowe's ratio test
                    good_matches = []
                    for match_pair in matches:
                        if len(match_pair) == 2:
                            m, n = match_pair
                            if m.distance < 0.75 * n.distance:
                                good_matches.append(m)

                    # Calculate score
                    if len(des_template) > 0:
                        match_ratio = len(good_matches) / len(des_template)
                        scores[template_id] = max(scores[template_id], match_ratio)

                except Exception as e:
                    logger.debug(f"Error matching icon {template_id}/{icon_type}: {e}")
                    continue

        # For templates without icon templates, give neutral score
        for template_id in self.templates:
            if template_id not in scores:
                scores[template_id] = 0.5

        return scores

    def _analyze_spacing(self, gray: np.ndarray, width: int, height: int) -> Dict[str, float]:
        """
        Analyze spacing patterns: text line spacing, section gaps, alignment.

        Args:
            gray: Grayscale image
            width: Image width
            height: Image height

        Returns:
            Dictionary mapping template_id to confidence score
        """
        scores = {}

        # Extract text regions using morphological operations
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            # No text detected
            for template_id in self.templates:
                scores[template_id] = 0.5
            return scores

        # Calculate bounding boxes for each contour
        bboxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 5 and h > 5:  # Filter out noise
                bboxes.append((x, y, w, h))

        # Sort by Y position (top to bottom)
        bboxes.sort(key=lambda b: b[1])

        # Calculate line spacing (average vertical distance between text lines)
        line_spacings = []
        for i in range(len(bboxes) - 1):
            gap = bboxes[i + 1][1] - (bboxes[i][1] + bboxes[i][3])
            if 0 < gap < 100:  # Reasonable gap range
                line_spacings.append(gap)

        avg_line_spacing = np.mean(line_spacings) if line_spacings else 25.0

        # Detect section gaps (larger gaps)
        section_gaps = [gap for gap in line_spacings if gap > avg_line_spacing * 2]

        # Calculate density in top, middle, bottom sections
        top_density = sum(1 for b in bboxes if b[1] < height * 0.2) / len(bboxes)
        middle_density = sum(1 for b in bboxes if height * 0.2 <= b[1] < height * 0.8) / len(bboxes)
        bottom_density = sum(1 for b in bboxes if b[1] >= height * 0.8) / len(bboxes)

        density_profile = {
            'top': top_density,
            'middle': middle_density,
            'bottom': bottom_density
        }

        # Compare against template spacing profiles
        for template_id, template in self.templates.items():
            spacing_profile = template.get('detection', {}).get('spacing_profile')

            if not spacing_profile:
                # No spacing profile defined
                scores[template_id] = 0.5
                continue

            score = self._compute_spacing_score(
                spacing_profile,
                avg_line_spacing,
                section_gaps,
                density_profile,
                width,
                height
            )
            scores[template_id] = score

        return scores

    def _compute_spacing_score(self, template_spacing: dict, line_spacing: float,
                                section_gaps: list, density_profile: dict,
                                width: int, height: int) -> float:
        """
        Compute spacing pattern match score.

        Args:
            template_spacing: Template spacing profile
            line_spacing: Average line spacing in pixels
            section_gaps: List of section gap distances
            density_profile: Text density profile
            width: Image width
            height: Image height

        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 0.0
        weights = 0.0

        # 1. Line spacing score
        expected_spacing = template_spacing.get('line_spacing_mean', 25.0)
        spacing_std = template_spacing.get('line_spacing_std', 5.0)
        spacing_diff = abs(line_spacing - expected_spacing)
        spacing_score = max(0.0, 1.0 - spacing_diff / (spacing_std * 3))

        score += spacing_score * 0.4
        weights += 0.4

        # 2. Section gaps score
        expected_gaps = template_spacing.get('section_gaps', [])
        gap_match = 0
        for gap in section_gaps:
            for expected_gap in expected_gaps:
                if abs(gap - expected_gap) < 20:  # Within 20 pixels tolerance
                    gap_match += 1
                    break

        if expected_gaps:
            gap_score = min(1.0, gap_match / len(expected_gaps))
            score += gap_score * 0.3
            weights += 0.3

        # 3. Density profile score
        expected_density = template_spacing.get('density_profile', {})
        if expected_density:
            density_score = 0.0
            for section in ['top', 'middle', 'bottom']:
                if section in expected_density:
                    expected = expected_density[section]
                    actual = density_profile.get(section, 0.0)
                    diff = abs(actual - expected)
                    density_score += max(0.0, 1.0 - diff * 2)

            density_score /= 3  # Average over 3 sections
            score += density_score * 0.3
            weights += 0.3

        # Normalize score
        if weights > 0:
            return score / weights
        return 0.5

    def _compute_layout_score_enhanced(
        self,
        template_id: str,
        template: Dict[str, Any],
        qr_position: Optional[Tuple[float, float]],
        qr_content: Optional[str],
        zones: Dict[str, float],
        logo_positions: list,
        image_width: int,
        image_height: int
    ) -> float:
        """
        Compute enhanced layout similarity score for a template.

        Args:
            template_id: Template identifier
            template: Template configuration
            qr_position: QR code center position (x, y) as percentages
            qr_content: QR code decoded content
            zones: 5x5 grid zone densities
            logo_positions: List of detected logo positions
            image_width: Image width in pixels
            image_height: Image height in pixels

        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 0.0
        weights = 0.0

        # 1. QR code position score (40% weight)
        if qr_position:
            qr_x, qr_y = qr_position
            qr_score = 0.0

            # Most Thai receipts have QR at bottom
            if qr_y > 0.7:
                qr_score += 0.6
            elif qr_y < 0.3:
                qr_score += 0.3

            # QR code content analysis (if available)
            if qr_content:
                # Check for payment reference patterns
                if any(keyword in qr_content for keyword in ['REF', 'ref', 'จ่าย', 'โอน']):
                    qr_score += 0.2

            score += qr_score * 0.4
            weights += 0.4

        # 2. 5x5 grid density pattern score (35% weight)
        # Calculate density for top, middle, bottom sections
        top_zones = [f'zone_{i}_{j}' for i in range(2) for j in range(5)]
        middle_zones = [f'zone_{i}_{j}' for i in range(2, 4) for j in range(5)]
        bottom_zones = [f'zone_{i}_{j}' for i in range(4, 5) for j in range(5)]

        top_density = np.mean([zones.get(z, 0) for z in top_zones])
        middle_density = np.mean([zones.get(z, 0) for z in middle_zones])
        bottom_density = np.mean([zones.get(z, 0) for z in bottom_zones])

        # Thai receipt pattern: moderate top, high middle (sender/receiver), high bottom (amount)
        density_score = 0.0
        if 0.05 < top_density < 0.25:
            density_score += 0.3
        if 0.15 < middle_density < 0.45:
            density_score += 0.4
        if 0.15 < bottom_density < 0.50:
            density_score += 0.3

        score += density_score * 0.35
        weights += 0.35

        # 3. Logo position score (25% weight)
        if logo_positions:
            logo_score = 0.0
            for logo_x, logo_y in logo_positions:
                # Most Thai bank logos are at top-right or top-left
                if logo_y < 0.25:  # Top area
                    if logo_x > 0.75 or logo_x < 0.25:  # Right or left
                        logo_score += 0.7

            logo_score = min(1.0, logo_score)
            score += logo_score * 0.25
            weights += 0.25

        # Normalize score
        if weights > 0:
            return score / weights
        return 0.0

    def _fuse_confidences(self, method_results: Dict[str, Tuple[Dict[str, float], float]]) -> Dict[str, float]:
        """
        Fuse confidence scores from all detection methods using Bayesian scoring.

        Args:
            method_results: Dictionary mapping method name to (scores_dict, weight) tuple

        Returns:
            Dictionary mapping template_id to final fused confidence score
        """
        final_scores = {}

        # Get all template IDs
        all_template_ids = set(self.templates.keys())

        for template_id in all_template_ids:
            total_score = 0.0
            total_weight = 0.0

            for method_name, (scores_dict, weight) in method_results.items():
                # Get score for this template from this method
                method_score = scores_dict.get(template_id, 0.0)

                # Apply prior confidence (templates with logo templates get higher prior)
                prior_confidence = 1.0
                if method_name == 'logo' and template_id in self.logo_templates:
                    prior_confidence = 1.2  # Boost confidence for templates with real logos
                elif method_name == 'icon' and template_id in self.icon_templates:
                    prior_confidence = 1.1  # Boost for templates with icon templates

                # Bayesian update: score * weight * prior
                weighted_score = method_score * weight * prior_confidence
                total_score += weighted_score
                total_weight += weight * prior_confidence

            # Normalize by total weight
            if total_weight > 0:
                final_scores[template_id] = total_score / total_weight
            else:
                final_scores[template_id] = 0.0

        return final_scores

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
