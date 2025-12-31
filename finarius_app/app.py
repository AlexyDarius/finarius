"""Main Streamlit application entry point."""

import logging
import streamlit as st

from finarius_app.core.database import init_db
from finarius_app.ui import (
    render_sidebar,
    initialize_session_state,
    get_db,
    set_db,
    display_messages,
    error_handler,
    PAGE_DASHBOARD,
    PAGE_ACCOUNTS,
    PAGE_TRANSACTIONS,
    PAGE_PORTFOLIO,
    PAGE_ANALYTICS,
    PAGE_SETTINGS,
)
from finarius_app.ui.accounts import render_accounts_page
from finarius_app.ui.transactions import render_transactions_page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configure Streamlit page settings
st.set_page_config(
    page_title="Finarius",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@error_handler
def initialize_database() -> None:
    """Initialize database connection (singleton pattern)."""
    db = get_db()
    if db is None:
        try:
            logger.info("Initializing database connection...")
            db = init_db()
            set_db(db)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            st.error("Failed to initialize database. Please check the logs.")
            raise


@error_handler
def render_page_content(selected_page: str) -> None:
    """Render content for the selected page.

    Args:
        selected_page: Selected page identifier.
    """
    # Display messages (errors, success)
    display_messages()

    # Route to appropriate page
    if selected_page == PAGE_DASHBOARD:
        render_dashboard_page()
    elif selected_page == PAGE_ACCOUNTS:
        render_accounts_page()
    elif selected_page == PAGE_TRANSACTIONS:
        render_transactions_page()
    elif selected_page == PAGE_PORTFOLIO:
        render_portfolio_page()
    elif selected_page == PAGE_ANALYTICS:
        render_analytics_page()
    elif selected_page == PAGE_SETTINGS:
        render_settings_page()
    else:
        st.error(f"Unknown page: {selected_page}")


def render_dashboard_page() -> None:
    """Render dashboard page (placeholder)."""
    st.title("📊 Dashboard")
    st.info("🚧 Dashboard page coming soon!")


# render_accounts_page is imported from finarius_app.ui.accounts


# render_transactions_page is imported from finarius_app.ui.transactions


def render_portfolio_page() -> None:
    """Render portfolio page (placeholder)."""
    st.title("💼 Portfolio")
    st.info("🚧 Portfolio page coming soon!")


def render_analytics_page() -> None:
    """Render analytics page (placeholder)."""
    st.title("📈 Analytics")
    st.info("🚧 Analytics page coming soon!")


def render_settings_page() -> None:
    """Render settings page (placeholder)."""
    st.title("⚙️ Settings")
    st.info("🚧 Settings page coming soon!")


def main() -> None:
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()

    # Initialize database connection
    initialize_database()

    # Render sidebar navigation
    selected_page = render_sidebar()

    # Render page content
    render_page_content(selected_page)


if __name__ == "__main__":
    main()
