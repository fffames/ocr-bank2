"""Unit tests for OCR field parsers."""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock


class TestBaseParser:
    """Tests for BaseParser class."""

    def test_base_parser_is_abstract(self):
        """Test that BaseParser cannot be instantiated directly."""
        from app.services.parsers.base_parser import BaseParser

        with pytest.raises(TypeError):
            BaseParser()

    def test_clean_text_basic(self):
        """Test basic text cleaning."""
        from app.services.parsers.base_parser import BaseParser

        # Create a concrete implementation
        class ConcreteParser(BaseParser):
            def parse(self, text):
                return self.clean_text(text)

        parser = ConcreteParser()

        # Test whitespace removal
        assert parser.clean_text("  test  text  ") == "test text"

        # Test newline removal
        assert parser.clean_text("test\n\ntext") == "test text"

        # Test tab removal
        assert parser.clean_text("test\t\ttext") == "test text"

    def test_clean_text_empty(self):
        """Test cleaning empty text."""
        from app.services.parsers.base_parser import BaseParser

        class ConcreteParser(BaseParser):
            def parse(self, text):
                return self.clean_text(text)

        parser = ConcreteParser()
        assert parser.clean_text("") == ""
        assert parser.clean_text(None) == ""

    def test_clean_text_custom_patterns(self):
        """Test text cleaning with custom patterns."""
        from app.services.parsers.base_parser import BaseParser

        class ConcreteParser(BaseParser):
            def parse(self, text):
                return self.clean_text(text, patterns=[r'\d+', r'[A-Z]+'])

        parser = ConcreteParser()
        result = parser.clean_text("ABC123def456")
        # Should remove digits and uppercase letters
        assert result == "def"

    def test_extract_with_regex_success(self):
        """Test regex extraction when pattern matches."""
        from app.services.parsers.base_parser import BaseParser

        class ConcreteParser(BaseParser):
            def parse(self, text):
                return self.extract_with_regex(text, r'\d{4}', group=0)

        parser = ConcreteParser()
        result = parser.parse("Year: 2024")
        assert result == "2024"

    def test_extract_with_regex_no_match(self):
        """Test regex extraction when pattern doesn't match."""
        from app.services.parsers.base_parser import BaseParser

        class ConcreteParser(BaseParser):
            def parse(self, text):
                return self.extract_with_regex(text, r'\d{4}', group=0)

        parser = ConcreteParser()
        result = parser.parse("No digits here")
        assert result is None

    def test_extract_with_regex_groups(self):
        """Test regex extraction with capture groups."""
        from app.services.parsers.base_parser import BaseParser

        class ConcreteParser(BaseParser):
            def parse(self, text):
                return self.extract_with_regex(text, r'(\d{2})/(\d{2})/(\d{4})', group=2)

        parser = ConcreteParser()
        result = parser.parse("Date: 28/01/2024")
        assert result == "2024"


