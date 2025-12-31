"""Session state management for Finarius Streamlit app."""

from typing import Optional, Any
import streamlit as st

from finarius_app.core.database import Database


def initialize_session_state() -> None:
    """Initialize session state with default values."""
    # Database instance
    if "db" not in st.session_state:
        st.session_state.db = None

    # Selected page (for navigation)
    if "selected_page" not in st.session_state:
        from finarius_app.ui.navigation import PAGE_DASHBOARD
        st.session_state.selected_page = PAGE_DASHBOARD

    # Selected account (for filtering)
    if "selected_account_id" not in st.session_state:
        st.session_state.selected_account_id = None

    # Date range for analytics
    if "date_range" not in st.session_state:
        st.session_state.date_range = None

    # UI state
    if "show_transaction_form" not in st.session_state:
        st.session_state.show_transaction_form = False

    if "editing_transaction_id" not in st.session_state:
        st.session_state.editing_transaction_id = None

    if "show_account_form" not in st.session_state:
        st.session_state.show_account_form = False

    if "editing_account_id" not in st.session_state:
        st.session_state.editing_account_id = None

    # Error messages
    if "error_message" not in st.session_state:
        st.session_state.error_message = None

    if "success_message" not in st.session_state:
        st.session_state.success_message = None


def get_db() -> Optional[Database]:
    """Get database instance from session state.

    Returns:
        Database instance or None if not initialized.
    """
    return st.session_state.get("db")


def set_db(db: Database) -> None:
    """Set database instance in session state.

    Args:
        db: Database instance.
    """
    st.session_state.db = db


def clear_messages() -> None:
    """Clear error and success messages from session state."""
    st.session_state.error_message = None
    st.session_state.success_message = None


def set_error_message(message: str) -> None:
    """Set error message in session state.

    Args:
        message: Error message to display.
    """
    st.session_state.error_message = message
    st.session_state.success_message = None


def set_success_message(message: str) -> None:
    """Set success message in session state.

    Args:
        message: Success message to display.
    """
    st.session_state.success_message = message
    st.session_state.error_message = None


def display_messages() -> None:
    """Display error and success messages if present."""
    if st.session_state.get("error_message"):
        st.error(st.session_state.error_message)
        st.session_state.error_message = None

    if st.session_state.get("success_message"):
        st.success(st.session_state.success_message)
        st.session_state.success_message = None


def get_session_value(key: str, default: Any = None) -> Any:
    """Get value from session state.

    Args:
        key: Session state key.
        default: Default value if key doesn't exist.

    Returns:
        Value from session state or default.
    """
    return st.session_state.get(key, default)


def set_session_value(key: str, value: Any) -> None:
    """Set value in session state.

    Args:
        key: Session state key.
        value: Value to set.
    """
    st.session_state[key] = value

