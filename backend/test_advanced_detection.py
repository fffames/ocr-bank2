#!/usr/bin/env python3
"""
Test script for advanced OpenCV template detection.

Tests all 5 detection methods:
1. Logo Template Matching (35% weight)
2. Enhanced Layout Analysis (25% weight)
3. Color Histogram Matching (15% weight)
4. Icon/Feature Detection (15% weight)
5. Spacing Pattern Analysis (10% weight)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.template_manager import TemplateManager
import cv2
from pathlib import Path
import time


def test_advanced_detection(image_path: str):
    """
    Test advanced detection on a single image.

    Args:
        image_path: Path to receipt image
    """
    print(f"\n{'='*70}")
    print(f"Testing Advanced Detection on: {Path(image_path).name}")
    print(f"{'='*70}\n")

    # Initialize template manager
    template_manager = TemplateManager()

    # Check available templates
    templates = template_manager.list_templates()
    print(f"📋 Available templates: {len(templates)}")
    for t in templates:
        print(f"   - {t['template_id']}: {t['bank_name']} ({t['num_zones']} zones)")

    print(f"\n{'='*70}")
    print("Testing Individual Detection Methods")
    print(f"{'='*70}\n")

    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    height, width = gray.shape

    print(f"📸 Image size: {width}x{height}")

    # Test each method individually
    start_time = time.time()

    # Method 1: Logo Template Matching
    print(f"\n{'─'*70}")
    print("Method 1: Logo Template Matching (35% weight)")
    print(f"{'─'*70}")
    logo_scores = template_manager._match_logos_multiscale(gray, width, height)
    for template_id, score in sorted(logo_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  {template_id:15} {score:.4f}")

    # Method 2: Enhanced Layout Analysis
    print(f"\n{'─'*70}")
    print("Method 2: Enhanced Layout Analysis (25% weight)")
    print(f"{'─'*70}")
    layout_scores = template_manager._analyze_layout_enhanced(image, gray, width, height)
    for template_id, score in sorted(layout_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  {template_id:15} {score:.4f}")

    # Method 3: Color Histogram Matching
    print(f"\n{'─'*70}")
    print("Method 3: Color Histogram Matching (15% weight)")
    print(f"{'─'*70}")
    color_scores = template_manager._match_colors(hsv, width, height)
    for template_id, score in sorted(color_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  {template_id:15} {score:.4f}")

    # Method 4: Icon/Feature Detection
    print(f"\n{'─'*70}")
    print("Method 4: Icon/Feature Detection (15% weight)")
    print(f"{'─'*70}")
    icon_scores = template_manager._match_icons(gray, width, height)
    for template_id, score in sorted(icon_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  {template_id:15} {score:.4f}")

    # Method 5: Spacing Pattern Analysis
    print(f"\n{'─'*70}")
    print("Method 5: Spacing Pattern Analysis (10% weight)")
    print(f"{'─'*70}")
    spacing_scores = template_manager._analyze_spacing(gray, width, height)
    for template_id, score in sorted(spacing_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  {template_id:15} {score:.4f}")

    elapsed = time.time() - start_time

    # Bayesian confidence fusion
    print(f"\n{'='*70}")
    print("Bayesian Confidence Fusion (Final Scores)")
    print(f"{'='*70}\n")

    method_results = {
        'logo': (logo_scores, 0.35),
        'layout': (layout_scores, 0.25),
        'color': (color_scores, 0.15),
        'icon': (icon_scores, 0.15),
        'spacing': (spacing_scores, 0.10)
    }

    final_scores = template_manager._fuse_confidences(method_results)

    for template_id, score in sorted(final_scores.items(), key=lambda x: x[1], reverse=True):
        bar_length = int(score * 50)
        bar = '█' * bar_length + '░' * (50 - bar_length)
        print(f"  {template_id:15} {score:.4f}  [{bar}]")

    # Winner
    best_template = max(final_scores, key=final_scores.get)
    best_score = final_scores[best_template]

    print(f"\n{'='*70}")
    if best_score > 0.5:
        print(f"✅ WINNER: {best_template} (confidence: {best_score:.4f})")
    else:
        print(f"⚠️  WINNER: {best_template} (low confidence: {best_score:.4f})")
    print(f"{'='*70}")

    print(f"\n⏱️  Processing time: {elapsed:.3f} seconds")
    print(f"🎯 Target: <1.0 second for production use")

    # Test full detect_template method
    print(f"\n{'='*70}")
    print("Testing Full Detection Pipeline")
    print(f"{'='*70}\n")

    start_time = time.time()
    detected_template = template_manager.detect_template(image_path)
    elapsed = time.time() - start_time

    print(f"Detected template: {detected_template}")
    print(f"Processing time: {elapsed:.3f} seconds")


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_advanced_detection.py <image_path>")
        print("\nExample:")
        print("  python test_advanced_detection.py path/to/receipt.jpg")
        sys.exit(1)

    image_path = sys.argv[1]

    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        sys.exit(1)

    test_advanced_detection(image_path)


if __name__ == "__main__":
    main()
