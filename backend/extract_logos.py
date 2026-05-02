#!/usr/bin/env python3
"""
Extract logo regions from sample receipts to create logo templates.
"""
import cv2
import numpy as np
from pathlib import Path

def extract_logo_region(image_path: str, logo_region: dict, output_path: str):
    """Extract logo region from receipt image."""
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Failed to read {image_path}")
        return

    height, width = img.shape[:2]

    # Get logo region (percentage to pixels)
    x = int(logo_region['x_percent'] / 100 * width)
    y = int(logo_region['y_percent'] / 100 * height)
    w = int(logo_region['width_percent'] / 100 * width)
    h = int(logo_region['height_percent'] / 100 * height)

    # Extract logo
    logo = img[y:y+h, x:x+w]

    # Save
    cv2.imwrite(output_path, logo)
    print(f"✅ Extracted logo: {output_path}")
    print(f"   Region: x={x}, y={y}, w={w}, h={h}")

def main():
    """Extract logos from sample receipts for each bank."""
    import yaml

    templates_dir = Path("app/templates")
    logos_dir = templates_dir / "logos"
    logos_dir.mkdir(exist_ok=True)

    # Find all template YAML files
    yaml_files = list(templates_dir.glob("*.yaml"))

    if not yaml_files:
        print("❌ No template files found in app/templates/")
        return

    print(f"Found {len(yaml_files)} template files")
    print("⚠️  You need to provide sample receipt paths for each bank")
    print()

    # Read sample receipt paths from user
    print("Enter the path to a sample receipt for each bank:")
    print("(Press Enter to skip a bank)\n")

    sample_paths = {}

    for yaml_file in yaml_files:
        with open(yaml_file, 'r') as f:
            template = yaml.safe_load(f)

        bank_name = template.get('bank_name', yaml_file.stem)
        logo_region = template.get('detection', {}).get('logo_region', {})

        if not logo_region:
            print(f"⚠️  {bank_name}: No logo_region configured, skipping")
            continue

        # For now, use a placeholder
        # TODO: User needs to provide actual sample receipt paths
        print(f"{bank_name}: needs logo extracted")
        print(f"  Template: {yaml_file.name}")
        print(f"  Logo region: x={logo_region.get('x_percent')}%, y={logo_region.get('y_percent')}%, " +
              f"w={logo_region.get('width_percent')}%, h={logo_region.get('height_percent')}%")

    print("\n" + "="*60)
    print("📝 To extract logos manually:")
    print("1. Open a sample receipt in an image editor")
    print("2. Crop the logo region using the coordinates above")
    print("3. Save as: app/templates/logos/BANK_NAME.png")
    print("="*60)

if __name__ == "__main__":
    main()
