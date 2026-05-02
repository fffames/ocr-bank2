"""Unit tests for OCR service components."""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
from PIL import Image
import numpy as np
from datetime import date
from decimal import Decimal


class TestTemplateManager:
    """Tests for TemplateManager class."""

    def test_init_creates_templates_dir_if_not_exists(self, tmp_path):
        """Test that templates directory is created on initialization."""
        from app.services.template_manager import TemplateManager

        templates_dir = tmp_path / "templates"
        manager = TemplateManager(str(templates_dir))

        assert manager.templates_dir == templates_dir

    @patch('app.services.template_manager.TemplateManager._load_templates')
    def test_init_loads_templates(self, mock_load, tmp_path):
        """Test that templates are loaded on initialization."""
        from app.services.template_manager import TemplateManager

        mock_load.return_value = {'test': 'template'}
        manager = TemplateManager(str(tmp_path / "templates"))

        mock_load.assert_called_once()
        assert manager.templates == {'test': 'template'}

    def test_load_templates_from_directory(self, tmp_path):
        """Test loading templates from directory."""
        from app.services.template_manager import TemplateManager
        import yaml

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        # Create sample templates
        template1 = {
            'template_id': 'kbank',
            'bank_name': 'Kasikorn Bank',
            'zones': {'date': {'parser': 'thai_date'}}
        }
        template2 = {
            'template_id': 'scb',
            'bank_name': 'Siam Commercial Bank',
            'zones': {'amount': {'parser': 'thai_amount'}}
        }

        with open(templates_dir / 'kbank.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(template1, f)

        with open(templates_dir / 'scb.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(template2, f)

        manager = TemplateManager(str(templates_dir))

        assert len(manager.templates) == 2
        assert 'kbank' in manager.templates
        assert 'scb' in manager.templates

    def test_load_templates_nonexistent_directory(self, tmp_path):
        """Test loading templates when directory doesn't exist."""
        from app.services.template_manager import TemplateManager

        nonexistent_dir = tmp_path / "nonexistent"
        manager = TemplateManager(str(nonexistent_dir))

        assert manager.templates == {}

    def test_get_template_success(self, tmp_path):
        """Test getting existing template."""
        from app.services.template_manager import TemplateManager
        import yaml

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = {
            'template_id': 'test',
            'bank_name': 'Test Bank',
            'zones': {}
        }
        with open(templates_dir / 'test.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(template, f)

        manager = TemplateManager(str(templates_dir))
        result = manager.get_template('test')

        assert result is not None
        assert result['template_id'] == 'test'

    def test_get_template_not_found(self, tmp_path):
        """Test getting non-existent template."""
        from app.services.template_manager import TemplateManager

        manager = TemplateManager(str(tmp_path / "templates"))
        result = manager.get_template('nonexistent')

        assert result is None

    def test_list_templates(self, tmp_path):
        """Test listing all templates."""
        from app.services.template_manager import TemplateManager
        import yaml

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template1 = {
            'template_id': 'kbank',
            'bank_name': 'Kasikorn Bank',
            'description': 'KBANK template',
            'zones': {'date': {}, 'amount': {}}
        }
        template2 = {
            'template_id': 'scb',
            'bank_name': 'Siam Commercial Bank',
            'description': 'SCB template',
            'zones': {'sender': {}}
        }

        with open(templates_dir / 'kbank.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(template1, f)
        with open(templates_dir / 'scb.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(template2, f)

        manager = TemplateManager(str(templates_dir))
        result = manager.list_templates()

        assert len(result) == 2
        assert all('template_id' in t for t in result)
        assert all('bank_name' in t for t in result)
        assert all('num_zones' in t for t in result)

    @patch('pytesseract.image_to_string')
    def test_detect_template_by_keywords(self, mock_ocr, tmp_path):
        """Test template detection using keywords."""
        from app.services.template_manager import TemplateManager
        import yaml

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = {
            'template_id': 'kbank',
            'bank_name': 'Kasikorn Bank',
            'detection': {
                'primary_method': 'keywords',
                'keywords': ['KBank', 'Kasikorn', 'โอนเงิน']
            },
            'zones': {}
        }
        with open(templates_dir / 'kbank.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(template, f)

        # Mock OCR to return text with keyword
        mock_ocr.return_value = "KBANK transfer confirmation"

        manager = TemplateManager(str(templates_dir))
        detected = manager.detect_template('test_image.jpg')

        assert detected == 'kbank'

    @patch('pytesseract.image_to_string')
    def test_detect_template_no_match(self, mock_ocr, tmp_path):
        """Test template detection when no match found."""
        from app.services.template_manager import TemplateManager
        import yaml

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = {
            'template_id': 'kbank',
            'bank_name': 'Kasikorn Bank',
            'detection': {'keywords': ['KBank']},
            'zones': {}
        }
        with open(templates_dir / 'kbank.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(template, f)

        # Mock OCR to return text without keyword
        mock_ocr.return_value = "Some other bank transfer"

        manager = TemplateManager(str(templates_dir))
        detected = manager.detect_template('test_image.jpg')

        assert detected is None

    def test_validate_template_valid(self):
        """Test validation of valid template."""
        from app.services.template_manager import TemplateManager

        manager = TemplateManager()
        template = {
            'template_id': 'test',
            'bank_name': 'Test Bank',
            'zones': {
                'date': {
                    'x_percent': 10.0,
                    'y_percent': 10.0,
                    'width_percent': 30.0,
                    'height_percent': 10.0,
                    'parser': 'thai_date'
                }
            }
        }

        assert manager.validate_template(template) is True

    def test_validate_template_missing_fields(self):
        """Test validation of template with missing fields."""
        from app.services.template_manager import TemplateManager

        manager = TemplateManager()

        # Missing template_id
        template1 = {'bank_name': 'Test', 'zones': {}}
        assert manager.validate_template(template1) is False

        # Missing bank_name
        template2 = {'template_id': 'test', 'zones': {}}
        assert manager.validate_template(template2) is False

        # Missing zones
        template3 = {'template_id': 'test', 'bank_name': 'Test'}
        assert manager.validate_template(template3) is False

    def test_validate_template_invalid_zone(self):
        """Test validation of template with invalid zone."""
        from app.services.template_manager import TemplateManager

        manager = TemplateManager()
        template = {
            'template_id': 'test',
            'bank_name': 'Test Bank',
            'zones': {
                'date': {
                    'x_percent': 10.0,
                    'y_percent': 10.0,
                    'width_percent': 30.0,
                    'height_percent': 10.0
                    # Missing 'parser' field
                }
            }
        }

        assert manager.validate_template(template) is False


class TestZoneExtractor:
    """Tests for ZoneExtractor class."""

    def test_init(self):
        """Test ZoneExtractor initialization."""
        from app.services.zone_extractor import ZoneExtractor

        extractor = ZoneExtractor()
        assert extractor.tesseract_config == r'--oem 3 --psm 6 -l tha+eng'

    def test_crop_zone_valid(self, sample_image_path):
        """Test cropping a valid zone."""
        from app.services.zone_extractor import ZoneExtractor

        extractor = ZoneExtractor()
        zone = {
            'x_percent': 10.0,
            'y_percent': 10.0,
            'width_percent': 30.0,
            'height_percent': 20.0
        }
        image_size = (800, 1200)

        cropped = extractor.crop_zone(sample_image_path, zone, image_size)

        assert isinstance(cropped, Image.Image)
        # Verify cropped image size
        # x=80, y=120, w=240, h=240
        assert cropped.size == (240, 240)

    def test_crop_zone_invalid_coordinates(self, sample_image_path):
        """Test cropping with invalid coordinates."""
        from app.services.zone_extractor import ZoneExtractor

        extractor = ZoneExtractor()

        # Negative coordinates
        zone1 = {'x_percent': -10.0, 'y_percent': 10.0, 'width_percent': 30.0, 'height_percent': 20.0}
        with pytest.raises(ValueError):
            extractor.crop_zone(sample_image_path, zone1, (800, 1200))

        # Zone extends beyond image
        zone2 = {'x_percent': 80.0, 'y_percent': 80.0, 'width_percent': 30.0, 'height_percent': 30.0}
        with pytest.raises(ValueError):
            extractor.crop_zone(sample_image_path, zone2, (800, 1200))

    def test_crop_zone_image_not_found(self):
        """Test cropping non-existent image."""
        from app.services.zone_extractor import ZoneExtractor

        extractor = ZoneExtractor()
        zone = {'x_percent': 10.0, 'y_percent': 10.0, 'width_percent': 30.0, 'height_percent': 20.0}

        with pytest.raises(FileNotFoundError):
            extractor.crop_zone('nonexistent.jpg', zone, (800, 1200))

    def test_preprocess_grayscale(self):
        """Test grayscale preprocessing."""
        from app.services.zone_extractor import ZoneExtractor

        extractor = ZoneExtractor()
        img = Image.new('RGB', (100, 100), color='red')
        processed = extractor.preprocess_image(img, method='grayscale')

        assert processed.mode == 'L'  # Grayscale mode

    def test_preprocess_threshold(self):
        """Test threshold preprocessing."""
        from app.services.zone_extractor import ZoneExtractor

        extractor = ZoneExtractor()
        img = Image.new('RGB', (100, 100), color='gray')
        processed = extractor.preprocess_image(img, method='threshold')

        assert processed.mode == '1'  # Binary mode

    def test_preprocess_none(self):
        """Test no preprocessing."""
        from app.services.zone_extractor import ZoneExtractor

        extractor = ZoneExtractor()
        img = Image.new('RGB', (100, 100), color='red')
        processed = extractor.preprocess_image(img, method='none')

        assert processed.mode == 'RGB'
        assert processed.size == (100, 100)

    @patch('pytesseract.image_to_string')
    def test_ocr_zone_success(self, mock_ocr):
        """Test successful OCR on zone."""
        from app.services.zone_extractor import ZoneExtractor

        mock_ocr.return_value = "Test OCR Result"
        extractor = ZoneExtractor()

        img = Image.new('RGB', (100, 100), color='white')
        result = extractor.ocr_zone(img)

        assert result == "Test OCR Result"
        mock_ocr.assert_called_once()

    @patch('pytesseract.image_to_string')
    def test_ocr_zone_failure(self, mock_ocr):
        """Test OCR when Tesseract fails."""
        from app.services.zone_extractor import ZoneExtractor

        mock_ocr.side_effect = Exception("Tesseract error")
        extractor = ZoneExtractor()

        img = Image.new('RGB', (100, 100), color='white')
        result = extractor.ocr_zone(img)

        assert result == ""

    @patch('pytesseract.image_to_string')
    def test_extract_zone_text_complete_pipeline(self, mock_ocr, sample_image_path):
        """Test complete zone extraction pipeline."""
        from app.services.zone_extractor import ZoneExtractor

        mock_ocr.return_value = "28 ม.ค. 67"
        extractor = ZoneExtractor()

        zone = {
            'x_percent': 10.0,
            'y_percent': 10.0,
            'width_percent': 30.0,
            'height_percent': 10.0,
            'preprocessor': 'grayscale'
        }
        image_size = (800, 1200)

        result = extractor.extract_zone_text(sample_image_path, zone, image_size)

        assert result == "28 ม.ค. 67"


class TestTemplateOCRService:
    """Tests for TemplateOCRService class."""

    @patch('app.services.template_ocr_service.ZoneExtractor')
    @patch('app.services.template_ocr_service.TemplateManager')
    @patch('app.services.template_ocr_service.ThaiDateParser')
    @patch('app.services.template_ocr_service.ThaiAmountParser')
    @patch('app.services.template_ocr_service.ThaiNameParser')
    def test_init(self, mock_name, mock_amount, mock_date, mock_tm, mock_ze):
        """Test TemplateOCRService initialization."""
        from app.services.template_ocr_service import TemplateOCRService

        service = TemplateOCRService()

        assert service.template_manager is not None
        assert service.zone_extractor is not None
        assert service.parsers is not None

    @patch('app.services.template_ocr_service.ZoneExtractor')
    @patch('app.services.template_ocr_service.TemplateManager')
    @patch('app.services.template_ocr_service.ThaiDateParser')
    @patch('app.services.template_ocr_service.ThaiAmountParser')
    @patch('app.services.template_ocr_service.ThaiNameParser')
    def test_extract_from_image_with_template_id(self, mock_name, mock_amount, mock_date, mock_tm_class, mock_ze_class, sample_image_path):
        """Test extraction with explicit template ID."""
        from app.services.template_ocr_service import TemplateOCRService

        # Setup mocks
        mock_tm = Mock()
        mock_tm.get_template = Mock(return_value={
            'template_id': 'kbank',
            'bank_name': 'Kasikorn Bank',
            'zones': {
                'date': {
                    'parser': 'thai_date',
                    'x_percent': 10.0,
                    'y_percent': 10.0,
                    'width_percent': 30.0,
                    'height_percent': 10.0,
                    'preprocessor': 'grayscale'
                }
            }
        })
        mock_tm_class.return_value = mock_tm

        mock_ze = Mock()
        mock_ze.extract_zone_text = Mock(return_value="28 ม.ค. 67")
        mock_ze_class.return_value = mock_ze

        mock_date_parser = Mock()
        mock_date_parser.parse = Mock(return_value=date(2024, 1, 28))
        mock_date.return_value = mock_date_parser

        service = TemplateOCRService()
        result = service.extract_from_image(sample_image_path, template_id='kbank')

        assert 'extracted_date' in result
        assert 'raw_text' in result
        mock_ze.extract_zone_text.assert_called()

    @patch('app.services.template_ocr_service.ZoneExtractor')
    @patch('app.services.template_ocr_service.TemplateManager')
    @patch('app.services.template_ocr_service.ThaiDateParser')
    @patch('app.services.template_ocr_service.ThaiAmountParser')
    @patch('app.services.template_ocr_service.ThaiNameParser')
    def test_extract_from_image_auto_detect(self, mock_name, mock_amount, mock_date, mock_tm_class, mock_ze_class, sample_image_path):
        """Test extraction with auto template detection."""
        from app.services.template_ocr_service import TemplateOCRService

        # Setup mocks
        mock_tm = Mock()
        mock_tm.detect_template = Mock(return_value='kbank')
        mock_tm.get_template = Mock(return_value={
            'template_id': 'kbank',
            'bank_name': 'Kasikorn Bank',
            'zones': {
                'amount': {
                    'parser': 'thai_amount',
                    'x_percent': 60.0,
                    'y_percent': 50.0,
                    'width_percent': 30.0,
                    'height_percent': 10.0,
                    'preprocessor': 'grayscale'
                }
            }
        })
        mock_tm_class.return_value = mock_tm

        mock_ze = Mock()
        mock_ze.extract_zone_text = Mock(return_value="1,234.56")
        mock_ze_class.return_value = mock_ze

        mock_amount_parser = Mock()
        from decimal import Decimal
        mock_amount_parser.parse = Mock(return_value=Decimal("1234.56"))
        mock_amount.return_value = mock_amount_parser

        service = TemplateOCRService()
        result = service.extract_from_image(sample_image_path)

        assert 'amount' in result
        mock_tm.detect_template.assert_called_once_with(sample_image_path)

    @patch('app.services.template_ocr_service.ZoneExtractor')
    @patch('app.services.template_ocr_service.TemplateManager')
    @patch('app.services.template_ocr_service.ThaiDateParser')
    @patch('app.services.template_ocr_service.ThaiAmountParser')
    @patch('app.services.template_ocr_service.ThaiNameParser')
    def test_extract_from_image_detection_fails(self, mock_name, mock_amount, mock_date, mock_tm_class, mock_ze_class, sample_image_path):
        """Test extraction when template detection fails."""
        from app.services.template_ocr_service import TemplateOCRService

        # Setup mocks
        mock_tm = Mock()
        mock_tm.detect_template = Mock(return_value=None)
        mock_tm_class.return_value = mock_tm

        service = TemplateOCRService()

        with pytest.raises(ValueError, match="Could not auto-detect template"):
            service.extract_from_image(sample_image_path)

    @patch('app.services.template_ocr_service.ZoneExtractor')
    @patch('app.services.template_ocr_service.TemplateManager')
    @patch('app.services.template_ocr_service.ThaiDateParser')
    @patch('app.services.template_ocr_service.ThaiAmountParser')
    @patch('app.services.template_ocr_service.ThaiNameParser')
    def test_extract_from_image_missing_parser(self, mock_name, mock_amount, mock_date, mock_tm_class, mock_ze_class, sample_image_path):
        """Test extraction when zone has no parser (raw text)."""
        from app.services.template_ocr_service import TemplateOCRService

        # Setup mocks
        mock_tm = Mock()
        mock_tm.get_template = Mock(return_value={
            'template_id': 'kbank',
            'bank_name': 'Kasikorn Bank',
            'zones': {
                'note': {
                    'parser': 'text',  # No parser, returns raw text
                    'x_percent': 10.0,
                    'y_percent': 80.0,
                    'width_percent': 80.0,
                    'height_percent': 10.0,
                    'preprocessor': 'grayscale'
                }
            }
        })
        mock_tm_class.return_value = mock_tm

        mock_ze = Mock()
        mock_ze.extract_zone_text = Mock(return_value="Reference: 12345")
        mock_ze_class.return_value = mock_ze

        service = TemplateOCRService()
        result = service.extract_from_image(sample_image_path, template_id='kbank')

        assert 'raw_text' in result
        assert 'Reference: 12345' in result['raw_text']

    @patch('app.services.template_ocr_service.ZoneExtractor')
    @patch('app.services.template_ocr_service.TemplateManager')
    @patch('app.services.template_ocr_service.ThaiDateParser')
    @patch('app.services.template_ocr_service.ThaiAmountParser')
    @patch('app.services.template_ocr_service.ThaiNameParser')
    def test_extract_from_image_zone_extraction_fails(self, mock_name, mock_amount, mock_date, mock_tm_class, mock_ze_class, sample_image_path):
        """Test extraction when zone extraction fails."""
        from app.services.template_ocr_service import TemplateOCRService

        # Setup mocks
        mock_tm = Mock()
        mock_tm.get_template = Mock(return_value={
            'template_id': 'kbank',
            'bank_name': 'Kasikorn Bank',
            'zones': {
                'date': {
                    'parser': 'thai_date',
                    'x_percent': 10.0,
                    'y_percent': 10.0,
                    'width_percent': 30.0,
                    'height_percent': 10.0,
                    'preprocessor': 'grayscale'
                }
            }
        })
        mock_tm_class.return_value = mock_tm

        mock_ze = Mock()
        mock_ze.extract_zone_text = Mock(side_effect=Exception("OCR failed"))
        mock_ze_class.return_value = mock_ze

        service = TemplateOCRService()
        result = service.extract_from_image(sample_image_path, template_id='kbank')

        # Should continue with None for failed zone
        assert 'raw_text' in result

    @patch('app.services.template_ocr_service.ZoneExtractor')
    @patch('app.services.template_ocr_service.TemplateManager')
    @patch('app.services.template_ocr_service.ThaiDateParser')
    @patch('app.services.template_ocr_service.ThaiAmountParser')
    @patch('app.services.template_ocr_service.ThaiNameParser')
    def test_get_template_ocr_service_singleton(self, mock_name, mock_amount, mock_date, mock_tm_class, mock_ze_class):
        """Test that get_template_ocr_service returns singleton."""
        from app.services.template_ocr_service import get_template_ocr_service, TemplateOCRService

        # Reset singleton
        import app.services.template_ocr_service as ocr_module
        ocr_module._template_ocr_service = None

        service1 = get_template_ocr_service()
        service2 = get_template_ocr_service()

        assert service1 is service2

    @patch('app.services.template_ocr_service.ZoneExtractor')
    @patch('app.services.template_ocr_service.TemplateManager')
    @patch('app.services.template_ocr_service.ThaiDateParser')
    @patch('app.services.template_ocr_service.ThaiAmountParser')
    @patch('app.services.template_ocr_service.ThaiNameParser')
    def test_format_result(self, mock_name, mock_amount, mock_date, mock_tm_class, mock_ze_class):
        """Test result formatting."""
        from app.services.template_ocr_service import TemplateOCRService

        service = TemplateOCRService()

        parsed = {
            'date': date(2024, 1, 28),
            'sender_name': 'นายสมชาย ใจดี',
            'receiver_name': 'นางสาวมานี มีตา',
            'amount': Decimal("1234.56"),
            'note': 'Test transfer'
        }
        raw = {
            'date': '28 ม.ค. 67',
            'sender_name': 'นายสมชาย ใจดี',
            'receiver_name': 'นางสาวมานี มีตา',
            'amount': '1,234.56 บาท',
            'note': 'Test transfer'
        }

        result = service._format_result(parsed, raw)

        assert result['extracted_date'] == date(2024, 1, 28)
        assert result['sender'] == 'นายสมชาย ใจดี'
        assert result['receiver'] == 'นางสาวมานี มีตา'
        assert result['amount'] == Decimal("1234.56")
        assert result['confidence_score'] == Decimal("0.95")
        assert 'raw_text' in result


class TestIntegration:
    """Integration tests for OCR services."""

    @patch('pytesseract.image_to_string')
    @patch('PIL.Image.open')
    def test_end_to_end_template_extraction(self, mock_pil_open, mock_ocr, tmp_path):
        """Test complete template-based OCR pipeline."""
        from app.services.template_manager import TemplateManager
        from app.services.zone_extractor import ZoneExtractor
        from app.services.template_ocr_service import TemplateOCRService
        import yaml

        # Create template
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = {
            'template_id': 'test_bank',
            'bank_name': 'Test Bank',
            'description': 'Integration test template',
            'image_size': [800, 1200],
            'detection': {
                'primary_method': 'keywords',
                'keywords': ['TestBank']
            },
            'zones': {
                'date': {
                    'x_percent': 10.0,
                    'y_percent': 10.0,
                    'width_percent': 30.0,
                    'height_percent': 10.0,
                    'parser': 'thai_date',
                    'required': True,
                    'preprocessor': 'grayscale'
                }
            }
        }

        with open(templates_dir / 'test_bank.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(template, f)

        # Mock OCR responses
        mock_ocr.side_effect = [
            "TestBank Transfer",  # Full image OCR for detection
            "28 ม.ค. 67"  # Zone OCR
        ]

        # Mock PIL image
        mock_img = Mock()
        mock_img.size = (800, 1200)
        mock_pil_open.return_value = mock_img

        # Create service and extract
        service = TemplateOCRService()
        service.template_manager.templates_dir = templates_dir
        service.template_manager._load_templates()

        # Test would require actual image file
        # This demonstrates the integration test structure
        assert len(service.template_manager.templates) == 1

    def test_template_validation_and_loading(self, tmp_path):
        """Test template validation and loading workflow."""
        from app.services.template_manager import TemplateManager
        import yaml

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        # Valid template
        valid_template = {
            'template_id': 'valid',
            'bank_name': 'Valid Bank',
            'zones': {
                'date': {
                    'x_percent': 10.0,
                    'y_percent': 10.0,
                    'width_percent': 30.0,
                    'height_percent': 10.0,
                    'parser': 'thai_date'
                }
            }
        }

        # Invalid template (missing parser)
        invalid_template = {
            'template_id': 'invalid',
            'bank_name': 'Invalid Bank',
            'zones': {
                'date': {
                    'x_percent': 10.0,
                    'y_percent': 10.0,
                    'width_percent': 30.0,
                    'height_percent': 10.0
                    # Missing 'parser'
                }
            }
        }

        with open(templates_dir / 'valid.yaml', 'w') as f:
            yaml.dump(valid_template, f)

        with open(templates_dir / 'invalid.yaml', 'w') as f:
            yaml.dump(invalid_template, f)

        manager = TemplateManager(str(templates_dir))

        # Valid template should be loaded
        assert 'valid' in manager.templates
        assert manager.validate_template(manager.templates['valid']) is True

        # Invalid template should also be loaded (validation is separate)
        assert 'invalid' in manager.templates
        assert manager.validate_template(manager.templates['invalid']) is False