class TestThaiDateParser:
    """Tests for ThaiDateParser class."""

    def test_parse_thai_month_short_year(self):
        """Test parsing Thai date with short year."""
        from app.services.parsers.thai_date_parser import ThaiDateParser

        parser = ThaiDateParser()
        result = parser.parse("28 ม.ค. 67")

        assert result is not None
        assert result == date(2024, 1, 28)

    def test_parse_thai_month_full_year(self):
        """Test parsing Thai date with full Buddhist year."""
        from app.services.parsers.thai_date_parser import ThaiDateParser

        parser = ThaiDateParser()
        result = parser.parse("28 มกราคม 2567")

        assert result is not None
        assert result == date(2024, 1, 28)

    def test_parse_slash_format_christian_era(self):
        """Test parsing date in slash format (Christian era)."""
        from app.services.parsers.thai_date_parser import ThaiDateParser

        parser = ThaiDateParser()

        result = parser.parse("28/01/2024")
        assert result == date(2024, 1, 28)

        result = parser.parse("28-01-2024")
        assert result == date(2024, 1, 28)

    def test_parse_slash_format_buddhist_era(self):
        """Test parsing date in slash format (Buddhist era)."""
        from app.services.parsers.thai_date_parser import ThaiDateParser

        parser = ThaiDateParser()
        result = parser.parse("28/01/2567")

        assert result is not None
        assert result == date(2024, 1, 28)

    def test_parse_different_thai_months(self):
        """Test parsing different Thai months."""
        from app.services.parsers.thai_date_parser import ThaiDateParser

        parser = ThaiDateParser()

        # Test various months
        assert parser.parse("15 ก.พ. 67") == date(2024, 2, 15)
        assert parser.parse("20 มี.ค. 67") == date(2024, 3, 20)
        assert parser.parse("10 เม.ย. 67") == date(2024, 4, 10)
        assert parser.parse("05 พ.ค. 67") == date(2024, 5, 5)
        assert parser.parse("01 มิ.ย. 67") == date(2024, 6, 1)
        assert parser.parse("25 ก.ค. 67") == date(2024, 7, 25)
        assert parser.parse("12 ส.ค. 67") == date(2024, 8, 12)
        assert parser.parse("01 ก.ย. 67") == date(2024, 9, 1)
        assert parser.parse("23 ต.ค. 67") == date(2024, 10, 23)
        assert parser.parse("05 พ.ย. 67") == date(2024, 11, 5)
        assert parser.parse("31 ธ.ค. 67") == date(2024, 12, 31)

    def test_parse_month_abbreviations(self):
        """Test parsing different Thai month abbreviations."""
        from app.services.parsers.thai_date_parser import ThaiDateParser

        parser = ThaiDateParser()

        # Test different abbreviations for January
        assert parser.parse("28 มกราคม 67") == date(2024, 1, 28)
        assert parser.parse("28 ม.ค. 67") == date(2024, 1, 28)
        assert parser.parse("28 มค 67") == date(2024, 1, 28)

    def test_parse_invalid_date(self):
        """Test parsing invalid dates."""
        from app.services.parsers.thai_date_parser import ThaiDateParser

        parser = ThaiDateParser()

        # Invalid day
        assert parser.parse("32 ม.ค. 67") is None

        # Invalid month
        assert parser.parse("28 ไม่มีเดือนนี้ 67") is None

        # Invalid date format
        assert parser.parse("not a date") is None

    def test_parse_empty_text(self):
        """Test parsing empty text."""
        from app.services.parsers.thai_date_parser import ThaiDateParser

        parser = ThaiDateParser()
        assert parser.parse("") is None
        assert parser.parse(None) is None

    def test_parse_with_noise(self):
        """Test parsing date with surrounding noise text."""
        from app.services.parsers.thai_date_parser import ThaiDateParser

        parser = ThaiDateParser()

        # Date with surrounding text
        result = parser.parse("วันที่ 28 ม.ค. 67 เวลา 10:30")
        assert result == date(2024, 1, 28)

        # Multiple dates - should return first match
        result = parser.parse("From 28/01/2024 to 30/01/2024")
        assert result == date(2024, 1, 28)

    def test_parse_two_digit_year_variations(self):
        """Test parsing various two-digit year formats."""
        from app.services.parsers.thai_date_parser import ThaiDateParser

        parser = ThaiDateParser()

        # Should handle 2-digit years as Buddhist era
        assert parser.parse("28 ม.ค. 66") == date(2023, 1, 28)
        assert parser.parse("28 ม.ค. 67") == date(2024, 1, 28)
        assert parser.parse("28 ม.ค. 68") == date(2025, 1, 28)

    def test_is_valid_date(self):
        """Test date validation helper."""
        from app.services.parsers.thai_date_parser import ThaiDateParser

        parser = ThaiDateParser()

        # Valid dates
        assert parser._is_valid_date(28, 1, 2024) is True
        assert parser._is_valid_date(31, 12, 2024) is True

        # Invalid dates
        assert parser._is_valid_date(32, 1, 2024) is False  # Invalid day
        assert parser._is_valid_date(28, 13, 2024) is False  # Invalid month
        assert parser._is_valid_date(28, 1, 1800) is False  # Year too old
        assert parser._is_valid_date(28, 1, 2200) is False  # Year too far in future


