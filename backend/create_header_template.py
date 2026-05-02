#!/usr/bin/env python3
"""
Create header templates from receipt images for better template matching.

Instead of using just the logo, this uses the entire header section (logo + bank name + layout)
which is much more reliable for template detection.
"""
import cv2
import sys
from pathlib import Path

def create_header_template(image_path: str, bank_name: str):
    """
    Extract header region from receipt and save as template.

    Args:
        image_path: Path to receipt image
        bank_name: Name of bank (SCB, Kasikorn, TTB, etc.)
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Failed to read: {image_path}")
        return False

    height, width = img.shape[:2]
    print(f"📸 Image: {Path(image_path).name}")
    print(f"   Size: {width}x{height}")

    # Extract header region (top portion with logo and bank name)
    # Use a larger region to capture distinctive layout elements
    header_y = int(0.02 * height)      # Start at 2% from top
    header_h = int(0.20 * height)      # Extract top 20% of image
    header_x = int(0.10 * width)       # Start at 10% from left (avoid edges)
    header_w = int(0.80 * width)       # Use 80% of width

    header = img[header_y:header_y+header_h, header_x:header_x+header_w]

    # Save template
    logos_dir = Path("app/templates/logos")
    logos_dir.mkdir(exist_ok=True)

    template_path = logos_dir / f"{bank_name}_header.png"
    cv2.imwrite(str(template_path), header)

    print(f"✅ Created header template: {template_path}")
    print(f"   Region: top 20% starting from 10% left")
    print(f"   Template size: {header_w}x{header_h}")

    # Update template YAML to use the header template
    yaml_path = Path(f"app/templates/{bank_name}.yaml")
    if yaml_path.exists():
        import yaml
        with open(yaml_path, 'r') as f:
            template = yaml.safe_load(f)

        # Update logo_template path
        if 'detection' not in template:
            template['detection'] = {}
        template['detection']['logo_template'] = {
            'path': f"logos/{bank_name}_header.png",
            'method': 'match_template',
            'match_threshold': 0.5,  # Lower threshold for header matching
            'scales': [0.9, 1.0, 1.1]
        }

        # Save updated YAML
        with open(yaml_path, 'w') as f:
            yaml.dump(template, f, allow_unicode=True, default_flow_style=False)

        print(f"✅ Updated template config: {yaml_path}")
        print(f"   Set logo_template to: logos/{bank_name}_header.png")
        print(f"   Lowered threshold to 0.5 for better matching")

    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python create_header_template.py <image_path> <bank_name>")
        print("")
        print("Example:")
        print("  python create_header_template.py ~/Downloads/scb_receipt.jpg SCB")
        print("  python create_header_template.py ~/Downloads/kbank_receipt.jpg Kasikorn")
        sys.exit(1)

    image_path = sys.argv[1]
    bank_name = sys.argv[2]

    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        sys.exit(1)

    success = create_header_template(image_path, bank_name)

    if success:
        print(f"\n✅ Header template created successfully!")
        print(f"   Restart backend to apply changes")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
