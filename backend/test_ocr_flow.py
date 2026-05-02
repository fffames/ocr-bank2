#!/usr/bin/env python3
"""Test OCR flow to debug parsing issues."""

import sys
import os

# Add backend to path
sys.path.insert(0, '/Users/boonkerdinchoi/Downloads/year 4/ocr_bank/ocr-bank2/backend')

from app.services.template_ocr_service import get_template_ocr_service

# Test with the problematic image
image_path = "/Users/boonkerdinchoi/Downloads/year 4/ocr_bank/116596.jpg"

print("=== Testing OCR Flow ===")
print(f"Image: {image_path}\n")

try:
    service = get_template_ocr_service()
    result = service.extract_from_image(image_path)

    print("\n=== Final Result ===")
    print(f"Extracted date type: {type(result.get('extracted_date'))}")
    print(f"Extracted date value: {result.get('extracted_date')}")
    print(f"Extracted time type: {type(result.get('extracted_time'))}")
    print(f"Extracted time value: {result.get('extracted_time')}")
    print(f"Sender: {result.get('sender')}")
    print(f"Receiver: {result.get('receiver')}")
    print(f"Amount: {result.get('amount')}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
