"""Display settings section for settings page."""

import streamlit as st

from finarius_app.ui.session_state import get_session_value, set_session_value


# Display settings constants
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY"]
DATE_FORMATS = ["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "DD-MM-YYYY"]
NUMBER_FORMATS = ["Standard (1,234.56)", "European (1.234,56)", "Compact (1.23K)"]


def render_display_settings() -> None:
    """Render display settings section.
    
    Note: These settings are stored in session state for now.
    In a full implementation, they would be persisted to a config file.
    """
    st.subheader("🎨 Display Settings")
    
    # Default currency
    st.markdown("#### Default Currency")
    current_currency = get_session_value("default_currency", "USD")
    selected_currency = st.selectbox(
        "Default Currency",
        options=CURRENCIES,
        index=CURRENCIES.index(current_currency) if current_currency in CURRENCIES else 0,
        help="Default currency for displaying values"
    )
    if selected_currency != current_currency:
        set_session_value("default_currency", selected_currency)
        st.info(f"Default currency set to {selected_currency}")
    
    # Date format
    st.markdown("#### Date Format")
    current_date_format = get_session_value("date_format", "YYYY-MM-DD")
    selected_date_format = st.selectbox(
        "Date Format",
        options=DATE_FORMATS,
        index=DATE_FORMATS.index(current_date_format) if current_date_format in DATE_FORMATS else 0,
        help="Format for displaying dates"
    )
    if selected_date_format != current_date_format:
        set_session_value("date_format", selected_date_format)
        st.info(f"Date format set to {selected_date_format}")
    
    # Number format
    st.markdown("#### Number Format")
    current_number_format = get_session_value("number_format", "Standard (1,234.56)")
    selected_number_format = st.selectbox(
        "Number Format",
        options=NUMBER_FORMATS,
        index=NUMBER_FORMATS.index(current_number_format) if current_number_format in NUMBER_FORMATS else 0,
        help="Format for displaying numbers"
    )
    if selected_number_format != current_number_format:
        set_session_value("number_format", selected_number_format)
        st.info(f"Number format set to {selected_number_format}")
    
    st.info("💡 Note: Display settings are stored in session. To persist across sessions, configuration file support is needed.")

