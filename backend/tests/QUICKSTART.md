# Quick Test Reference

## Essential Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific file
pytest tests/test_parsers.py -v

# Run specific test
pytest tests/test_parsers.py::TestThaiDateParser::test_parse_thai_month_short_year -v

# Run with markers
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m "not slow"

# Run failed tests only
pytest tests/ --lf

# Run with verbose output
pytest tests/ -vv

# Run with debugger on failure
pytest tests/ --pdb
```

## Test File Map

| File | Purpose | Test Count |
|------|---------|------------|
| `test_template_api.py` | API endpoints | ~40 |
| `test_ocr_services.py` | Service layer | ~35 |
| `test_parsers.py` | Parser logic | ~50 |
| `test_example.py` | Examples/Reference | ~20 |

## Common Patterns

### API Test
```python
def test_endpoint(self, client):
    response = client.get("/templates/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### Service Test with Mock
```python
@patch('pytesseract.image_to_string')
def test_ocr_service(self, mock_ocr):
    mock_ocr.return_value = "test text"
    result = service.extract()
    assert result is not None
```

### Parser Test
```python
def test_parser(self):
    parser = ThaiDateParser()
    result = parser.parse("28 ม.ค. 67")
    assert result == date(2024, 1, 28)
```

### Parametrized Test
```python
@pytest.mark.parametrize("input,expected", [
    ("28 ม.ค. 67", date(2024, 1, 28)),
    ("28/01/2024", date(2024, 1, 28)),
])
def test_dates(self, input, expected):
    result = parser.parse(input)
    assert result == expected
```

## Fixtures Quick Reference

### Available in `conftest.py`
- `client` - FastAPI test client
- `app` - FastAPI application
- `temp_templates_dir` - Temporary directory
- `sample_template_dict` - Sample template
- `sample_image_path` - Test image
- `mock_tesseract` - Mocked OCR
- `mock_pil_image` - Mocked PIL

### Using Fixtures
```python
def test_with_fixture(self, sample_template_dict):
    assert 'template_id' in sample_template_dict
```

## Markers

```python
@pytest.mark.unit           # Unit test
@pytest.mark.integration    # Integration test
@pytest.mark.api           # API test
@pytest.mark.slow          # Slow test
@pytest.mark.tesseract     # Requires Tesseract
```

## Test Data

### Sample Templates
```python
from tests.fixtures import get_sample_template

# Get KBANK template
template = get_sample_template('kbank')

# Get all templates
templates = get_all_sample_templates()
```

### Sample Results
```python
from tests.fixtures import (
    SAMPLE_OCR_RESULTS,
    SAMPLE_PARSED_VALUES,
    SAMPLE_EXTRACTION_RESULTS
)
```

## Debugging

### Print in Tests
```python
def test_with_print(self, capsys):
    print("Debug info")
    captured = capsys.readouterr()
    assert "Debug info" in captured.out
```

### Breakpoint
```python
def test_debug(self):
    breakpoint()  # Run with: pytest --pdb
    assert True
```

### Show Output
```python
# Show print output
pytest tests/ -s

# Show local variables on failure
pytest tests/ -l
```

## Coverage

### Generate Coverage
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Coverage for Specific Module
```bash
pytest tests/ --cov=app.services.parsers
```

### Minimum Coverage
```bash
pytest tests/ --cov=app --cov-fail-under=80
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Tests
  run: |
    cd backend
    pytest tests/ --cov=app --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v2
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
pytest tests/ -q
```

## Common Issues

### Import Error
```bash
# Fix: Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

### Fixture Not Found
```bash
# Fix: Ensure conftest.py is in tests/ directory
ls tests/conftest.py
```

### Mock Not Working
```bash
# Fix: Use correct import path
@patch('app.services.zone_extractor.pytesseract')
# NOT: @patch('pytesseract')
```

## Test Organization

### File Structure
```
tests/
├── conftest.py              # Shared fixtures
├── fixtures.py              # Test data
├── test_template_api.py     # API tests
├── test_ocr_services.py     # Service tests
├── test_parsers.py          # Parser tests
└── test_example.py          # Examples
```

### Test Class Structure
```python
class TestComponent:
    """Tests for Component."""

    def test_feature_success(self):
        """Test feature works correctly."""
        pass

    def test_feature_failure(self):
        """Test feature handles errors."""
        pass

    @pytest.mark.parametrize("input,expected", [...])
    def test_feature_variations(self, input, expected):
        """Test feature with various inputs."""
        pass
```

## Best Practices

1. **Descriptive Names**
   ```python
   def test_parse_thai_date_with_buddhist_era(self):
       pass
   ```

2. **One Assert Per Test**
   ```python
   def test_multiple_claims(self):
       assert result.date is not None
       # Don't do this:
       # assert result.date is not None and result.amount is not None
   ```

3. **Use Fixtures**
   ```python
   def test_with_fixture(self, sample_template):
       # Instead of creating template in test
       pass
   ```

4. **Mock External Dependencies**
   ```python
   @patch('pytesseract.image_to_string')
   def test_with_mock(self, mock_ocr):
       mock_ocr.return_value = "test"
       pass
   ```

5. **Test Both Success and Failure**
   ```python
   def test_valid_input(self):
       assert parse("valid") is not None

   def test_invalid_input(self):
       assert parse("invalid") is None
   ```

## Resources

- Full documentation: `tests/README.md`
- Pytest docs: https://docs.pytest.org/
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- Mock docs: https://docs.python.org/3/library/unittest.mock.html

## Quick Help

```bash
# pytest help
pytest --help

# Show markers
pytest --markers

# Show fixtures
pytest --fixtures

# Collect tests (don't run)
pytest tests/ --collect-only
```

---

**Remember:** Tests should be **fast**, **isolated**, and **reliable**.
