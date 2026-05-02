"""
Example test file demonstrating best practices for writing tests.

This file serves as a reference for writing new tests in the OCR Bank project.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import date
from decimal import Decimal


class ExampleTestGroup:
    """Example test class with best practices."""

    def test_descriptive_test_name(self):
        """Test name should clearly describe what is being tested."""
        # Arrange
        expected_value = "test"

        # Act
        actual_value = "test"

        # Assert
        assert actual_value == expected_value

    @pytest.mark.unit
    def test_with_marked_category(self):
        """Tests can be categorized using markers."""
        assert True

    @pytest.mark.parametrize("input,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
    ])
    def test_parametrized(self, input, expected):
        """Parametrized tests run multiple times with different inputs."""
        assert input * 2 == expected

    @patch('module.function_to_mock')
    def test_with_mock(self, mock_function):
        """Mock external dependencies to isolate the code under test."""
        # Setup mock
        mock_function.return_value = "mocked value"

        # Call code under test
        result = "some_function"()

        # Assert
        assert result == "mocked value"
        mock_function.assert_called_once()


class TestUsingFixtures:
    """Example tests using fixtures from conftest.py."""

    def test_using_sample_fixture(self, sample_template_dict):
        """Use fixtures defined in conftest.py for shared test data."""
        assert 'template_id' in sample_template_dict
        assert 'zones' in sample_template_dict

    def test_using_multiple_fixtures(self, sample_template_dict, sample_zone):
        """Tests can use multiple fixtures."""
        assert sample_template_dict['template_id'] == 'test_kbank'
        assert sample_zone['field_name'] == 'date'


class TestAsyncExample:
    """Example async tests (if needed)."""

    @pytest.mark.asyncio
    async def test_async_function(self):
        """Async tests should use the asyncio marker."""
        # Arrange
        async def async_func():
            return "async result"

        # Act
        result = await async_func()

        # Assert
        assert result == "async result"


class TestErrorHandling:
    """Example tests for error handling."""

    def test_exception_raised(self):
        """Test that exceptions are raised correctly."""
        with pytest.raises(ValueError, match="error message"):
            raise ValueError("error message")

    def test_exception_not_raised(self):
        """Test that exceptions are not raised when they shouldn't be."""
        # Should not raise
        try:
            result = 1 + 1
        except Exception:
            pytest.fail("Should not raise exception")

        assert result == 2


class TestWithComplexSetup:
    """Example tests with complex setup/teardown."""

    @pytest.fixture
    def complex_setup(self, tmp_path):
        """Fixtures can handle complex setup/teardown."""
        # Setup: Create test data
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        yield test_file  # Provide to test

        # Teardown: Clean up (handled automatically by tmp_path)

    def test_with_complex_setup(self, complex_setup):
        """Use complex fixture."""
        assert complex_setup.read_text() == "test data"


# Integration test example
class ExampleIntegrationTest:
    """Example integration test (tests multiple components together)."""

    @pytest.mark.integration
    def test_end_to_end_workflow(self, sample_template_dict, sample_image_path):
        """Integration tests should test complete workflows."""
        # This would test the full flow:
        # 1. Load template
        # 2. Process image
        # 3. Extract zones
        # 4. Parse fields
        # 5. Return result

        # Mock the actual OCR for integration test
        with patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "28 ม.ค. 67"

            # Simulate workflow
            template = sample_template_dict
            assert template is not None

            # In real test, you'd call actual service
            # result = service.extract_from_image(sample_image_path, template)
            # assert result['extracted_date'] == date(2024, 1, 28)


# Parameterized test example
class ExampleParameterizedTests:
    """Example tests with multiple test cases."""

    @pytest.mark.parametrize("date_str,expected_date", [
        ("28 ม.ค. 67", date(2024, 1, 28)),
        ("28/01/2024", date(2024, 1, 28)),
        ("15 ก.พ. 67", date(2024, 2, 15)),
    ])
    def test_date_parsing_variations(self, date_str, expected_date):
        """Test multiple date format variations."""
        from app.services.parsers.thai_date_parser import ThaiDateParser

        parser = ThaiDateParser()
        result = parser.parse(date_str)

        assert result == expected_date


