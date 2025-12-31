"""Navigation and sidebar menu for Finarius Streamlit app."""

from typing import Optional
import streamlit as st


# Page identifiers
PAGE_DASHBOARD = "dashboard"
PAGE_ACCOUNTS = "accounts"
PAGE_TRANSACTIONS = "transactions"
PAGE_PORTFOLIO = "portfolio"
PAGE_ANALYTICS = "analytics"
PAGE_SETTINGS = "settings"

# Page configuration
PAGES = {
    PAGE_DASHBOARD: {
        "title": "Dashboard",
        "icon": "📊",
        "description": "Portfolio overview and key metrics",
    },
    PAGE_ACCOUNTS: {
        "title": "Accounts",
        "icon": "🏦",
        "description": "Manage investment accounts",
    },
    PAGE_TRANSACTIONS: {
        "title": "Transactions",
        "icon": "💸",
        "description": "View and manage transactions",
    },
    PAGE_PORTFOLIO: {
        "title": "Portfolio",
        "icon": "💼",
        "description": "Portfolio positions and holdings",
    },
    PAGE_ANALYTICS: {
        "title": "Analytics",
        "icon": "📈",
        "description": "Performance analytics and insights",
    },
    PAGE_SETTINGS: {
        "title": "Settings",
        "icon": "⚙️",
        "description": "Application settings and configuration",
    },
}


def render_sidebar() -> str:
    """Render sidebar navigation menu and return selected page.

    Returns:
        Selected page identifier.
    """
    st.sidebar.title("📊 Finarius")
    st.sidebar.markdown("---")

    # Initialize selected page in session state if not present
    if "selected_page" not in st.session_state:
        st.session_state.selected_page = PAGE_DASHBOARD

    # Render navigation menu
    selected_page = st.sidebar.radio(
        "Navigation",
        options=list(PAGES.keys()),
        format_func=lambda key: f"{PAGES[key]['icon']} {PAGES[key]['title']}",
        index=list(PAGES.keys()).index(st.session_state.selected_page),
    )

    # Update session state
    st.session_state.selected_page = selected_page

    # Show page description
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**{PAGES[selected_page]['description']}**")

    return selected_page


def get_page_title(page: str) -> str:
    """Get page title.

    Args:
        page: Page identifier.

    Returns:
        Page title.
    """
    return PAGES.get(page, {}).get("title", "Finarius")


def get_page_icon(page: str) -> str:
    """Get page icon.

    Args:
        page: Page identifier.

    Returns:
        Page icon.
    """
    return PAGES.get(page, {}).get("icon", "📊")