class TestThaiAmountParser:
    """Tests for ThaiAmountParser class."""

    def test_parse_with_commas_and_decimals(self):
        """Test parsing amount with commas and decimals."""
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        parser = ThaiAmountParser()
        result = parser.parse("1,234.56")

        assert result is not None
        assert result == Decimal("1234.56")

    def test_parse_with_currency_symbol(self):
        """Test parsing amount with Thai currency symbol."""
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        parser = ThaiAmountParser()

        assert parser.parse("฿1,234.56") == Decimal("1234.56")
        assert parser.parse("1,234.56 บาท") == Decimal("1234.56")
        assert parser.parse("THB 1,234.56") == Decimal("1234.56")

    def test_parse_plain_number(self):
        """Test parsing plain number without formatting."""
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        parser = ThaiAmountParser()
        result = parser.parse("1234.56")

        assert result == Decimal("1234.56")

    def test_parse_with_keyword(self):
        """Test parsing amount with Thai keywords."""
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        parser = ThaiAmountParser()

        result = parser.parse("จำนวนเงิน: 1,234.56 บาท")
        assert result == Decimal("1234.56")

        result = parser.parse("amount: 1,234.56")
        assert result == Decimal("1234.56")

    def test_parse_large_amounts(self):
        """Test parsing large currency amounts."""
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        parser = ThaiAmountParser()

        result = parser.parse("1,000,000.00")
        assert result == Decimal("1000000.00")

        result = parser.parse("999,999,999.99")
        assert result == Decimal("999999999.99")

    def test_parse_zero_and_negative(self):
        """Test parsing zero and handling invalid amounts."""
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        parser = ThaiAmountParser()

        # Zero is valid
        result = parser.parse("0.00")
        assert result == Decimal("0")

        # Negative not handled by current implementation
        # (would need to add support if required)

    def test_parse_invalid_amounts(self):
        """Test parsing invalid amount strings."""
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        parser = ThaiAmountParser()

        # Not a number
        assert parser.parse("not a number") is None

        # Empty string
        assert parser.parse("") is None
        assert parser.parse(None) is None

        # Just currency symbol
        assert parser.parse("บาท") is None

    def test_parse_with_noise(self):
        """Test parsing amount with surrounding text."""
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        parser = ThaiAmountParser()

        # Multiple numbers - should return the first valid amount
        result = parser.parse("Total: 1,234.56 and 5,678.90")
        assert result == Decimal("1234.56")

        # Amount in sentence
        result = parser.parse("Transfer amount of 10,000.00 บาท completed")
        assert result == Decimal("10000.00")

    def test_parse_without_decimals(self):
        """Test parsing amounts without decimal places."""
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        parser = ThaiAmountParser()

        # Should handle integers
        result = parser.parse("1,000")
        assert result == Decimal("1000")

        result = parser.parse("500")
        assert result == Decimal("500")

    def test_clean_and_parse(self):
        """Test the clean_and_parse helper method."""
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        parser = ThaiAmountParser()

        # Test cleaning various formats
        assert parser._clean_and_parse("1,234.56") == Decimal("1234.56")
        assert parser._clean_and_parse("฿1,234.56") == Decimal("1234.56")
        assert parser._clean_and_parse("1,234.56บาท") == Decimal("1234.56")
        assert parser._clean_and_parse("THB 1,234.56") == Decimal("1234.56")

        # Test invalid string
        assert parser._clean_and_parse("invalid") is None

    def test_try_currency_pattern(self):
        """Test currency pattern matching."""
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        parser = ThaiAmountParser()

        # Should match various patterns
        assert parser._try_currency_pattern("฿1,234.56") == Decimal("1234.56")
        assert parser._try_currency_pattern("1,234.56 บาท") == Decimal("1234.56")
        assert parser._try_currency_pattern("THB 1,234.56") == Decimal("1234.56")
        assert parser._try_currency_pattern("จำนวนเงิน: 1,234.56") == Decimal("1234.56")

        # Should not match non-currency text
        assert parser._try_currency_pattern("not an amount") is None

    def test_try_number_pattern(self):
        """Test number pattern matching."""
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        parser = ThaiAmountParser()

        # Should match number patterns
        assert parser._try_number_pattern("1,234.56") == Decimal("1234.56")
        assert parser._try_number_pattern("1234.56") == Decimal("1234.56")

        # Should skip zero amounts
        assert parser._try_number_pattern("0.00") is None

        # Should not match text
        assert parser._try_number_pattern("not a number") is None


