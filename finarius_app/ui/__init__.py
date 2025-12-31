"""Finarius Streamlit UI components."""

from .navigation import (
    render_sidebar,
    get_page_title,
    get_page_icon,
    PAGE_DASHBOARD,
    PAGE_ACCOUNTS,
    PAGE_TRANSACTIONS,
    PAGE_PORTFOLIO,
    PAGE_ANALYTICS,
    PAGE_SETTINGS,
)
from .session_state import (
    initialize_session_state,
    get_db,
    set_db,
    clear_messages,
    set_error_message,
    set_success_message,
    display_messages,
    get_session_value,
    set_session_value,
)
from .error_handler import (
    handle_error,
    error_handler,
    safe_execute,
)
from .accounts import render_accounts_page
from .transactions import render_transactions_page

__all__ = [
    # Navigation
    "render_sidebar",
    "get_page_title",
    "get_page_icon",
    "PAGE_DASHBOARD",
    "PAGE_ACCOUNTS",
    "PAGE_TRANSACTIONS",
    "PAGE_PORTFOLIO",
    "PAGE_ANALYTICS",
    "PAGE_SETTINGS",
    # Session state
    "initialize_session_state",
    "get_db",
    "set_db",
    "clear_messages",
    "set_error_message",
    "set_success_message",
    "display_messages",
    "get_session_value",
    "set_session_value",
    # Error handling
    "handle_error",
    "error_handler",
    "safe_execute",
    # Accounts UI
    "render_accounts_page",
    # Transactions UI
    "render_transactions_page",
]

