#!/usr/bin/env python3
"""Test template parsing after fixes."""

import yaml
from app.services.parsers.thai_date_parser import ThaiDateParser
from app.services.parsers.thai_time_parser import ThaiTimeParser
from app.services.parsers.thai_amount_parser import ThaiAmountParser
from app.services.parsers.thai_name_parser import ThaiNameParser

# Load the updated template
with open('/Users/boonkerdinchoi/Downloads/year 4/ocr_bank/ocr-bank2/backend/app/templates/Kasikorn.yaml', 'r') as f:
    template = yaml.safe_load(f)

print("=== Template Parser Configuration ===")
print(f"Template: {template['bank_name']}")
print()

# Check parser types for each zone
parsers = {
    'thai_date': ThaiDateParser(),
    'thai_amount': ThaiAmountParser(),
    'thai_name': ThaiNameParser(),
    'time': ThaiTimeParser(),
}

# Test data extracted from the error message
test_data = {
    'date': '28 เม.ย. 69',
    'time': '16:12',
    'amount': '3,000.00 บาท',
    'sender_name': 'นาย วีรวัฒน์ ส',
    'receiver_name': 'นาย ชาโลม อินธ์อย'
}

print("=== Testing Parsers with Extracted Data ===")
for field_name, zone_config in template['zones'].items():
    parser_type = zone_config.get('parser')
    test_text = test_data.get(field_name, f'No test data for {field_name}')

    print(f"\nField: {field_name}")
    print(f"  Parser type: {parser_type}")
    print(f"  Test text: {test_text}")

    if parser_type in parsers:
        parser = parsers[parser_type]
        try:
            result = parser.parse(test_text)
            print(f"  ✓ Parsed result: {result} (type: {type(result).__name__})")
        except Exception as e:
            print(f"  ✗ Parse error: {e}")
    else:
        print(f"  ℹ No parser (raw text will be used)")

print("\n=== Summary ===")
print("All fields with 'thai_date', 'thai_amount', 'thai_name', or 'time' parsers")
print("should now return proper Python objects (date, Decimal, str, time)")
print("instead of raw text strings.")
