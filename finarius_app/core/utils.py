"""Utility functions for Finarius application.

This module provides common utility functions for date handling, number formatting,
validation, and data manipulation used throughout the application.
"""

from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal, ROUND_HALF_UP

from .config import Config
from .exceptions import ValidationError


# Date utilities
def parse_date(date_string: str, date_format: Optional[str] = None) -> date:
    """Parse a date string into a date object.

    Supports multiple date formats. If date_format is not provided,
    tries common formats or uses config default.

    Args:
        date_string: Date string to parse (e.g., "2024-01-15", "01/15/2024").
        date_format: Optional format string. If None, tries common formats.

    Returns:
        Parsed date object.

    Raises:
        ValidationError: If date string cannot be parsed.

    Example:
        >>> parse_date("2024-01-15")
        datetime.date(2024, 1, 15)
        >>> parse_date("01/15/2024", "%m/%d/%Y")
        datetime.date(2024, 1, 15)
    """
    if date_format:
        try:
            return datetime.strptime(date_string, date_format).date()
        except ValueError as e:
            raise ValidationError(
                f"Invalid date format: {date_string}",
                {"date_string": date_string, "format": date_format},
            ) from e

    # Try common formats
    formats = [
        "%Y-%m-%d",  # ISO format
        "%m/%d/%Y",  # US format
        "%d/%m/%Y",  # European format
        "%Y-%m-%d %H:%M:%S",  # ISO with time
        "%m-%d-%Y",  # US format with dashes
        "%d-%m-%Y",  # European format with dashes
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue

    # Try using config default format
    try:
        config = Config()
        default_format = config.get("display.date_format", "%Y-%m-%d")
        return datetime.strptime(date_string, default_format).date()
    except (ValueError, AttributeError):
        pass

    raise ValidationError(
        f"Unable to parse date: {date_string}",
        {"date_string": date_string},
    )


def format_date(d: date, date_format: Optional[str] = None) -> str:
    """Format a date object as a string.

    Uses the configured date format from config if not provided.

    Args:
        d: Date object to format.
        date_format: Optional format string. If None, uses config default.

    Returns:
        Formatted date string.

    Example:
        >>> format_date(date(2024, 1, 15))
        '2024-01-15'
        >>> format_date(date(2024, 1, 15), "%m/%d/%Y")
        '01/15/2024'
    """
    if date_format is None:
        config = Config()
        date_format = config.get("display.date_format", "%Y-%m-%d")

    return d.strftime(date_format)


def get_date_range(start: date, end: date, step_days: int = 1) -> List[date]:
    """Generate a list of dates between start and end (inclusive).

    Args:
        start: Start date (inclusive).
        end: End date (inclusive).
        step_days: Number of days between each date. Default is 1 (daily).

    Returns:
        List of date objects from start to end.

    Raises:
        ValidationError: If start date is after end date.

    Example:
        >>> get_date_range(date(2024, 1, 1), date(2024, 1, 5))
        [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)]
    """
    if start > end:
        raise ValidationError(
            "Start date must be before or equal to end date",
            {"start": str(start), "end": str(end)},
        )

    dates = []
    current = start
    while current <= end:
        dates.append(current)
        # Add step_days to current date
        from datetime import timedelta

        current += timedelta(days=step_days)

    return dates


# Number utilities
def format_currency(amount: float, currency: Optional[str] = None) -> str:
    """Format a number as currency.

    Uses the configured currency and number format from config.

    Args:
        amount: Amount to format.
        currency: Currency code (e.g., "USD", "EUR"). If None, uses config default.

    Returns:
        Formatted currency string.

    Example:
        >>> format_currency(1234.56, "USD")
        '$1,234.56'
        >>> format_currency(1234.56, "EUR")
        '€1,234.56'
    """
    if currency is None:
        config = Config()
        currency = config.get("display.default_currency", "USD")

    # Currency symbols
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "CAD": "C$",
        "AUD": "A$",
        "CHF": "CHF",
        "CNY": "¥",
    }

    symbol = symbols.get(currency, currency)

    # Get number format from config
    config = Config()
    number_format = config.get("display.number_format", "{:,.2f}")

    formatted = number_format.format(abs(amount))
    if amount < 0:
        return f"-{symbol}{formatted}"
    return f"{symbol}{formatted}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format a number as a percentage.

    Args:
        value: Value to format (e.g., 0.15 for 15%).
        decimals: Number of decimal places. Default is 2.

    Returns:
        Formatted percentage string.

    Example:
        >>> format_percentage(0.15)
        '15.00%'
        >>> format_percentage(0.15234, 1)
        '15.2%'
    """
    percentage = value * 100
    return f"{percentage:.{decimals}f}%"


def round_decimal(value: float, decimals: int = 2) -> float:
    """Round a decimal number to specified decimal places.

    Uses banker's rounding (round half to even) for consistency.

    Args:
        value: Value to round.
        decimals: Number of decimal places. Default is 2.

    Returns:
        Rounded value.

    Example:
        >>> round_decimal(3.14159, 2)
        3.14
        >>> round_decimal(3.145, 2)
        3.14
    """
    if decimals < 0:
        raise ValidationError(
            "Decimal places must be non-negative",
            {"decimals": decimals},
        )

    # Use Decimal for precise rounding
    d = Decimal(str(value))
    quantizer = Decimal(10) ** -decimals
    rounded = d.quantize(quantizer, rounding=ROUND_HALF_UP)
    return float(rounded)


# Validation utilities
def validate_symbol(symbol: str) -> bool:
    """Validate a stock symbol format.

    Basic validation for symbol format. For more comprehensive validation,
    use prices.validation.validate_symbol or prices.validation.symbol_exists.

    Args:
        symbol: Symbol string to validate.

    Returns:
        True if symbol format is valid, False otherwise.

    Example:
        >>> validate_symbol("AAPL")
        True
        >>> validate_symbol("")
        False
        >>> validate_symbol("123")
        False
    """
    if not symbol or not isinstance(symbol, str):
        return False

    # Basic validation: 1-10 characters, alphanumeric and some special chars
    symbol = symbol.strip().upper()
    if len(symbol) < 1 or len(symbol) > 10:
        return False

    # Allow letters, numbers, dots, and hyphens
    return symbol.replace(".", "").replace("-", "").isalnum()


def validate_date(d: date) -> bool:
    """Validate that a date object is valid.

    Args:
        d: Date object to validate.

    Returns:
        True if date is valid, False otherwise.

    Example:
        >>> validate_date(date(2024, 1, 15))
        True
        >>> validate_date(date(1900, 1, 1))
        True
    """
    if not isinstance(d, date):
        return False

    # Check for reasonable date range (not too far in past or future)
    min_date = date(1900, 1, 1)
    max_date = date(2100, 12, 31)

    return min_date <= d <= max_date


def validate_amount(amount: float) -> bool:
    """Validate that an amount is valid (non-negative, finite).

    Args:
        amount: Amount to validate.

    Returns:
        True if amount is valid, False otherwise.

    Example:
        >>> validate_amount(100.50)
        True
        >>> validate_amount(-10)
        False
        >>> validate_amount(float('inf'))
        False
    """
    if not isinstance(amount, (int, float)):
        return False

    # Check for finite value
    import math

    if not math.isfinite(amount):
        return False

    # Check for non-negative
    return amount >= 0


# Data utilities
def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero.

    Args:
        numerator: Numerator value.
        denominator: Denominator value.
        default: Value to return if denominator is zero. Default is 0.0.

    Returns:
        Division result or default value.

    Example:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)
        0.0
        >>> safe_divide(10, 0, default=float('inf'))
        inf
    """
    if denominator == 0:
        return default
    return numerator / denominator


def calculate_percentage_change(old: float, new: float) -> float:
    """Calculate percentage change between two values.

    Formula: ((new - old) / old) * 100

    Args:
        old: Original value.
        new: New value.

    Returns:
        Percentage change as a decimal (e.g., 0.15 for 15% increase).

    Raises:
        ValidationError: If old value is zero (division by zero).

    Example:
        >>> calculate_percentage_change(100, 110)
        0.1
        >>> calculate_percentage_change(100, 90)
        -0.1
    """
    if old == 0:
        raise ValidationError(
            "Cannot calculate percentage change: original value is zero",
            {"old": old, "new": new},
        )

    return (new - old) / old

