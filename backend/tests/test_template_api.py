"""Unit tests for Template API endpoints."""
import pytest
import yaml
import json
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestListTemplates:
    """Tests for GET /api/templates/ endpoint."""

    def test_list_templates_empty(self, client, temp_templates_dir):
        """Test listing templates when directory is empty."""
        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.get("/templates/")
            assert response.status_code == 200
            assert response.json() == []

    def test_list_templates_with_templates(self, client, temp_templates_dir, sample_template_dict):
        """Test listing templates with existing templates."""
        # Create sample template files
        template1 = sample_template_dict.copy()
        template1['template_id'] = 'kbank'
        template1['bank_name'] = 'Kasikorn Bank'

        template2 = sample_template_dict.copy()
        template2['template_id'] = 'scb'
        template2['bank_name'] = 'Siam Commercial Bank'

        with open(temp_templates_dir / 'kbank.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(template1, f)

        with open(temp_templates_dir / 'scb.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(template2, f)

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.get("/templates/")

            assert response.status_code == 200
            templates = response.json()

            assert len(templates) == 2
            assert any(t['template_id'] == 'kbank' for t in templates)
            assert any(t['template_id'] == 'scb' for t in templates)

    def test_list_templates_nonexistent_directory(self, client, tmp_path):
        """Test listing templates when directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        with patch('app.api.templates.TEMPLATES_DIR', nonexistent_dir):
            response = client.get("/templates/")
            assert response.status_code == 200
            assert response.json() == []

    def test_list_templates_invalid_yaml(self, client, temp_templates_dir):
        """Test listing templates with invalid YAML files."""
        # Create invalid YAML file
        with open(temp_templates_dir / 'invalid.yaml', 'w') as f:
            f.write("invalid: yaml: content: [")

        # Create valid template
        with open(temp_templates_dir / 'valid.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(sample_template_dict, f)

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.get("/templates/")

            assert response.status_code == 200
            templates = response.json()
            # Should return only valid template
            assert len(templates) == 1
            assert templates[0]['template_id'] == 'valid'


class TestCreateTemplate:
    """Tests for POST /api/templates/ endpoint."""

    def test_create_template_success(self, client, temp_templates_dir, sample_template_dict):
        """Test successful template creation."""
        template_data = {
            'template_id': 'test_kbank',
            'bank_name': 'Kasikorn Bank',
            'description': 'Test KBANK transfer template',
            'image_size': [800, 1200],
            'detection_keywords': ['KBank', 'Kasikorn'],
            'zones': [
                {
                    'id': 'date_zone',
                    'field_name': 'date',
                    'parser_type': 'thai_date',
                    'x_percent': 10.0,
                    'y_percent': 15.0,
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
        }

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.post("/templates/", json=template_data)

            assert response.status_code == 200
            data = response.json()
            assert data['message'] == "Template saved successfully"
            assert data['template_id'] == 'test_kbank'

            # Verify file was created
            template_path = temp_templates_dir / 'test_kbank.yaml'
            assert template_path.exists()

            # Verify YAML content
            with open(template_path, 'r', encoding='utf-8') as f:
                saved_template = yaml.safe_load(f)

                assert saved_template['template_id'] == 'test_kbank'
                assert saved_template['bank_name'] == 'Kasikorn Bank'
                assert saved_template['detection']['keywords'] == ['KBank', 'Kasikorn']
                assert 'date' in saved_template['zones']
                assert 'amount' in saved_template['zones']

    def test_create_template_duplicate(self, client, temp_templates_dir, sample_template_dict):
        """Test creating template that already exists."""
        # Create existing template
        template_path = temp_templates_dir / 'test_kbank.yaml'
        with open(template_path, 'w', encoding='utf-8') as f:
            yaml.dump(sample_template_dict, f)

        template_data = {
            'template_id': 'test_kbank',
            'bank_name': 'Kasikorn Bank',
            'description': 'Test KBANK transfer template',
            'image_size': [800, 1200],
            'detection_keywords': ['KBank'],
            'zones': []
        }

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.post("/templates/", json=template_data)

            assert response.status_code == 400
            assert 'already exists' in response.json()['detail']

    def test_create_template_with_zones(self, client, temp_templates_dir):
        """Test creating template with multiple zones."""
        template_data = {
            'template_id': 'scb_template',
            'bank_name': 'Siam Commercial Bank',
            'description': 'SCB transfer template',
            'image_size': [800, 1200],
            'detection_keywords': ['SCB', 'ไทยพาณิชย์'],
            'zones': [
                {
                    'id': 'date',
                    'field_name': 'date',
                    'parser_type': 'thai_date',
                    'x_percent': 10.0,
                    'y_percent': 15.0,
                    'width_percent': 30.0,
                    'height_percent': 10.0,
                    'required': True
                },
                {
                    'id': 'sender',
                    'field_name': 'sender_name',
                    'parser_type': 'thai_name',
                    'x_percent': 10.0,
                    'y_percent': 30.0,
                    'width_percent': 40.0,
                    'height_percent': 10.0,
                    'required': True
                },
                {
                    'id': 'receiver',
                    'field_name': 'receiver_name',
                    'parser_type': 'thai_name',
                    'x_percent': 10.0,
                    'y_percent': 45.0,
                    'width_percent': 40.0,
                    'height_percent': 10.0,
                    'required': True
                },
                {
                    'id': 'amount',
                    'field_name': 'amount',
                    'parser_type': 'thai_amount',
                    'x_percent': 60.0,
                    'y_percent': 60.0,
                    'width_percent': 30.0,
                    'height_percent': 10.0,
                    'required': True
                },
                {
                    'id': 'time',
                    'field_name': 'time',
                    'parser_type': 'thai_date',
                    'x_percent': 70.0,
                    'y_percent': 75.0,
                    'width_percent': 20.0,
                    'height_percent': 8.0,
                    'required': False
                }
            ]
        }

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.post("/templates/", json=template_data)

            assert response.status_code == 200

            # Verify all zones were saved
            template_path = temp_templates_dir / 'scb_template.yaml'
            with open(template_path, 'r', encoding='utf-8') as f:
                saved_template = yaml.safe_load(f)

                assert len(saved_template['zones']) == 5
                assert 'date' in saved_template['zones']
                assert 'sender_name' in saved_template['zones']
                assert 'receiver_name' in saved_template['zones']
                assert 'amount' in saved_template['zones']
                assert 'time' in saved_template['zones']

    def test_create_template_invalid_data(self, client, temp_templates_dir):
        """Test creating template with invalid data."""
        invalid_data = {
            'template_id': '',  # Empty ID
            'bank_name': 'Test Bank',
            'description': 'Test',
            'image_size': [800, 1200],
            'detection_keywords': [],
            'zones': []
        }

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.post("/templates/", json=invalid_data)
            # Pydantic validation should fail
            assert response.status_code == 422


class TestGetTemplate:
    """Tests for GET /api/templates/{template_id} endpoint."""

    def test_get_template_success(self, client, temp_templates_dir, sample_template_dict):
        """Test getting existing template."""
        template_id = 'test_kbank'
        sample_template_dict['template_id'] = template_id

        template_path = temp_templates_dir / f'{template_id}.yaml'
        with open(template_path, 'w', encoding='utf-8') as f:
            yaml.dump(sample_template_dict, f)

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.get(f"/templates/{template_id}")

            assert response.status_code == 200
            data = response.json()

            assert data['template_id'] == template_id
            assert data['bank_name'] == 'Kasikorn Bank'
            assert 'zones' in data

    def test_get_template_not_found(self, client, temp_templates_dir):
        """Test getting non-existent template."""
        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.get("/templates/nonexistent")

            assert response.status_code == 404
            assert 'not found' in response.json()['detail']

    def test_get_template_invalid_yaml(self, client, temp_templates_dir):
        """Test getting template with invalid YAML."""
        template_path = temp_templates_dir / 'invalid.yaml'
        with open(template_path, 'w') as f:
            f.write("invalid: yaml: content:")

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.get("/templates/invalid")

            # Should return error due to invalid YAML
            assert response.status_code >= 400


class TestDeleteTemplate:
    """Tests for DELETE /api/templates/{template_id} endpoint."""

    def test_delete_template_success(self, client, temp_templates_dir, sample_template_dict):
        """Test successful template deletion."""
        template_id = 'test_kbank'
        sample_template_dict['template_id'] = template_id

        template_path = temp_templates_dir / f'{template_id}.yaml'
        with open(template_path, 'w', encoding='utf-8') as f:
            yaml.dump(sample_template_dict, f)

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.delete(f"/templates/{template_id}")

            assert response.status_code == 200
            data = response.json()
            assert 'deleted successfully' in data['message']

            # Verify file was deleted
            assert not template_path.exists()

    def test_delete_template_not_found(self, client, temp_templates_dir):
        """Test deleting non-existent template."""
        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.delete("/templates/nonexistent")

            assert response.status_code == 404
            assert 'not found' in response.json()['detail']


class TestZoneOCR:
    """Tests for POST /api/templates/test-zone endpoint."""

    @pytest.fixture
    def zone_request_data(self, sample_base64_image, sample_zone):
        """Sample request data for zone OCR testing."""
        return {
            'image_data': sample_base64_image,
            'zone': sample_zone
        }

    def test_zone_ocr_success(self, client, zone_request_data, mock_tesseract):
        """Test successful OCR on a zone."""
        # Mock the OCR result
        mock_tesseract.return_value = "28 ม.ค. 67"

        response = client.post("/templates/test-zone", json=zone_request_data)

        assert response.status_code == 200
        data = response.json()
        assert 'extracted_text' in data

    def test_zone_ocr_missing_data(self, client):
        """Test zone OCR with missing required data."""
        # Missing image_data
        response = client.post("/templates/test-zone", json={
            'zone': {
                'x_percent': 10.0,
                'y_percent': 10.0,
                'width_percent': 20.0,
                'height_percent': 10.0
            }
        })

        assert response.status_code == 400
        assert 'Missing' in response.json()['detail']

    def test_zone_ocr_invalid_base64(self, client, sample_zone):
        """Test zone OCR with invalid base64 data."""
        response = client.post("/templates/test-zone", json={
            'image_data': 'invalid-base64-data',
            'zone': sample_zone
        })

        assert response.status_code >= 400

    def test_zone_ocr_tesseract_error(self, client, zone_request_data, mock_tesseract):
        """Test zone OCR when Tesseract fails."""
        # Mock Tesseract to raise exception
        mock_tesseract.side_effect = Exception("Tesseract not available")

        response = client.post("/templates/test-zone", json=zone_request_data)

        assert response.status_code == 500
        assert 'OCR test failed' in response.json()['detail']

    @patch('app.api.templates.ZoneExtractor')
    def test_zone_ocr_integration(self, mock_extractor_class, client, zone_request_data):
        """Test zone OCR with ZoneExtractor integration."""
        # Create mock extractor
        mock_extractor = Mock()
        mock_extractor.extract_zone_text = Mock(return_value="1,234.56 บาท")
        mock_extractor_class.return_value = mock_extractor

        response = client.post("/templates/test-zone", json=zone_request_data)

        assert response.status_code == 200
        data = response.json()
        assert data['extracted_text'] == "1,234.56 บาท"

        # Verify extractor was called
        mock_extractor.extract_zone_text.assert_called_once()


class TestTemplateValidation:
    """Tests for template data validation."""

    def test_template_zones_validation(self, client, temp_templates_dir):
        """Test template with valid zones configuration."""
        template_data = {
            'template_id': 'validated_template',
            'bank_name': 'Test Bank',
            'description': 'Template with validated zones',
            'image_size': [800, 1200],
            'detection_keywords': ['Test'],
            'zones': [
                {
                    'id': 'zone1',
                    'field_name': 'date',
                    'parser_type': 'thai_date',
                    'x_percent': 10.0,
                    'y_percent': 10.0,
                    'width_percent': 30.0,
                    'height_percent': 10.0,
                    'required': True
                }
            ]
        }

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.post("/templates/", json=template_data)
            assert response.status_code == 200

    def test_template_invalid_coordinates(self, client, temp_templates_dir):
        """Test template with invalid zone coordinates."""
        template_data = {
            'template_id': 'invalid_template',
            'bank_name': 'Test Bank',
            'description': 'Template with invalid coordinates',
            'image_size': [800, 1200],
            'detection_keywords': ['Test'],
            'zones': [
                {
                    'id': 'zone1',
                    'field_name': 'date',
                    'parser_type': 'thai_date',
                    'x_percent': 150.0,  # Invalid: > 100
                    'y_percent': 10.0,
                    'width_percent': 30.0,
                    'height_percent': 10.0,
                    'required': True
                }
            ]
        }

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            # Should accept the data (validation happens during OCR processing)
            response = client.post("/templates/", json=template_data)
            assert response.status_code == 200


class TestTemplateEdgeCases:
    """Tests for edge cases and error handling."""

    def test_template_with_thai_characters(self, client, temp_templates_dir):
        """Test creating template with Thai characters."""
        template_data = {
            'template_id': 'thai_template',
            'bank_name': 'ธนาคารไทยพาณิชย์',
            'description': 'แม่แบบโอนเงิน',
            'image_size': [800, 1200],
            'detection_keywords': ['ไทยพาณิชย์', 'SCB', 'โอนเงิน'],
            'zones': []
        }

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.post("/templates/", json=template_data)
            assert response.status_code == 200

            # Verify Thai characters are preserved
            template_path = temp_templates_dir / 'thai_template.yaml'
            with open(template_path, 'r', encoding='utf-8') as f:
                saved_template = yaml.safe_load(f)
                assert saved_template['bank_name'] == 'ธนาคารไทยพาณิชย์'
                assert 'ไทยพาณิชย์' in saved_template['detection']['keywords']

    def test_template_with_special_characters(self, client, temp_templates_dir):
        """Test template with special characters in description."""
        template_data = {
            'template_id': 'special_chars',
            'bank_name': 'Test Bank (ไทย)',
            'description': 'Template with special chars: @#$%^&*()',
            'image_size': [800, 1200],
            'detection_keywords': ['Test'],
            'zones': []
        }

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.post("/templates/", json=template_data)
            assert response.status_code == 200

    def test_template_empty_zones(self, client, temp_templates_dir):
        """Test creating template with no zones."""
        template_data = {
            'template_id': 'empty_zones',
            'bank_name': 'Test Bank',
            'description': 'Template with no zones',
            'image_size': [800, 1200],
            'detection_keywords': ['Test'],
            'zones': []
        }

        with patch('app.api.templates.TEMPLATES_DIR', temp_templates_dir):
            response = client.post("/templates/", json=template_data)
            assert response.status_code == 200

            # Verify zones is empty dict
            template_path = temp_templates_dir / 'empty_zones.yaml'
            with open(template_path, 'r', encoding='utf-8') as f:
                saved_template = yaml.safe_load(f)
                assert saved_template['zones'] == {}
