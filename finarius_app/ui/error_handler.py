"""Error handling utilities for Finarius Streamlit app."""

import logging
import traceback
from typing import Callable, Any, Optional
import streamlit as st

from finarius_app.ui.session_state import set_error_message
from finarius_app.core.exceptions import FinariusException

logger = logging.getLogger(__name__)


def handle_error(error: Exception, user_message: Optional[str] = None) -> None:
    """Handle and display error to user.

    Args:
        error: Exception that occurred.
        user_message: User-friendly error message. If None, generates message from exception.
    """
    # Log detailed error with full traceback
    logger.error(f"Error occurred: {error}", exc_info=True)

    # Display user-friendly message
    if user_message:
        set_error_message(user_message)
    elif isinstance(error, FinariusException):
        # Use the exception's message which is already user-friendly
        message = error.message
        # Add helpful context from details if available
        if error.details:
            context_parts = []
            if "symbol" in error.details:
                context_parts.append(f"Symbol: {error.details['symbol']}")
            if "field" in error.details:
                context_parts.append(f"Field: {error.details['field']}")
            if context_parts:
                message += f" ({', '.join(context_parts)})"
        set_error_message(message)
    else:
        # Default user-friendly message for unknown exceptions
        error_type = type(error).__name__
        set_error_message(
            f"An error occurred: {error_type}. Please check the logs for details."
        )


def error_handler(func: Callable) -> Callable:
    """Decorator to handle errors in Streamlit functions.

    This decorator wraps a function and catches any exceptions, displaying
    them to the user in a user-friendly way while logging the full error.

    Args:
        func: Function to wrap.

    Returns:
        Wrapped function with error handling.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_error(e)
            # Re-raise to stop execution if needed
            raise

    return wrapper


def safe_execute(
    func: Callable, *args: Any, default: Any = None, **kwargs: Any
) -> Any:
    """Safely execute a function and return default on error.

    Args:
        func: Function to execute.
        *args: Positional arguments for function.
        default: Default value to return on error.
        **kwargs: Keyword arguments for function.

    Returns:
        Function result or default value on error.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in safe_execute: {e}", exc_info=True)
        return default