# Test grouping and organization
class TestGroup1_BasicFunctionality:
    """Tests can be grouped by functionality."""

    def test_feature_a(self):
        pass

    def test_feature_b(self):
        pass


class TestGroup2_AdvancedFeatures:
    """Another test group for different features."""

    def test_advanced_feature_x(self):
        pass

    def test_advanced_feature_y(self):
        pass


# Skip and xfail examples
class TestSkipping:
    """Examples of test skipping and expected failures."""

    @pytest.mark.skip(reason="Feature not implemented yet")
    def test_not_implemented(self):
        """Skip tests for unimplemented features."""
        pass

    @pytest.mark.skipif(
        True,  # Add condition here
        reason="Skipping due to external dependency"
    )
    def test_skip_with_condition(self):
        """Skip tests based on conditions."""
        pass

    @pytest.mark.xfail
    def test_expected_failure(self):
        """Mark tests that are expected to fail."""
        assert 1 == 2  # This will fail but test will pass


# Performance test example
class TestPerformance:
    """Example performance tests."""

    @pytest.mark.slow
    def test_performance_large_template(self):
        """Mark slow tests so they can be skipped when needed."""
        import time

        # Simulate slow operation
        time.sleep(0.1)

        assert True


# Custom assertion helpers
class TestWithCustomHelpers:
    """Tests with custom assertion helpers."""

    def _assert_template_valid(self, template):
        """Custom helper to validate template structure."""
        assert 'template_id' in template
        assert 'bank_name' in template
        assert 'zones' in template
        assert isinstance(template['zones'], dict)

    def test_using_custom_helper(self, sample_template_dict):
        """Use custom helpers for reusable assertions."""
        self._assert_template_valid(sample_template_dict)


# Debugging example
class TestDebugging:
    """Example tests with debugging aids."""

    def test_with_print(self, capsys):
        """Use capsys to capture print output."""
        print("Debug information")

        captured = capsys.readouterr()
        assert "Debug information" in captured.out

    @pytest.mark.debug
    def test_with_breakpoint(self):
        """Run with: pytest --pdb"""
        # Add breakpoint() for debugging
        # breakpoint()
        assert True


# Test data builders
class TestWithDataBuilders:
    """Tests using data builders for complex objects."""

    def _build_template(self, template_id="test", bank_name="Test Bank"):
        """Builder function for creating test data."""
        return {
            'template_id': template_id,
            'bank_name': bank_name,
            'zones': {}
        }

    def test_with_data_builder(self):
        """Use data builders for flexible test data."""
        template = self._build_template(
            template_id="custom",
            bank_name="Custom Bank"
        )

        assert template['template_id'] == "custom"
        assert template['bank_name'] == "Custom Bank"


# Mocking external services
class TestWithServiceMocks:
    """Tests mocking external services."""

    @patch('pytesseract.image_to_string')
    def test_mocking_tesseract(self, mock_ocr):
        """Mock Tesseract OCR for consistent testing."""
        # Setup mock response
        mock_ocr.return_value = "Test OCR Result"

        # Test code that uses Tesseract
        from app.services.zone_extractor import ZoneExtractor

        extractor = ZoneExtractor()
        # This won't actually call Tesseract
        # result = extractor.ocr_zone(mock_image)

        # Assert mock was called
        # assert mock_ocr.called


# Context manager usage
class TestWithContextManagers:
    """Tests using context managers for setup/teardown."""

    def test_with_patch_context_manager(self):
        """Use patch as context manager for temporary mocks."""
        with patch('module.function') as mock_func:
            mock_func.return_value = "mocked"
            # Test code here
            assert mock_func.return_value == "mocked"
        # Mock is removed after context


# Property-based testing example
class TestPropertyBased:
    """Example property-based tests."""

    @pytest.mark.parametrize("value", [1, 2, 100, 1000])
    def test_property_positive_numbers(self, value):
        """Test property for all positive numbers."""
        assert value > 0
        assert value * 2 > value


# Cleanup and teardown
class TestWithTeardown:
    """Tests requiring explicit cleanup."""

    def test_with_cleanup(self, tmp_path):
        """Test that creates temporary files."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Test code here
        assert test_file.exists()

        # Cleanup happens automatically via tmp_path fixture


if __name__ == "__main__":
    # Run with: python -m pytest test_example.py -v
    pytest.main([__file__, "-v"])
