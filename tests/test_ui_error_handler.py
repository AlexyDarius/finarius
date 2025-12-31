"""Tests for UI error handler module."""

import pytest
from unittest.mock import MagicMock, patch

from finarius_app.ui.error_handler import (
    handle_error,
    error_handler,
    safe_execute,
)


class TestErrorHandler:
    """Test error handler module."""

    @patch("finarius_app.ui.error_handler.logger")
    @patch("finarius_app.ui.error_handler.set_error_message")
    def test_handle_error_with_message(self, mock_set_error, mock_logger):
        """Test handling error with custom message."""
        error = ValueError("Test error")

        handle_error(error, "Custom error message")

        mock_logger.error.assert_called_once()
        mock_set_error.assert_called_once_with("Custom error message")

    @patch("finarius_app.ui.error_handler.logger")
    @patch("finarius_app.ui.error_handler.set_error_message")
    def test_handle_error_without_message(self, mock_set_error, mock_logger):
        """Test handling error without custom message."""
        error = ValueError("Test error")

        handle_error(error)

        mock_logger.error.assert_called_once()
        mock_set_error.assert_called_once()
        # Verify default message format
        call_args = mock_set_error.call_args[0][0]
        assert "ValueError" in call_args

    @patch("finarius_app.ui.error_handler.handle_error")
    def test_error_handler_decorator_success(self, mock_handle_error):
        """Test error handler decorator on successful function."""

        @error_handler
        def test_func(x: int, y: int) -> int:
            return x + y

        result = test_func(2, 3)

        assert result == 5
        mock_handle_error.assert_not_called()

    @patch("finarius_app.ui.error_handler.handle_error")
    def test_error_handler_decorator_error(self, mock_handle_error):
        """Test error handler decorator on function that raises error."""

        @error_handler
        def test_func() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            test_func()

        mock_handle_error.assert_called_once()

    def test_safe_execute_success(self):
        """Test safe_execute with successful function."""

        def test_func(x: int, y: int) -> int:
            return x + y

        result = safe_execute(test_func, 2, 3)

        assert result == 5

    @patch("finarius_app.ui.error_handler.logger")
    def test_safe_execute_error(self, mock_logger):
        """Test safe_execute with function that raises error."""

        def test_func() -> None:
            raise ValueError("Test error")

        result = safe_execute(test_func, default="default_value")

        assert result == "default_value"
        mock_logger.error.assert_called_once()

    @patch("finarius_app.ui.error_handler.logger")
    def test_safe_execute_error_no_default(self, mock_logger):
        """Test safe_execute with function that raises error and no default."""

        def test_func() -> None:
            raise ValueError("Test error")

        result = safe_execute(test_func)

        assert result is None
        mock_logger.error.assert_called_once()

    def test_safe_execute_with_kwargs(self):
        """Test safe_execute with keyword arguments."""

        def test_func(x: int, y: int = 0) -> int:
            return x + y

        result = safe_execute(test_func, 5, y=3)

        assert result == 8

