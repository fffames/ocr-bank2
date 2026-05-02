#!/usr/bin/env python3
"""
Extract logo templates from receipt images for template matching.

This utility helps prepare logo assets for the advanced detection system.
It extracts logo regions from receipt images and saves them as grayscale templates.
"""

import sys
import cv2
import numpy as np
from pathlib import Path
import argparse


def extract_logo_region(
    image_path: str,
    x_percent: float,
    y_percent: float,
    width_percent: float,
    height_percent: float,
    output_path: str
):
    """
    Extract logo region from receipt image.

    Args:
        image_path: Path to receipt image
        x_percent: X position of logo region (percentage of image width)
        y_percent: Y position of logo region (percentage of image height)
        width_percent: Width of logo region (percentage of image width)
        height_percent: Height of logo region (percentage of image height)
        output_path: Path to save extracted logo
    """
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return False

    height, width = image.shape[:2]
    print(f"📸 Image size: {width}x{height}")

    # Calculate logo region coordinates
    x = int(x_percent * width / 100)
    y = int(y_percent * height / 100)
    region_width = int(width_percent * width / 100)
    region_height = int(height_percent * height / 100)

    # Ensure region is within image bounds
    x = max(0, min(x, width - region_width))
    y = max(0, min(y, height - region_height))
    region_width = min(region_width, width - x)
    region_height = min(region_height, height - y)

    print(f"📍 Logo region: x={x}, y={y}, width={region_width}, height={region_height}")

    # Extract logo region
    logo_region = image[y:y+region_height, x:x+region_width]

    # Convert to grayscale for template matching
    logo_gray = cv2.cvtColor(logo_region, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to create clean logo template
    _, logo_thresh = cv2.threshold(logo_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Save extracted logo
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(str(output_path), logo_thresh)
    print(f"✅ Logo saved to: {output_path}")

    # Create visualization
    vis_image = image.copy()
    cv2.rectangle(vis_image, (x, y), (x + region_width, y + region_height), (0, 255, 0), 2)
    vis_path = output_path.parent / f"{output_path.stem}_visualization.jpg"
    cv2.imwrite(str(vis_path), vis_image)
    print(f"🎨 Visualization saved to: {vis_path}")

    return True


def auto_detect_logo_region(image_path: str) -> tuple:
    """
    Auto-detect logo region using HoughCircles.

    Args:
        image_path: Path to receipt image

    Returns:
        Tuple of (x_percent, y_percent, width_percent, height_percent)
        or None if logo not detected
    """
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape

    # Detect circular shapes (logos are often circular/oval)
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=min(width, height) // 4,
        param1=50,
        param2=30,
        minRadius=min(width, height) // 20,
        maxRadius=min(width, height) // 3
    )

    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")

        # Find the largest circle (likely the main logo)
        max_radius = 0
        best_circle = None
        for (x, y, r) in circles:
            if r > max_radius:
                max_radius = r
                best_circle = (x, y, r)

        if best_circle:
            x, y, r = best_circle

            # Calculate region with some padding
            padding = 2.5
            region_width = int(r * 2 * padding)
            region_height = int(r * 2 * padding)
            x_start = max(0, x - region_width // 2)
            y_start = max(0, y - region_height // 2)

            # Convert to percentages
            x_percent = x_start * 100 / width
            y_percent = y_start * 100 / height
            width_percent = min(100, region_width * 100 / width)
            height_percent = min(100, region_height * 100 / height)

            return (x_percent, y_percent, width_percent, height_percent)

    return None


def extract_logos_for_template(template_path: str, sample_image_path: str):
    """
    Extract all logos needed for a template.

    Args:
        template_path: Path to template YAML file
        sample_image_path: Path to sample receipt image
    """
    import yaml

    # Load template
    with open(template_path, 'r') as f:
        template = yaml.safe_load(f)

    template_id = template.get('template_id')
    print(f"\n🔧 Processing template: {template_id}")

    # Get logo region from template
    detection_config = template.get('detection', {})
    logo_region = detection_config.get('logo_region')

    if logo_region:
        # Manual extraction from template config
        output_dir = Path("backend/app/templates/logos")
        output_path = output_dir / f"{template_id}.png"

        extract_logo_region(
            sample_image_path,
            logo_region.get('x_percent', 80),
            logo_region.get('y_percent', 0),
            logo_region.get('width_percent', 20),
            logo_region.get('height_percent', 15),
            output_path
        )

        print(f"✅ Logo template ready for {template_id}")
        print(f"   Add this to template YAML:")
        print(f"   detection:")
        print(f"     logo_template:")
        print(f"       path: \"logos/{template_id}.png\"")
        print(f"       method: \"match_template\"")
        print(f"       match_threshold: 0.75")
        print(f"       scales: [0.8, 0.9, 1.0, 1.1, 1.2]")
    else:
        # Try auto-detection
        print("⚠️  No logo_region defined in template, trying auto-detection...")
        auto_region = auto_detect_logo_region(sample_image_path)

        if auto_region:
            x_percent, y_percent, width_percent, height_percent = auto_region

            output_dir = Path("backend/app/templates/logos")
            output_path = output_dir / f"{template_id}.png"

            extract_logo_region(
                sample_image_path,
                x_percent,
                y_percent,
                width_percent,
                height_percent,
                output_path
            )

            print(f"\n✅ Auto-detected logo! Add this to template YAML:")
            print(f"   detection:")
            print(f"     logo_region:")
            print(f"       x_percent: {x_percent:.1f}")
            print(f"       y_percent: {y_percent:.1f}")
            print(f"       width_percent: {width_percent:.1f}")
            print(f"       height_percent: {height_percent:.1f}")
        else:
            print("❌ Could not auto-detect logo region")
            print("   Please manually specify logo_region in template YAML")


def main():
    parser = argparse.ArgumentParser(
        description="Extract logo templates from receipt images"
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Manual extraction command
    manual_parser = subparsers.add_parser('manual', help='Manually extract logo region')
    manual_parser.add_argument('image_path', help='Path to receipt image')
    manual_parser.add_argument('x_percent', type=float, help='X position (percentage)')
    manual_parser.add_argument('y_percent', type=float, help='Y position (percentage)')
    manual_parser.add_argument('width_percent', type=float, help='Width (percentage)')
    manual_parser.add_argument('height_percent', type=float, help='Height (percentage)')
    manual_parser.add_argument('output_path', help='Output path for extracted logo')

    # Auto-detection command
    auto_parser = subparsers.add_parser('auto', help='Auto-detect and extract logo')
    auto_parser.add_argument('image_path', help='Path to receipt image')
    auto_parser.add_argument('output_path', help='Output path for extracted logo')

    # Template-based extraction
    template_parser = subparsers.add_parser('template', help='Extract logos from template config')
    template_parser.add_argument('template_path', help='Path to template YAML file')
    template_parser.add_argument('sample_image_path', help='Path to sample receipt image')

    args = parser.parse_args()

    if args.command == 'manual':
        extract_logo_region(
            args.image_path,
            args.x_percent,
            args.y_percent,
            args.width_percent,
            args.height_percent,
            args.output_path
        )
    elif args.command == 'auto':
        region = auto_detect_logo_region(args.image_path)
        if region:
            x_percent, y_percent, width_percent, height_percent = region
            extract_logo_region(
                args.image_path,
                x_percent,
                y_percent,
                width_percent,
                height_percent,
                args.output_path
            )
        else:
            print("❌ Could not auto-detect logo region")
    elif args.command == 'template':
        extract_logos_for_template(args.template_path, args.sample_image_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
