# Test Suite for OCR Bank Backend

Comprehensive test suite for the template-based OCR system.

## Overview

This test suite provides complete coverage for:
- **Template API endpoints** - FastAPI CRUD operations
- **OCR services** - Template management, zone extraction, and OCR processing
- **Field parsers** - Thai date, amount, and name parsing
- **Integration tests** - End-to-end workflows

## Test Structure

```
backend/tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and test configuration
├── test_template_api.py        # FastAPI endpoint tests
├── test_ocr_services.py        # OCR service layer tests
├── test_parsers.py             # Parser unit tests
└── README.md                   # This file
```

## Running Tests

### Run All Tests
```bash
cd /Users/boonkerdinchoi/Downloads/year\ 4/ocr_bank/ocr-bank2/backend
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_template_api.py
pytest tests/test_ocr_services.py
pytest tests/test_parsers.py
```

### Run Specific Test Class
```bash
pytest tests/test_template_api.py::TestListTemplates
pytest tests/test_ocr_services.py::TestTemplateManager
pytest tests/test_parsers.py::TestThaiDateParser
```

### Run Specific Test Method
```bash
pytest tests/test_template_api.py::TestListTemplates::test_list_templates_empty
```

### Run with Verbose Output
```bash
pytest tests/ -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=app --cov-report=html
```

### Run with Coverage for Specific Module
```bash
pytest tests/ --cov=app.api.templates --cov=app.services.template_ocr_service
```

## Test Categories

### 1. Template API Tests (`test_template_api.py`)

Tests for all template CRUD endpoints:

- **GET /api/templates/** - List all templates
- **POST /api/templates/** - Create new template
- **GET /api/templates/{id}** - Get specific template
- **DELETE /api/templates/{id}** - Delete template
- **POST /api/templates/test-zone** - Test OCR on zone

**Test Classes:**
- `TestListTemplates` - Template listing functionality
- `TestCreateTemplate` - Template creation and validation
- `TestGetTemplate` - Template retrieval
- `DeleteTemplate` - Template deletion
- `TestZoneOCR` - Zone OCR testing endpoint
- `TestTemplateValidation` - Data validation
- `TestTemplateEdgeCases` - Edge cases and error handling

### 2. OCR Service Tests (`test_ocr_services.py`)

Tests for OCR service components:

**TemplateManager Tests:**
- Template loading from YAML files
- Template retrieval and listing
- Template auto-detection using keywords
- Template validation

**ZoneExtractor Tests:**
- Image cropping with percentage coordinates
- Image preprocessing (grayscale, threshold)
- Tesseract OCR integration
- Complete extraction pipeline

**TemplateOCRService Tests:**
- End-to-end extraction workflow
- Template auto-detection
- Field parsing integration
- Result formatting
- Error handling

### 3. Parser Tests (`test_parsers.py`)

Tests for field parsing components:

**ThaiDateParser:**
- Thai month names (full and abbreviated)
- Buddhist era conversion (2567 → 2024)
- Slash/dash format dates
- Two-digit year handling
- Invalid date detection

**ThaiAmountParser:**
- Currency symbol handling (฿, THB, บาท)
- Comma-separated numbers
- Decimal handling
- Keyword-based extraction
- Large amount parsing

**ThaiNameParser:**
- Title prefix handling (นาย, นาง, Mr., Mrs., etc.)
- Prefix keyword removal (จาก, ผู้ส่ง, etc.)
- Thai and English name support
- Name validation

## Fixtures and Mocks

The test suite uses pytest fixtures defined in `conftest.py`:

### Core Fixtures
- `app` - FastAPI application instance
- `client` - Test client for API requests
- `temp_templates_dir` - Temporary templates directory
- `sample_template_dict` - Sample template data
- `sample_template_yaml` - Sample YAML content
- `sample_image_path` - Sample test image
- `sample_image_bytes` - Sample image as bytes
- `sample_base64_image` - Base64 encoded image

### Mocks
- `mock_tesseract` - Mock Tesseract OCR
- `mock_pil_image` - Mock PIL Image operations
- `mock_zone_extractor` - Mock ZoneExtractor
- `mock_template_manager` - Mock TemplateManager
- `mock_parsers` - Mock all parsers

## Test Data

### Sample Template
```yaml
template_id: test_kbank
bank_name: Kasikorn Bank
description: Test KBANK transfer template
image_size: [800, 1200]
detection:
  primary_method: keywords
  keywords: [KBank, Kasikorn, โอนเงิน]
zones:
  date:
    x_percent: 10.0
    y_percent: 15.0
    width_percent: 30.0
    height_percent: 10.0
    parser: thai_date
    required: true
    preprocessor: grayscale
```

### Sample Test Cases

**Date Parsing:**
- "28 ม.ค. 67" → 2024-01-28
- "28 มกราคม 2567" → 2024-01-28
- "28/01/2024" → 2024-01-28

**Amount Parsing:**
- "1,234.56 บาท" → 1234.56
- "฿10,000.00" → 10000.00
- "THB 999,999.99" → 999999.99

**Name Parsing:**
- "จาก นายสมชาย ใจดี" → "นายสมชาย ใจดี"
- "Mr. John Doe" → "Mr. John Doe"

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/ --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### Docker Compose for Testing
```yaml
services:
  test:
    build: .
    command: pytest tests/ --cov=app --cov-report=term-missing
    volumes:
      - ./backend:/app
    environment:
      - TESTING=true
```

## Best Practices

### Writing New Tests

1. **Use descriptive test names:**
   ```python
   def test_parse_thai_month_short_year(self):
       """Test parsing Thai date with short year."""
       pass
   ```

2. **Group related tests in classes:**
   ```python
   class TestThaiDateParser:
       """Tests for ThaiDateParser class."""
       pass
   ```

3. **Use fixtures for shared setup:**
   ```python
   def test_with_fixture(self, sample_template_dict):
       pass
   ```

4. **Mock external dependencies:**
   ```python
   @patch('pytesseract.image_to_string')
   def test_ocr(self, mock_ocr):
       mock_ocr.return_value = "test text"
       pass
   ```

5. **Test both success and failure cases:**
   ```python
   def test_success(self):
       assert result == expected

   def test_failure(self):
       with pytest.raises(ValueError):
           function()
   ```

### Test Coverage Goals

- **Line coverage:** > 80%
- **Branch coverage:** > 75%
- **Critical paths:** 100%

### When to Mock

**Mock:**
- External APIs (Tesseract, VLM)
- File system operations (in unit tests)
- Database operations
- Network calls

**Don't Mock:**
- Parser logic (test the real implementation)
- Data transformations
- Business logic

## Troubleshooting

### Common Issues

**1. Tests fail with import errors:**
```bash
# Ensure you're in the backend directory
cd /Users/boonkerdinchoi/Downloads/year\ 4/ocr_bank/ocr-bank2/backend

# Install dependencies
pip install -r requirements.txt
```

**2. Tesseract not found:**
```bash
# Install Tesseract (macOS)
brew install tesseract tesseract-lang

# Install Tesseract (Ubuntu)
sudo apt-get install tesseract-ocr-tha
```

**3. Fixture not found:**
- Ensure `conftest.py` is in the tests directory
- Check fixture name spelling

**4. Mock not applied:**
- Use correct import path in `@patch` decorator
- Patch where the object is used, not where it's defined

## Contributing

When adding new features:

1. **Write tests first** (TDD approach)
2. **Ensure all tests pass** before committing
3. **Add new fixtures** to `conftest.py` if needed
4. **Update this README** with new test categories

## License

Same as the main OCR Bank project.
