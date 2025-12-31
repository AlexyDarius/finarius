"""Custom exceptions for price downloader module."""


class FinariusPriceException(Exception):
    """Base exception for price-related errors."""

    pass


class PriceDownloadError(FinariusPriceException):
    """Exception raised when price download fails."""

    pass


class SymbolNotFoundError(FinariusPriceException):
    """Exception raised when a symbol is not found or invalid."""

    pass


class ValidationError(FinariusPriceException):
    """Exception raised when validation fails."""

    pass


class InsufficientDataError(FinariusPriceException):
    """Exception raised when insufficient data is available."""

    pass

