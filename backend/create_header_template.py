#!/usr/bin/env python3
"""
Create header templates from full receipt images for improved template detection.

This script extracts the top 25% of a receipt image and saves it as a header template.
Header templates are much more reliable than logo-only templates.
"""
import cv2
import sys
from pathlib import Path

def create_header_template(image_path: str, bank_name: str):
    """
    Create a header template from a full receipt image.

    Args:
        image_path: Path to the receipt image
        bank_name: Bank identifier (SCB, Kasikorn, TTB, etc.)

    Returns:
        True if successful, False otherwise
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Failed to read image: {image_path}")
        return False

    height, width = img.shape[:2]
    print(f"📸 Image: {Path(image_path).name}")
    print(f"   Size: {width}x{height}")

    # Extract top 25% as header (adjusts for different image sizes)
    header_height = int(height * 0.25)
    if header_height < 50:
        header_height = int(height * 0.30)  # Use 30% for small images
        print(f"   Using 30% height for small image")
    else:
        print(f"   Using 25% height for header")

    header = img[0:header_height, :]

    # Save header template
    logos_dir = Path("app/templates/logos")
    logos_dir.mkdir(exist_ok=True)

    template_path = logos_dir / f"{bank_name}_header.png"
    cv2.imwrite(str(template_path), header)

    print(f"✅ Created header template: {template_path}")
    print(f"   Header size: {width}x{header_height}")
    print(f"   Template type: Full header (logo + bank name + layout)")

    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python create_header_template.py <image_path> <bank_name>")
        print("")
        print("Examples:")
        print("  python create_header_template.py ~/Downloads/scb_receipt.jpg SCB")
        print("  python create_header_template.py ~/Pictures/kbank.jpg Kasikorn")
        print("  python create_header_template.py ~/Desktop/ttb_receipt.jpg TTB")
        print("")
        print("💡 Tip: Use a clear, well-aligned receipt image for best results")
        sys.exit(1)

    image_path = sys.argv[1]
    bank_name = sys.argv[2]

    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        print("Please check the path and try again")
        sys.exit(1)

    success = create_header_template(image_path, bank_name)

    if success:
        print(f"\n✅ Header template created successfully!")
        print(f"\n📝 What happens next:")
        print(f"   1. Backend will automatically load the header template on restart")
        print(f"   2. Template detection will use full header comparison (70% weight)")
        print(f"   3. Much more reliable than logo-only matching!")
        print(f"\n🔄 Restart backend to apply changes:")
        print(f"   pkill -f uvicorn && python -m uvicorn app.main:app --reload")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
