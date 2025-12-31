"""Main settings page rendering."""

import streamlit as st

from finarius_app.ui.session_state import get_db
from finarius_app.ui.error_handler import error_handler
from .database import render_database_settings
from .prices import render_price_settings
from .display import render_display_settings
from .export_import import render_export_import_settings


@error_handler
def render_settings_page() -> None:
    """Render settings page."""
    st.title("⚙️ Settings")
    
    db = get_db()
    if db is None:
        st.error("Database not initialized")
        return
    
    # Database settings
    render_database_settings(db)
    
    st.markdown("---")
    
    # Price update settings
    render_price_settings(db)
    
    st.markdown("---")
    
    # Display settings
    render_display_settings()
    
    st.markdown("---")
    
    # Export/Import settings
    render_export_import_settings(db)

