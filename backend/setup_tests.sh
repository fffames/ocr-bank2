#!/bin/bash
# Setup script for OCR Bank test suite

set -e

echo "=== OCR Bank Test Suite Setup ==="
echo ""

# Change to backend directory
cd "$(dirname "$0")"

# Check Python version
echo "Checking Python version..."
python --version || python3 --version

# Install pytest if not already installed
echo ""
echo "Installing/Updating pytest and plugins..."
pip install -q pytest pytest-asyncio pytest-cov || pip3 install -q pytest pytest-asyncio pytest-cov

# Install other dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt || pip3 install -q -r requirements.txt

# Create necessary directories
echo ""
echo "Creating test directories..."
mkdir -p tests
mkdir -p app/templates

# Check Tesseract installation
echo ""
echo "Checking Tesseract OCR installation..."
if command -v tesseract &> /dev/null; then
    echo "✓ Tesseract found: $(tesseract --version | head -n1)"
else
    echo "⚠ Tesseract not found. Install with:"
    echo "  macOS: brew install tesseract tesseract-lang"
    echo "  Ubuntu: sudo apt-get install tesseract-ocr-tha"
fi

# Run pytest --version to verify installation
echo ""
echo "Verifying pytest installation..."
pytest --version

# Run tests with collection only (no execution)
echo ""
echo "Test collection:"
pytest tests/ --collect-only -q || echo "Note: Some tests may require additional setup"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Run tests with:"
echo "  pytest tests/                    # Run all tests"
echo "  pytest tests/ -v                 # Verbose output"
echo "  pytest tests/ --cov              # With coverage"
echo "  python run_tests.py --help       # See more options"
echo ""
echo "See tests/README.md for detailed documentation."
