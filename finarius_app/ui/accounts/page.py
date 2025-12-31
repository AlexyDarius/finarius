"""Main accounts page rendering."""

import streamlit as st

from finarius_app.core.models import get_all_accounts
from finarius_app.ui.session_state import get_db
from finarius_app.ui.error_handler import error_handler
from .statistics import render_account_statistics
from .forms import render_add_account_form
from .table import render_accounts_table


@error_handler
def render_accounts_page() -> None:
    """Render accounts management page."""
    st.title("🏦 Accounts")
    
    db = get_db()
    if db is None:
        st.error("Database not initialized")
        return
    
    # Get all accounts
    accounts = get_all_accounts(db)
    
    # Display account statistics
    render_account_statistics(accounts, db)
    
    st.markdown("---")
    
    # Add account form
    render_add_account_form(db)
    
    st.markdown("---")
    
    # Display accounts table with actions
    render_accounts_table(accounts, db)

