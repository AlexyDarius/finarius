"""Finarius core portfolio engine and calculations."""

from . import prices
from . import engine
from . import metrics
from .config import Config
from .logger import setup_logging, get_logger, reset_logging, set_log_level
from .exceptions import (
    FinariusException,
    DatabaseError,
    PriceDownloadError,
    ValidationError,
    SymbolNotFoundError,
    InsufficientDataError,
    ConfigurationError,
    CalculationError,
)
from .utils import (
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

__all__ = [
    "prices",
    "engine",
    "metrics",
    "Config",
    "setup_logging",
    "get_logger",
    "reset_logging",
    "set_log_level",
    "FinariusException",
    "DatabaseError",
    "PriceDownloadError",
    "ValidationError",
    "SymbolNotFoundError",
    "InsufficientDataError",
    "ConfigurationError",
    "CalculationError",
    # Date utilities
    "parse_date",
    "format_date",
    "get_date_range",
    # Number utilities
    "format_currency",
    "format_percentage",
    "round_decimal",
    # Validation utilities
    "validate_symbol",
    "validate_date",
    "validate_amount",
    # Data utilities
    "safe_divide",
    "calculate_percentage_change",
]