class TestThaiNameParser:
    """Tests for ThaiNameParser class."""

    def test_parse_thai_name_with_title(self):
        """Test parsing Thai name with title."""
        from app.services.parsers.thai_name_parser import ThaiNameParser

        parser = ThaiNameParser()

        result = parser.parse("นายสมชาย ใจดี")
        assert result == "นายสมชาย ใจดี"

        result = parser.parse("นางสาวมานี มีตา")
        assert result == "นางสาวมานี มีตา"

    def test_parse_english_name_with_title(self):
        """Test parsing English name with title."""
        from app.services.parsers.thai_name_parser import ThaiNameParser

        parser = ThaiNameParser()

        result = parser.parse("Mr. John Doe")
        assert result == "Mr. John Doe"

        result = parser.parse("Mrs. Jane Smith")
        assert result == "Mrs. Jane Smith"

        result = parser.parse("Ms. Mary Johnson")
        assert result == "Ms. Mary Johnson"

    def test_parse_with_prefix_keywords(self):
        """Test parsing names with prefix keywords."""
        from app.services.parsers.thai_name_parser import ThaiNameParser

        parser = ThaiNameParser()

        # Should remove common prefixes
        result = parser.parse("จาก นายสมชาย ใจดี")
        assert result == "นายสมชาย ใจดี"

        result = parser.parse("ผู้ส่ง นางสาวมานี มีตา")
        assert result == "นางสาวมานี มีตา"

        result = parser.parse("ผู้รับ Mr. John Doe")
        assert result == "Mr. John Doe"

    def test_parse_name_without_title(self):
        """Test parsing name without title (if it looks like a name)."""
        from app.services.parsers.thai_name_parser import ThaiNameParser

        parser = ThaiNameParser()

        # Thai name without title
        result = parser.parse("สมชาย ใจดี")
        assert result == "สมชาย ใจดี"

        # English name without title
        result = parser.parse("John Doe")
        assert result == "John Doe"

    def test_parse_invalid_names(self):
        """Test parsing invalid name strings."""
        from app.services.parsers.thai_name_parser import ThaiNameParser

        parser = ThaiNameParser()

        # Too short
        assert parser.parse("A") is None

        # Too long
        assert parser.parse("A" * 101) is None

        # Mostly digits
        assert parser.parse("1234567890") is None

        # Mostly special characters
        assert parser.parse("!@#$%^&*()") is None

    def test_parse_empty_text(self):
        """Test parsing empty text."""
        from app.services.parsers.thai_name_parser import ThaiNameParser

        parser = ThaiNameParser()
        assert parser.parse("") is None
        assert parser.parse(None) is None

    def test_looks_like_name_valid(self):
        """Test name validation with valid names."""
        from app.services.parsers.thai_name_parser import ThaiNameParser

        parser = ThaiNameParser()

        # Valid Thai names
        assert parser._looks_like_name("สมชาย ใจดี") is True
        assert parser._looks_like_name("นายสมชาย ใจดี") is True

        # Valid English names
        assert parser._looks_like_name("John Doe") is True
        assert parser._looks_like_name("Mrs. Jane Smith") is True

    def test_looks_like_name_invalid(self):
        """Test name validation with invalid strings."""
        from app.services.parsers.thai_name_parser import ThaiNameParser

        parser = ThaiNameParser()

        # Too short
        assert parser._looks_like_name("A") is False

        # Too long
        assert parser._looks_like_name("A" * 101) is False

        # Mostly digits
        assert parser._looks_like_name("1234567890") is False

        # Mostly special characters
        assert parser._looks_like_name("!@#$%^&*()") is False

        # No letters
        assert parser._looks_like_name("123-456-7890") is False

    def test_parse_academic_titles(self):
        """Test parsing names with academic titles."""
        from app.services.parsers.thai_name_parser import ThaiNameParser

        parser = ThaiNameParser()

        # Thai academic titles
        result = parser.parse("ดร.สมชาย วิทยาศาสตร์")
        assert result == "ดร.สมชาย วิทยาศาสตร์"

        result = parser.parse("ผศ.ดร.มานี หลักสูตร")
        assert result == "ผศ.ดร.มานี หลักสูตร"

        # English academic titles
        result = parser.parse("Dr. John Smith")
        assert result == "Dr. John Smith"

        result = parser.parse("Prof. Jane Doe")
        assert result == "Prof. Jane Doe"

    def test_parse_with_noise(self):
        """Test parsing name with surrounding noise."""
        from app.services.parsers.thai_name_parser import ThaiNameParser

        parser = ThaiNameParser()

        # Name in sentence
        result = parser.parse("Sender: นายสมชาย ใจดี Account: 123-456")
        # Should extract the name part
        assert result is not None

    def test_remove_prefixes(self):
        """Test prefix removal helper."""
        from app.services.parsers.thai_name_parser import ThaiNameParser

        parser = ThaiNameParser()

        assert parser._remove_prefixes("จาก นายสมชาย ใจดี") == "นายสมชาย ใจดี"
        assert parser._remove_prefixes("ไปยัง นางสาวมานี มีตา") == "นางสาวมานี มีตา"
        assert parser._remove_prefixes("ผู้ส่ง Mr. John Doe") == "Mr. John Doe"
        assert parser._remove_prefixes("ผู้รับ Mrs. Jane Smith") == "Mrs. Jane Smith"

    def test_extract_name_with_title(self):
        """Test title extraction helper."""
        from app.services.parsers.thai_name_parser import ThaiNameParser

        parser = ThaiNameParser()

        # Should find and extract title + name
        result = parser._extract_name_with_title("นายสมชาย ใจดี")
        assert result == "นายสมชาย ใจดี"

        result = parser._extract_name_with_title("Mr. John Doe")
        assert result == "Mr. John Doe"

        # Should return None if no title found
        result = parser._extract_name_with_title("สมชาย ใจดี")
        assert result is None


