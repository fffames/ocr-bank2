"""Test data fixtures for OCR Bank tests.

This module provides sample test data for templates, OCR results, and parsed values.
"""
from datetime import date
from decimal import Decimal


# Sample Templates
SAMPLE_TEMPLATES = {
    'kbank': {
        'template_id': 'kbank',
        'bank_name': 'Kasikorn Bank',
        'description': 'KBANK mobile transfer receipt',
        'image_size': [800, 1200],
        'version': '1.0',
        'detection': {
            'primary_method': 'keywords',
            'keywords': ['KBank', 'Kasikorn', 'โอนเงิน', 'บัญชี']
        },
        'zones': {
            'date': {
                'x_percent': 10.0,
                'y_percent': 15.0,
                'width_percent': 30.0,
                'height_percent': 10.0,
                'parser': 'thai_date',
                'required': True,
                'preprocessor': 'grayscale'
            },
            'time': {
                'x_percent': 70.0,
                'y_percent': 15.0,
                'width_percent': 20.0,
                'height_percent': 8.0,
                'parser': 'thai_date',
                'required': False,
                'preprocessor': 'grayscale'
            },
            'sender_name': {
                'x_percent': 10.0,
                'y_percent': 30.0,
                'width_percent': 40.0,
                'height_percent': 10.0,
                'parser': 'thai_name',
                'required': True,
                'preprocessor': 'grayscale'
            },
            'sender_account': {
                'x_percent': 10.0,
                'y_percent': 40.0,
                'width_percent': 40.0,
                'height_percent': 8.0,
                'parser': 'text',
                'required': True,
                'preprocessor': 'grayscale'
            },
            'receiver_name': {
                'x_percent': 10.0,
                'y_percent': 55.0,
                'width_percent': 40.0,
                'height_percent': 10.0,
                'parser': 'thai_name',
                'required': True,
                'preprocessor': 'grayscale'
            },
            'receiver_account': {
                'x_percent': 10.0,
                'y_percent': 65.0,
                'width_percent': 40.0,
                'height_percent': 8.0,
                'parser': 'text',
                'required': True,
                'preprocessor': 'grayscale'
            },
            'amount': {
                'x_percent': 60.0,
                'y_percent': 50.0,
                'width_percent': 30.0,
                'height_percent': 10.0,
                'parser': 'thai_amount',
                'required': True,
                'preprocessor': 'grayscale'
            },
            'note': {
                'x_percent': 10.0,
                'y_percent': 80.0,
                'width_percent': 80.0,
                'height_percent': 10.0,
                'parser': 'text',
                'required': False,
                'preprocessor': 'grayscale'
            }
        }
    },
    'scb': {
        'template_id': 'scb',
        'bank_name': 'Siam Commercial Bank',
        'description': 'SCB Easy App transfer receipt',
        'image_size': [800, 1200],
        'version': '1.0',
        'detection': {
            'primary_method': 'keywords',
            'keywords': ['SCB', 'ไทยพาณิชย์', 'Easy App']
        },
        'zones': {
            'date': {
                'x_percent': 10.0,
                'y_percent': 12.0,
                'width_percent': 35.0,
                'height_percent': 10.0,
                'parser': 'thai_date',
                'required': True,
                'preprocessor': 'grayscale'
            },
            'sender_name': {
                'x_percent': 10.0,
                'y_percent': 28.0,
                'width_percent': 45.0,
                'height_percent': 10.0,
                'parser': 'thai_name',
                'required': True,
                'preprocessor': 'grayscale'
            },
            'receiver_name': {
                'x_percent': 10.0,
                'y_percent': 45.0,
                'width_percent': 45.0,
                'height_percent': 10.0,
                'parser': 'thai_name',
                'required': True,
                'preprocessor': 'grayscale'
            },
            'amount': {
                'x_percent': 55.0,
                'y_percent': 60.0,
                'width_percent': 35.0,
                'height_percent': 12.0,
                'parser': 'thai_amount',
                'required': True,
                'preprocessor': 'grayscale'
            }
        }
    },
    'krungthai': {
        'template_id': 'krungthai',
        'bank_name': 'Krungthai Bank',
        'description': 'KTB NEXT transfer receipt',
        'image_size': [800, 1200],
        'version': '1.0',
        'detection': {
            'primary_method': 'keywords',
            'keywords': ['KTB', 'Krungthai', 'กรุงไทย']
        },
        'zones': {
            'date': {
                'x_percent': 10.0,
                'y_percent': 15.0,
                'width_percent': 30.0,
                'height_percent': 10.0,
                'parser': 'thai_date',
                'required': True,
                'preprocessor': 'grayscale'
            },
            'amount': {
                'x_percent': 60.0,
                'y_percent': 50.0,
                'width_percent': 30.0,
                'height_percent': 10.0,
                'parser': 'thai_amount',
                'required': True,
                'preprocessor': 'grayscale'
            }
        }
    }
}


