"""Tests for exceptions module."""

import pytest
from finarius_app.core.exceptions import (
    FinariusException,
    DatabaseError,
    PriceDownloadError,
    ValidationError,
    SymbolNotFoundError,
    InsufficientDataError,
    ConfigurationError,
    CalculationError,
)


class TestFinariusException:
    """Test base FinariusException class."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = FinariusException("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.details == {}

    def test_exception_with_details(self):
        """Test exception with details dictionary."""
        details = {"key": "value", "code": 123}
        exc = FinariusException("Test error", details)
        assert exc.message == "Test error"
        assert exc.details == details
        assert "key=value" in str(exc)
        assert "code=123" in str(exc)

    def test_exception_to_dict(self):
        """Test exception serialization to dictionary."""
        details = {"symbol": "AAPL", "date": "2024-01-01"}
        exc = FinariusException("Test error", details)
        result = exc.to_dict()

        assert result["type"] == "FinariusException"
        assert result["message"] == "Test error"
        assert result["details"] == details

    def test_exception_inheritance(self):
        """Test that exception is a proper Exception."""
        exc = FinariusException("Test error")
        assert isinstance(exc, Exception)
        assert isinstance(exc, FinariusException)


class TestDatabaseError:
    """Test DatabaseError exception."""

    def test_database_error_basic(self):
        """Test basic DatabaseError creation."""
        exc = DatabaseError("Database connection failed")
        assert isinstance(exc, FinariusException)
        assert isinstance(exc, DatabaseError)
        assert str(exc) == "Database connection failed"

    def test_database_error_with_details(self):
        """Test DatabaseError with details."""
        details = {"db_path": "db.sqlite", "error_code": "SQLITE_CANTOPEN"}
        exc = DatabaseError("Failed to open database", details)
        assert exc.details == details
        assert "db_path=db.sqlite" in str(exc)


class TestPriceDownloadError:
    """Test PriceDownloadError exception."""

    def test_price_download_error_basic(self):
        """Test basic PriceDownloadError creation."""
        exc = PriceDownloadError("Failed to download price")
        assert isinstance(exc, FinariusException)
        assert isinstance(exc, PriceDownloadError)

    def test_price_download_error_with_details(self):
        """Test PriceDownloadError with details."""
        details = {"symbol": "AAPL", "date": "2024-01-01", "status_code": 500}
        exc = PriceDownloadError("Network error", details)
        assert exc.details == details
        assert "symbol=AAPL" in str(exc)


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_basic(self):
        """Test basic ValidationError creation."""
        exc = ValidationError("Invalid input")
        assert isinstance(exc, FinariusException)
        assert isinstance(exc, ValidationError)

    def test_validation_error_with_details(self):
        """Test ValidationError with details."""
        details = {"field": "symbol", "value": "INVALID", "reason": "Invalid format"}
        exc = ValidationError("Validation failed", details)
        assert exc.details == details


class TestSymbolNotFoundError:
    """Test SymbolNotFoundError exception."""

    def test_symbol_not_found_error_basic(self):
        """Test basic SymbolNotFoundError creation."""
        exc = SymbolNotFoundError("Symbol not found")
        assert isinstance(exc, FinariusException)
        assert isinstance(exc, SymbolNotFoundError)

    def test_symbol_not_found_error_with_details(self):
        """Test SymbolNotFoundError with details."""
        details = {"symbol": "INVALID", "exchange": "NYSE"}
        exc = SymbolNotFoundError("Symbol does not exist", details)
        assert exc.details == details
        assert "symbol=INVALID" in str(exc)


class TestInsufficientDataError:
    """Test InsufficientDataError exception."""

    def test_insufficient_data_error_basic(self):
        """Test basic InsufficientDataError creation."""
        exc = InsufficientDataError("Not enough data")
        assert isinstance(exc, FinariusException)
        assert isinstance(exc, InsufficientDataError)

    def test_insufficient_data_error_with_details(self):
        """Test InsufficientDataError with details."""
        details = {"required": 100, "available": 50, "data_type": "prices"}
        exc = InsufficientDataError("Insufficient data for calculation", details)
        assert exc.details == details
        assert "required=100" in str(exc)


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_configuration_error_basic(self):
        """Test basic ConfigurationError creation."""
        exc = ConfigurationError("Invalid configuration")
        assert isinstance(exc, FinariusException)
        assert isinstance(exc, ConfigurationError)

    def test_configuration_error_with_details(self):
        """Test ConfigurationError with details."""
        details = {"config_key": "logging.level", "value": "INVALID", "valid_values": ["DEBUG", "INFO"]}
        exc = ConfigurationError("Invalid log level", details)
        assert exc.details == details


class TestCalculationError:
    """Test CalculationError exception."""

    def test_calculation_error_basic(self):
        """Test basic CalculationError creation."""
        exc = CalculationError("Calculation failed")
        assert isinstance(exc, FinariusException)
        assert isinstance(exc, CalculationError)

    def test_calculation_error_with_details(self):
        """Test CalculationError with details."""
        details = {"operation": "division", "divisor": 0, "metric": "return"}
        exc = CalculationError("Division by zero", details)
        assert exc.details == details


class TestExceptionHierarchy:
    """Test exception hierarchy and inheritance."""

    def test_all_exceptions_inherit_from_finarius_exception(self):
        """Test that all exceptions inherit from FinariusException."""
        exceptions = [
            DatabaseError("test"),
            PriceDownloadError("test"),
            ValidationError("test"),
            SymbolNotFoundError("test"),
            InsufficientDataError("test"),
            ConfigurationError("test"),
            CalculationError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, FinariusException)
            assert isinstance(exc, Exception)

    def test_exception_catching(self):
        """Test that all Finarius exceptions can be caught together."""
        exceptions = [
            DatabaseError("db error"),
            PriceDownloadError("price error"),
            ValidationError("validation error"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except FinariusException as e:
                assert isinstance(e, FinariusException)
                assert e.message in ["db error", "price error", "validation error"]
            except Exception:
                pytest.fail("Should have caught FinariusException")

    def test_specific_exception_catching(self):
        """Test that specific exceptions can be caught individually."""
        try:
            raise DatabaseError("db error")
        except DatabaseError as e:
            assert e.message == "db error"
        except FinariusException:
            pytest.fail("Should have caught DatabaseError specifically")
        except Exception:
            pytest.fail("Should have caught DatabaseError")


class TestExceptionSerialization:
    """Test exception serialization."""

    def test_all_exceptions_serializable(self):
        """Test that all exceptions can be serialized to dict."""
        exceptions = [
            DatabaseError("db error", {"path": "db.sqlite"}),
            PriceDownloadError("price error", {"symbol": "AAPL"}),
            ValidationError("validation error", {"field": "date"}),
            SymbolNotFoundError("symbol error", {"symbol": "INVALID"}),
            InsufficientDataError("data error", {"required": 10}),
            ConfigurationError("config error", {"key": "level"}),
            CalculationError("calc error", {"operation": "divide"}),
        ]

        for exc in exceptions:
            result = exc.to_dict()
            assert "type" in result
            assert "message" in result
            assert "details" in result
            assert result["type"] == exc.__class__.__name__
            assert result["message"] == exc.message
            assert result["details"] == exc.details