class TestParserIntegration:
    """Integration tests for parsers working together."""

    def test_complete_receipt_parsing(self):
        """Test parsing a complete receipt with all fields."""
        from app.services.parsers.thai_date_parser import ThaiDateParser
        from app.services.parsers.thai_amount_parser import ThaiAmountParser
        from app.services.parsers.thai_name_parser import ThaiNameParser

        date_parser = ThaiDateParser()
        amount_parser = ThaiAmountParser()
        name_parser = ThaiNameParser()

        # Simulate OCR results from different zones
        date_text = "28 ม.ค. 67"
        sender_text = "จาก นายสมชาย ใจดี"
        receiver_text = "ผู้รับ นางสาวมานี มีตา"
        amount_text = "1,234.56 บาท"

        # Parse all fields
        parsed_date = date_parser.parse(date_text)
        parsed_sender = name_parser.parse(sender_text)
        parsed_receiver = name_parser.parse(receiver_text)
        parsed_amount = amount_parser.parse(amount_text)

        # Verify all parsed correctly
        assert parsed_date == date(2024, 1, 28)
        assert parsed_sender == "นายสมชาย ใจดี"
        assert parsed_receiver == "นางสาวมานี มีตา"
        assert parsed_amount == Decimal("1234.56")

    def test_parser_error_handling(self):
        """Test parser behavior with various edge cases."""
        from app.services.parsers.thai_date_parser import ThaiDateParser
        from app.services.parsers.thai_amount_parser import ThaiAmountParser
        from app.services.parsers.thai_name_parser import ThaiNameParser

        date_parser = ThaiDateParser()
        amount_parser = ThaiAmountParser()
        name_parser = ThaiNameParser()

        # All parsers should handle None gracefully
        assert date_parser.parse(None) is None
        assert amount_parser.parse(None) is None
        assert name_parser.parse(None) is None

        # All parsers should handle empty strings
        assert date_parser.parse("") is None
        assert amount_parser.parse("") is None
        assert name_parser.parse("") is None

        # All parsers should handle invalid input
        assert date_parser.parse("not valid input") is None
        assert amount_parser.parse("not valid input") is None
        assert name_parser.parse("not valid input") is None

    def test_parser_multilingual_support(self):
        """Test parsers handle both Thai and English input."""
        from app.services.parsers.thai_date_parser import ThaiDateParser
        from app.services.parsers.thai_name_parser import ThaiNameParser

        date_parser = ThaiDateParser()
        name_parser = ThaiNameParser()

        # Date parser should handle both formats
        thai_date = date_parser.parse("28 ม.ค. 67")
        eng_date = date_parser.parse("28/01/2024")

        assert thai_date is not None
        assert eng_date is not None

        # Name parser should handle both languages
        thai_name = name_parser.parse("นายสมชาย ใจดี")
        eng_name = name_parser.parse("Mr. John Doe")

        assert thai_name is not None
        assert eng_name is not None

    def test_parser_whitespace_handling(self):
        """Test that parsers handle various whitespace correctly."""
        from app.services.parsers.thai_date_parser import ThaiDateParser
        from app.services.parsers.thai_amount_parser import ThaiAmountParser

        date_parser = ThaiDateParser()
        amount_parser = ThaiAmountParser()

        # Extra whitespace should be handled
        assert date_parser.parse("28   ม.ค.   67") is not None
        assert amount_parser.parse("1,234.56  บาท") is not None

        # Newlines and tabs should be handled
        assert date_parser.parse("28\nม.ค.\t67") is not None
        assert amount_parser.parse("1,234.56\nบาท") is not None
