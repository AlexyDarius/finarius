"""Custom exceptions for Finarius application.

This module provides a hierarchy of custom exceptions for different
error scenarios in the application. All exceptions inherit from
FinariusException for easy catching and handling.
"""

from typing import Optional


class FinariusException(Exception):
    """Base exception class for all Finarius-specific exceptions.

    This exception serves as the base class for all custom exceptions
    in the Finarius application. It allows catching all application-specific
    errors with a single exception type.

    Attributes:
        message: Error message describing what went wrong.
        details: Optional dictionary with additional error details.
    """

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        """Initialize FinariusException.

        Args:
            message: Human-readable error message.
            details: Optional dictionary with additional error context.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of exception."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message

    def to_dict(self) -> dict:
        """Convert exception to dictionary for serialization.

        Returns:
            Dictionary with exception type, message, and details.
        """
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class DatabaseError(FinariusException):
    """Exception raised for database-related errors.

    This exception is raised when database operations fail, such as:
    - Connection failures
    - Query execution errors
    - Constraint violations
    - Transaction failures

    Example:
        >>> raise DatabaseError("Failed to connect to database", {"db_path": "db.sqlite"})
    """

    pass


class PriceDownloadError(FinariusException):
    """Exception raised when price download fails.

    This exception is raised when downloading market data fails, such as:
    - Network errors
    - API rate limiting
    - Invalid response format
    - Timeout errors

    Example:
        >>> raise PriceDownloadError("Failed to download price for AAPL", {"symbol": "AAPL"})
    """

    pass


class ValidationError(FinariusException):
    """Exception raised when validation fails.

    This exception is raised when input validation fails, such as:
    - Invalid symbol format
    - Invalid date range
    - Invalid transaction data
    - Missing required fields

    Example:
        >>> raise ValidationError("Invalid symbol format", {"symbol": "INVALID"})
    """

    pass


class SymbolNotFoundError(FinariusException):
    """Exception raised when a symbol is not found or invalid.

    This exception is raised when:
    - Symbol doesn't exist in the market
    - Symbol format is invalid
    - Symbol is not available for the requested date range

    Example:
        >>> raise SymbolNotFoundError("Symbol not found", {"symbol": "INVALID"})
    """

    pass


class InsufficientDataError(FinariusException):
    """Exception raised when insufficient data is available.

    This exception is raised when:
    - Not enough historical data for calculations
    - Missing price data for required dates
    - Empty portfolio or account
    - Insufficient transactions for analysis

    Example:
        >>> raise InsufficientDataError("Not enough data for calculation", {"required": 10, "available": 5})
    """

    pass


class ConfigurationError(FinariusException):
    """Exception raised for configuration-related errors.

    This exception is raised when:
    - Invalid configuration values
    - Missing required configuration
    - Configuration file parsing errors

    Example:
        >>> raise ConfigurationError("Invalid log level", {"level": "INVALID"})
    """

    pass


class CalculationError(FinariusException):
    """Exception raised when calculations fail.

    This exception is raised when:
    - Mathematical errors (division by zero, etc.)
    - Invalid input for calculations
    - Calculation overflow/underflow

    Example:
        >>> raise CalculationError("Division by zero in return calculation")
    """

    pass

