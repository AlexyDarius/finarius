"""Symbol validation utilities for price downloader."""

import re
import logging
from typing import Optional

import yfinance as yf

from .exceptions import SymbolNotFoundError, ValidationError

logger = logging.getLogger(__name__)

# Common exchange suffixes
EXCHANGE_SUFFIXES = {
    ".TO": "Toronto Stock Exchange",
    ".V": "TSX Venture Exchange",
    ".L": "London Stock Exchange",
    ".PA": "Paris Stock Exchange",
    ".DE": "Deutsche Börse",
    ".AS": "Amsterdam Stock Exchange",
    ".BR": "Brussels Stock Exchange",
    ".MI": "Milan Stock Exchange",
    ".MC": "Madrid Stock Exchange",
    ".SW": "SIX Swiss Exchange",
    ".HK": "Hong Kong Stock Exchange",
    ".T": "Tokyo Stock Exchange",
    ".SS": "Shanghai Stock Exchange",
    ".SZ": "Shenzhen Stock Exchange",
    ".AX": "Australian Securities Exchange",
    ".NZ": "New Zealand Stock Exchange",
    ".SA": "São Paulo Stock Exchange",
    ".MX": "Mexican Stock Exchange",
    ".IS": "Iceland Stock Exchange",
    ".OL": "Oslo Stock Exchange",
    ".ST": "Stockholm Stock Exchange",
    ".CO": "Copenhagen Stock Exchange",
    ".HE": "Helsinki Stock Exchange",
    ".AT": "Athens Stock Exchange",
    ".LS": "Lisbon Stock Exchange",
    ".VI": "Vienna Stock Exchange",
    ".WSE": "Warsaw Stock Exchange",
}

# Crypto currency prefixes/suffixes
CRYPTO_PATTERNS = [
    r"^[A-Z]{2,10}-USD$",  # BTC-USD, ETH-USD, etc.
    r"^[A-Z]{2,10}-EUR$",  # BTC-EUR, etc.
    r"^[A-Z]{2,10}-GBP$",  # BTC-GBP, etc.
]


def validate_symbol(symbol: str) -> bool:
    """Validate symbol format.

    Args:
        symbol: Stock symbol to validate.

    Returns:
        True if symbol format is valid.

    Raises:
        ValidationError: If symbol format is invalid.
    """
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol must be a non-empty string")

    symbol = symbol.strip().upper()

    if not symbol:
        raise ValidationError("Symbol cannot be empty or whitespace")

    # Basic format validation: alphanumeric, dots, hyphens allowed
    if not re.match(r"^[A-Z0-9.\-]+$", symbol):
        raise ValidationError(
            f"Symbol '{symbol}' contains invalid characters. "
            "Only letters, numbers, dots, and hyphens are allowed."
        )

    # Check minimum length
    if len(symbol) < 1:
        raise ValidationError("Symbol must be at least 1 character long")

    # Check maximum length (reasonable limit)
    if len(symbol) > 20:
        raise ValidationError("Symbol cannot exceed 20 characters")

    logger.debug(f"Symbol format validated: {symbol}")
    return True


def symbol_exists(symbol: str, timeout: int = 5) -> bool:
    """Check if symbol exists and is valid.

    This function attempts to fetch basic info for the symbol to verify
    it exists in the market data provider.

    Args:
        symbol: Stock symbol to check.
        timeout: Request timeout in seconds.

    Returns:
        True if symbol exists, False otherwise.

    Raises:
        ValidationError: If symbol format is invalid.
    """
    # First validate format
    validate_symbol(symbol)

    symbol = symbol.strip().upper()

    try:
        ticker = yf.Ticker(symbol)
        # Try to get basic info (fast operation)
        info = ticker.info

        # Check if we got valid info
        if info and isinstance(info, dict) and len(info) > 0:
            # Some symbols return empty dicts, check for key fields
            if "symbol" in info or "shortName" in info or "longName" in info:
                logger.debug(f"Symbol exists: {symbol}")
                return True

        logger.warning(f"Symbol '{symbol}' returned empty or invalid info")
        return False

    except Exception as e:
        logger.debug(f"Symbol '{symbol}' does not exist or error occurred: {e}")
        return False


def get_symbol_info(symbol: str) -> Optional[dict]:
    """Get basic information about a symbol.

    Args:
        symbol: Stock symbol.

    Returns:
        Dictionary with symbol information or None if not found.

    Raises:
        ValidationError: If symbol format is invalid.
        SymbolNotFoundError: If symbol is not found.
    """
    validate_symbol(symbol)

    symbol = symbol.strip().upper()

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        if not info or not isinstance(info, dict) or len(info) == 0:
            raise SymbolNotFoundError(f"Symbol '{symbol}' not found or has no data")

        return {
            "symbol": info.get("symbol", symbol),
            "short_name": info.get("shortName"),
            "long_name": info.get("longName"),
            "exchange": info.get("exchange"),
            "currency": info.get("currency"),
            "quote_type": info.get("quoteType"),  # EQUITY, ETF, CRYPTO, etc.
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }

    except SymbolNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting symbol info for '{symbol}': {e}")
        raise SymbolNotFoundError(f"Error retrieving info for symbol '{symbol}': {e}")

