"""Tests for utility functions module."""

import pytest
from datetime import date, timedelta
from finarius_app.core.utils import (
    parse_date,
    format_date,
    get_date_range,
    format_currency,
    format_percentage,
    round_decimal,
    validate_symbol,
    validate_date,
    validate_amount,
    safe_divide,
    calculate_percentage_change,
)
from finarius_app.core.exceptions import ValidationError


class TestDateUtilities:
    """Test date utility functions."""

    def test_parse_date_iso_format(self):
        """Test parsing ISO format date."""
        result = parse_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_parse_date_us_format(self):
        """Test parsing US format date."""
        result = parse_date("01/15/2024", "%m/%d/%Y")
        assert result == date(2024, 1, 15)

    def test_parse_date_european_format(self):
        """Test parsing European format date."""
        result = parse_date("15/01/2024", "%d/%m/%Y")
        assert result == date(2024, 1, 15)

    def test_parse_date_auto_detect(self):
        """Test automatic format detection."""
        result = parse_date("2024-01-15")
        assert result == date(2024, 1, 15)

        result = parse_date("01/15/2024")
        assert result == date(2024, 1, 15)

    def test_parse_date_invalid(self):
        """Test parsing invalid date raises ValidationError."""
        with pytest.raises(ValidationError):
            parse_date("invalid-date")

    def test_format_date_default(self):
        """Test formatting date with default format."""
        d = date(2024, 1, 15)
        result = format_date(d)
        assert result == "2024-01-15"  # Default ISO format

    def test_format_date_custom(self):
        """Test formatting date with custom format."""
        d = date(2024, 1, 15)
        result = format_date(d, "%m/%d/%Y")
        assert result == "01/15/2024"

    def test_get_date_range_daily(self):
        """Test generating daily date range."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 5)
        result = get_date_range(start, end)

        assert len(result) == 5
        assert result[0] == date(2024, 1, 1)
        assert result[-1] == date(2024, 1, 5)

    def test_get_date_range_weekly(self):
        """Test generating weekly date range."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 15)
        result = get_date_range(start, end, step_days=7)

        assert len(result) == 3
        assert result[0] == date(2024, 1, 1)
        assert result[1] == date(2024, 1, 8)
        assert result[2] == date(2024, 1, 15)

    def test_get_date_range_single_day(self):
        """Test date range with same start and end."""
        d = date(2024, 1, 1)
        result = get_date_range(d, d)
        assert result == [d]

    def test_get_date_range_invalid(self):
        """Test date range with start after end raises ValidationError."""
        start = date(2024, 1, 5)
        end = date(2024, 1, 1)

        with pytest.raises(ValidationError):
            get_date_range(start, end)


class TestNumberUtilities:
    """Test number formatting utilities."""

    def test_format_currency_usd(self):
        """Test formatting USD currency."""
        result = format_currency(1234.56, "USD")
        assert "$" in result
        assert "1,234.56" in result

    def test_format_currency_eur(self):
        """Test formatting EUR currency."""
        result = format_currency(1234.56, "EUR")
        assert "€" in result

    def test_format_currency_negative(self):
        """Test formatting negative currency."""
        result = format_currency(-1234.56, "USD")
        assert "-" in result
        assert "$" in result

    def test_format_currency_default(self):
        """Test formatting currency with default from config."""
        result = format_currency(1234.56)
        assert "$" in result  # Default is USD

    def test_format_percentage_basic(self):
        """Test formatting percentage."""
        result = format_percentage(0.15)
        assert result == "15.00%"

    def test_format_percentage_custom_decimals(self):
        """Test formatting percentage with custom decimals."""
        result = format_percentage(0.15234, 1)
        assert result == "15.2%"

    def test_format_percentage_negative(self):
        """Test formatting negative percentage."""
        result = format_percentage(-0.15)
        assert result == "-15.00%"

    def test_round_decimal_basic(self):
        """Test rounding decimal."""
        result = round_decimal(3.14159, 2)
        assert result == 3.14

    def test_round_decimal_up(self):
        """Test rounding up."""
        result = round_decimal(3.145, 2)
        assert result == 3.15

    def test_round_decimal_zero_decimals(self):
        """Test rounding to zero decimals."""
        result = round_decimal(3.7, 0)
        assert result == 4.0

    def test_round_decimal_negative_decimals(self):
        """Test rounding with negative decimals raises ValidationError."""
        with pytest.raises(ValidationError):
            round_decimal(3.14, -1)


