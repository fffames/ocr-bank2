#!/usr/bin/env python3
"""Test script for template detection system."""

import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'app'))

from services.template_manager import TemplateManager

def test_template_detection():
    """Test the template detection system with sample images."""

    # Initialize template manager
    templates_dir = Path(__file__).parent / 'app' / 'templates'
    manager = TemplateManager(str(templates_dir))

    print("\n" + "="*60)
    print("TEMPLATE DETECTION SYSTEM TEST")
    print("="*60)

    # List available templates
    print("\n📋 Available Templates:")
    templates = manager.list_templates()
    for tmpl in templates:
        print(f"  - {tmpl['template_id']}: {tmpl['bank_name']} ({tmpl['num_zones']} zones)")

    # Test with a sample image
    sample_images = [
        "/Users/boonkerdinchoi/Downloads/year 4/ocr_bank/ocr-bank2/116596.jpg",
    ]

    for image_path in sample_images:
        if Path(image_path).exists():
            print(f"\n🔍 Testing detection for: {Path(image_path).name}")
            print("-" * 60)

            # Run detection
            detected_template = manager.detect_template(image_path)

            if detected_template:
                template = manager.get_template(detected_template)
                print(f"\n✅ SUCCESS: Detected template '{detected_template}'")
                print(f"   Bank: {template.get('bank_name', 'Unknown')}")
                print(f"   Description: {template.get('description', 'N/A')}")
            else:
                print(f"\n❌ FAILED: Could not detect template")
        else:
            print(f"\n⚠️  Image not found: {image_path}")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_template_detection()
