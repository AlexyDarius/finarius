"""Dashboard filters (account selector, date range)."""

from typing import Optional, Tuple
from datetime import date, timedelta
import streamlit as st

from finarius_app.core.models import Account, get_all_accounts


def render_filters(db) -> Tuple[Optional[int], date, date]:
    """Render dashboard filters.
    
    Args:
        db: Database instance.
    
    Returns:
        Tuple of (account_id, start_date, end_date).
        account_id is None if "All Accounts" is selected.
    """
    accounts = get_all_accounts(db)
    
    if not accounts:
        st.warning("⚠️ No accounts found. Please create an account first.")
        return None, date.today() - timedelta(days=30), date.today()
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Account selector
        if len(accounts) == 1:
            account_id = accounts[0].id
            st.info(f"📊 Viewing: {accounts[0].name}")
        else:
            account_options = ["All Accounts"] + [f"{acc.name} (ID: {acc.id})" for acc in accounts]
            selected_account = st.selectbox("Account", account_options)
            account_id = None
            if selected_account != "All Accounts":
                account_id = int(selected_account.split("(ID: ")[1].split(")")[0])
    
    with col2:
        # Date range selector
        date_range = st.date_input(
            "Date Range",
            value=(date.today() - timedelta(days=30), date.today()),
            max_value=date.today()
        )
        if isinstance(date_range, tuple):
            start_date = date_range[0]
            end_date = date_range[1]
        else:
            start_date = date_range
            end_date = date.today()
    
    with col3:
        st.write("")  # Spacer
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    return account_id, start_date, end_date

