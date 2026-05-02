"""Shared fixtures and test configuration for pytest."""
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import numpy as np
import tempfile
import shutil

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.api.templates import router as template_router
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(template_router)
    return app


@pytest.fixture
def client(app):
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def temp_templates_dir(tmp_path):
    """Create temporary templates directory for testing."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    return templates_dir


@pytest.fixture
def sample_template_dict():
    """Sample template dictionary for testing."""
    return {
        'template_id': 'test_kbank',
        'bank_name': 'Kasikorn Bank',
        'description': 'Test KBANK transfer template',
        'image_size': [800, 1200],
        'version': '1.0',
        'detection': {
            'primary_method': 'keywords',
            'keywords': ['KBank', 'Kasikorn', 'โอนเงิน']
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
            'sender_name': {
                'x_percent': 10.0,
                'y_percent': 30.0,
                'width_percent': 40.0,
                'height_percent': 10.0,
                'parser': 'thai_name',
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


@pytest.fixture
def sample_template_yaml(sample_template_dict):
    """Sample template YAML content for testing."""
    import yaml
    return yaml.dump(sample_template_dict, allow_unicode=True)


@pytest.fixture
def sample_image_path(tmp_path):
    """Create a sample test image."""
    # Create a simple test image
    img = Image.new('RGB', (800, 1200), color='white')

    # Add some text-like patterns
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)

    # Draw some rectangles to simulate zones
    draw.rectangle([80, 180, 320, 300], outline='black')  # date zone
    draw.rectangle([80, 360, 480, 480], outline='black')  # sender zone
    draw.rectangle([480, 600, 720, 720], outline='black')  # amount zone

    # Add some text
    try:
        # Try to use a default font
        font = ImageFont.load_default()
        draw.text((100, 200), "28 ม.ค. 67", fill='black', font=font)
        draw.text((100, 400), "นายสมชาย ใจดี", fill='black', font=font)
        draw.text((500, 640), "1,234.56", fill='black', font=font)
    except Exception:
        # If font loading fails, just draw rectangles
        pass

    img_path = tmp_path / "test_receipt.jpg"
    img.save(img_path)
    return str(img_path)


@pytest.fixture
def sample_image_bytes(sample_image_path):
    """Read sample image as bytes."""
    with open(sample_image_path, 'rb') as f:
        return f.read()


@pytest.fixture
def mock_tesseract():
    """Mock Tesseract OCR output."""
    with patch('pytesseract.image_to_string') as mock:
        # Default mock returns
        mock.return_value = "28 ม.ค. 67"
        yield mock


@pytest.fixture
def mock_pil_image():
    """Mock PIL Image operations."""
    with patch('PIL.Image.open') as mock:
        # Create a mock image
        img = Mock()
        img.size = (800, 1200)
        img.crop = Mock(return_value=img)
        img.convert = Mock(return_value=img)

        mock.return_value = img
        yield mock


@pytest.fixture
def sample_zone():
    """Sample zone configuration."""
    return {
        'id': 'test_zone',
        'field_name': 'date',
        'parser_type': 'thai_date',
        'x_percent': 10.0,
        'y_percent': 15.0,
        'width_percent': 30.0,
        'height_percent': 10.0,
        'required': True
    }


@pytest.fixture
def templates_patched(temp_templates_dir):
    """Patch templates directory path."""
    with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
        with patch('app.services.template_manager.TemplateManager.__init__', lambda self, templates_dir='app/templates': None):
            yield temp_templates_dir


@pytest.fixture
def sample_base64_image():
    """Sample base64 encoded image."""
    import base64
    # Create a small 1x1 pixel image
    img = Image.new('RGB', (1, 1), color='white')
    import io
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)

    base64_str = base64.b64encode(img_bytes.read()).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_str}"


@pytest.fixture
def mock_zone_extractor():
    """Mock ZoneExtractor for testing."""
    mock = Mock()
    mock.extract_zone_text = Mock(return_value="28 ม.ค. 67")
    return mock


@pytest.fixture
def mock_template_manager(sample_template_dict):
    """Mock TemplateManager for testing."""
    mock = Mock()
    mock.get_template = Mock(return_value=sample_template_dict)
    mock.detect_template = Mock(return_value='test_kbank')
    mock.list_templates = Mock(return_value=[sample_template_dict])
    return mock


@pytest.fixture
def mock_parsers():
    """Mock parsers for testing."""
    date_mock = Mock()
    date_mock.parse = Mock(return_value=None)

    amount_mock = Mock()
    amount_mock.parse = Mock(return_value=None)

    name_mock = Mock()
    name_mock.parse = Mock(return_value=None)

    return {
        'thai_date': date_mock,
        'thai_amount': amount_mock,
        'thai_name': name_mock
    }


@pytest.fixture
def mock_cv2():
    """Mock cv2 for image processing tests."""
    with patch('cv2.imread') as mock_read:
        with patch('cv2.cvtColor') as mock_convert:
            # Create mock image
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            mock_read.return_value = img
            mock_convert.return_value = img
            yield {'imread': mock_read, 'cvtcolor': mock_convert}


@pytest.fixture
def clean_temp_files(tmp_path):
    """Cleanup temporary files after test."""
    yield tmp_path
    # Cleanup happens automatically with tmp_path fixture


@pytest.fixture
def mock_file_operations():
    """Mock file system operations."""
    with patch('builtins.open', create=True) as mock_open:
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.unlink') as mock_unlink:
                    yield {
                        'open': mock_open,
                        'mkdir': mock_mkdir,
                        'unlink': mock_unlink
                    }


@pytest.fixture
def async_client(client):
    """Async version of test client for async endpoints."""
    return client


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset service singletons before each test."""
    # Import and reset singletons
    from app.services import template_ocr_service
    template_ocr_service._template_ocr_service = None
    yield
    # Reset after test
    template_ocr_service._template_ocr_service = None