# Sample OCR Results
SAMPLE_OCR_RESULTS = {
    'date': [
        "28 ม.ค. 67",
        "28 มกราคม 2567",
        "28/01/2024",
        "28-01-2024",
        "15 ก.พ. 67",
        "20 มี.ค. 67",
        "10 เม.ย. 67"
    ],
    'amount': [
        "1,234.56 บาท",
        "฿10,000.00",
        "THB 999,999.99",
        "100.00",
        "1,000,000.00"
    ],
    'name': [
        "นายสมชาย ใจดี",
        "นางสาวมานี มีตา",
        "จาก นายวิชัย ร่ำรวย",
        "ผู้รับ Mr. John Doe",
        "Mrs. Jane Smith"
    ],
    'account': [
        "123-4-56789-0",
        "987-6-54321-0",
        "XXX-123-456"
    ]
}


# Sample Parsed Values
SAMPLE_PARSED_VALUES = {
    'dates': [
        date(2024, 1, 28),
        date(2024, 2, 15),
        date(2024, 3, 20),
        date(2024, 4, 10)
    ],
    'amounts': [
        Decimal("1234.56"),
        Decimal("10000.00"),
        Decimal("999999.99"),
        Decimal("100.00"),
        Decimal("1000000.00")
    ],
    'names': [
        "นายสมชาย ใจดี",
        "นางสาวมานี มีตา",
        "Mr. John Doe",
        "Mrs. Jane Smith"
    ]
}


# Sample API Requests
SAMPLE_API_REQUESTS = {
    'create_template': {
        'template_id': 'test_bank',
        'bank_name': 'Test Bank',
        'description': 'Test template for unit tests',
        'image_size': [800, 1200],
        'detection_keywords': ['TestBank', 'Test'],
        'zones': [
            {
                'id': 'date_zone',
                'field_name': 'date',
                'parser_type': 'thai_date',
                'x_percent': 10.0,
                'y_percent': 10.0,
                'width_percent': 30.0,
                'height_percent': 10.0,
                'required': True
            },
            {
                'id': 'amount_zone',
                'field_name': 'amount',
                'parser_type': 'thai_amount',
                'x_percent': 60.0,
                'y_percent': 50.0,
                'width_percent': 30.0,
                'height_percent': 10.0,
                'required': True
            }
        ]
    },
    'test_zone': {
        'image_data': 'data:image/jpeg;base64,/9j/4AAQSkZJRg...',
        'zone': {
            'id': 'test_zone',
            'field_name': 'date',
            'parser_type': 'thai_date',
            'x_percent': 10.0,
            'y_percent': 10.0,
            'width_percent': 30.0,
            'height_percent': 10.0,
            'required': True
        }
    }
}


# Sample Extraction Results
SAMPLE_EXTRACTION_RESULTS = {
    'kbank_transfer': {
        "raw_text": "28 ม.ค. 67 | 10:30 | นายสมชาย ใจดี | 123-4-56789-0 | นางสาวมานี มีตา | 987-6-54321-0 | 1,234.56 | Transfer for rent",
        "extracted_date": date(2024, 1, 28),
        "extracted_time": None,
        "sender": "นายสมชาย ใจดี",
        "receiver": "นางสาวมานี มีตา",
        "amount": Decimal("1234.56"),
        "note": "Transfer for rent",
        "confidence_score": Decimal("0.95")
    },
    'scb_transfer': {
        "raw_text": "15/02/2024 | นายวิชัย ร่ำรวย | Mrs. Jane Smith | 10,000.00",
        "extracted_date": date(2024, 2, 15),
        "extracted_time": None,
        "sender": "นายวิชัย ร่ำรวย",
        "receiver": "Mrs. Jane Smith",
        "amount": Decimal("10000.00"),
        "note": None,
        "confidence_score": Decimal("0.95")
    }
}