class TestValidationUtilities:
    """Test validation utility functions."""

    def test_validate_symbol_valid(self):
        """Test validating valid symbols."""
        assert validate_symbol("AAPL") is True
        assert validate_symbol("MSFT") is True
        assert validate_symbol("BRK.B") is True
        assert validate_symbol("SPY") is True

    def test_validate_symbol_invalid(self):
        """Test validating invalid symbols."""
        assert validate_symbol("") is False
        assert validate_symbol("   ") is False
        assert validate_symbol("A" * 11) is False  # Too long
        assert validate_symbol("!@#") is False  # Invalid characters

    def test_validate_symbol_special_chars(self):
        """Test symbols with special characters."""
        assert validate_symbol("BRK.B") is True
        assert validate_symbol("SPY-USD") is True

    def test_validate_date_valid(self):
        """Test validating valid dates."""
        assert validate_date(date(2024, 1, 15)) is True
        assert validate_date(date(2000, 1, 1)) is True
        assert validate_date(date(2050, 12, 31)) is True

    def test_validate_date_invalid(self):
        """Test validating invalid dates."""
        assert validate_date(date(1800, 1, 1)) is False  # Too old
        assert validate_date(date(2200, 1, 1)) is False  # Too far future
        assert validate_date("2024-01-15") is False  # Not a date object

    def test_validate_amount_valid(self):
        """Test validating valid amounts."""
        assert validate_amount(100.50) is True
        assert validate_amount(0) is True
        assert validate_amount(1000000) is True

    def test_validate_amount_invalid(self):
        """Test validating invalid amounts."""
        assert validate_amount(-10) is False  # Negative
        assert validate_amount(float("inf")) is False  # Infinity
        assert validate_amount(float("nan")) is False  # NaN
        assert validate_amount("100") is False  # Not a number


class TestDataUtilities:
    """Test data manipulation utilities."""

    def test_safe_divide_normal(self):
        """Test normal division."""
        result = safe_divide(10, 2)
        assert result == 5.0

    def test_safe_divide_by_zero(self):
        """Test division by zero returns default."""
        result = safe_divide(10, 0)
        assert result == 0.0

    def test_safe_divide_by_zero_custom_default(self):
        """Test division by zero with custom default."""
        result = safe_divide(10, 0, default=float("inf"))
        assert result == float("inf")

    def test_safe_divide_negative(self):
        """Test division with negative numbers."""
        result = safe_divide(-10, 2)
        assert result == -5.0

    def test_calculate_percentage_change_increase(self):
        """Test calculating percentage increase."""
        result = calculate_percentage_change(100, 110)
        assert result == 0.1

    def test_calculate_percentage_change_decrease(self):
        """Test calculating percentage decrease."""
        result = calculate_percentage_change(100, 90)
        assert result == -0.1

    def test_calculate_percentage_change_double(self):
        """Test calculating 100% increase."""
        result = calculate_percentage_change(100, 200)
        assert result == 1.0

    def test_calculate_percentage_change_zero_old(self):
        """Test calculating percentage change with zero old value raises ValidationError."""
        with pytest.raises(ValidationError):
            calculate_percentage_change(0, 100)

    def test_calculate_percentage_change_negative(self):
        """Test calculating percentage change with negative values."""
        result = calculate_percentage_change(100, -50)
        assert result == -1.5


class TestUtilityIntegration:
    """Test utility functions working together."""

    def test_date_parse_and_format(self):
        """Test parsing and formatting dates."""
        date_str = "2024-01-15"
        d = parse_date(date_str)
        formatted = format_date(d)
        assert formatted == date_str

    def test_currency_and_percentage(self):
        """Test currency and percentage formatting together."""
        amount = 1000.0
        currency_str = format_currency(amount, "USD")
        percentage_str = format_percentage(0.15)

        assert "$" in currency_str
        assert "15.00%" in percentage_str

    def test_validate_and_format(self):
        """Test validation before formatting."""
        symbol = "AAPL"
        if validate_symbol(symbol):
            # Would use symbol in real scenario
            assert True

        amount = 100.50
        if validate_amount(amount):
            formatted = format_currency(amount)
            assert "$" in formatted