# Error Test Cases
ERROR_TEST_CASES = {
    'invalid_dates': [
        "",  # Empty
        "not a date",  # Invalid format
        "32 ม.ค. 67",  # Invalid day
        "28 ไม่มี. 67",  # Invalid month
        "28/13/2024",  # Invalid month number
    ],
    'invalid_amounts': [
        "",  # Empty
        "not a number",  # Invalid format
        "บาท",  # Just currency
        "ABC.DEF",  # Non-numeric
    ],
    'invalid_names': [
        "",  # Empty
        "A",  # Too short
        "1234567890",  # All digits
        "!@#$%^&*()",  # All special characters
    ]
}


# Image Test Data
IMAGE_TEST_DATA = {
    'valid_sizes': [
        (800, 1200),
        (1080, 1920),
        (720, 1280)
    ],
    'invalid_sizes': [
        (0, 0),
        (-1, -1),
        (100, 100)  # Too small
    ],
    'valid_zones': [
        {
            'x_percent': 10.0,
            'y_percent': 10.0,
            'width_percent': 30.0,
            'height_percent': 10.0
        },
        {
            'x_percent': 50.0,
            'y_percent': 50.0,
            'width_percent': 40.0,
            'height_percent': 20.0
        }
    ],
    'invalid_zones': [
        {
            'x_percent': -10.0,  # Negative
            'y_percent': 10.0,
            'width_percent': 30.0,
            'height_percent': 10.0
        },
        {
            'x_percent': 150.0,  # > 100
            'y_percent': 10.0,
            'width_percent': 30.0,
            'height_percent': 10.0
        },
        {
            'x_percent': 80.0,
            'y_percent': 80.0,
            'width_percent': 30.0,  # Extends beyond image
            'height_percent': 30.0
        }
    ]
}


# Helper functions
def get_sample_template(template_id='kbank'):
    """Get a sample template by ID."""
    return SAMPLE_TEMPLATES.get(template_id, SAMPLE_TEMPLATES['kbank']).copy()


def get_all_sample_templates():
    """Get all sample templates."""
    return {k: v.copy() for k, v in SAMPLE_TEMPLATES.items()}


def get_sample_ocr_result(field_type='date'):
    """Get a sample OCR result for a field type."""
    results = SAMPLE_OCR_RESULTS.get(field_type, [])
    return results[0] if results else None


def get_sample_parsed_value(field_type='dates'):
    """Get a sample parsed value."""
    values = SAMPLE_PARSED_VALUES.get(field_type, [])
    return values[0] if values else None


def get_sample_extraction_result(template_id='kbank'):
    """Get a sample extraction result."""
    return SAMPLE_EXTRACTION_RESULTS.get(
        f'{template_id}_transfer',
        SAMPLE_EXTRACTION_RESULTS['kbank_transfer']
    ).copy()


def get_error_test_cases(field_type='dates'):
    """Get error test cases for a field type."""
    return ERROR_TEST_CASES.get(field_type, [])


# Validation helpers
def is_valid_template(template):
    """Check if template has all required fields."""
    required_fields = ['template_id', 'bank_name', 'zones']
    return all(field in template for field in required_fields)


def is_valid_zone(zone):
    """Check if zone has all required fields."""
    required_fields = ['x_percent', 'y_percent', 'width_percent', 'height_percent', 'parser']
    return all(field in zone for field in required_fields)


# Export constants
__all__ = [
    'SAMPLE_TEMPLATES',
    'SAMPLE_OCR_RESULTS',
    'SAMPLE_PARSED_VALUES',
    'SAMPLE_API_REQUESTS',
    'SAMPLE_EXTRACTION_RESULTS',
    'ERROR_TEST_CASES',
    'IMAGE_TEST_DATA',
    'get_sample_template',
    'get_all_sample_templates',
    'get_sample_ocr_result',
    'get_sample_parsed_value',
    'get_sample_extraction_result',
    'get_error_test_cases',
    'is_valid_template',
    'is_valid_zone',
]
