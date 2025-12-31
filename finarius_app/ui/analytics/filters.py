"""Analytics filters (account selector, date range)."""

from typing import Optional, Tuple
from datetime import date, timedelta
import streamlit as st

from finarius_app.core.models import get_all_accounts


def render_filters(db) -> Tuple[Optional[int], date, date]:
    """Render analytics filters.
    
    Args:
        db: Database instance.
    
    Returns:
        Tuple of (account_id, start_date, end_date).
        account_id is None if "All Accounts" is selected.
    """
    accounts = get_all_accounts(db)
    
    if not accounts:
        st.warning("⚠️ No accounts found. Please create an account first.")
        return None, date.today() - timedelta(days=365), date.today()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Account selector
        if len(accounts) == 1:
            account_id = accounts[0].id
            st.info(f"📊 Analyzing: {accounts[0].name}")
        else:
            account_options = ["All Accounts"] + [f"{acc.name} (ID: {acc.id})" for acc in accounts]
            selected_account = st.selectbox("Account", account_options)
            account_id = None
            if selected_account != "All Accounts":
                account_id = int(selected_account.split("(ID: ")[1].split(")")[0])
    
    with col2:
        # Quick date range selector
        date_preset_key = "analytics_date_preset"
        if date_preset_key not in st.session_state:
            st.session_state[date_preset_key] = "Custom"
        
        date_preset = st.selectbox(
            "Date Range",
            options=["Custom", "YTD", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year"],
            key=date_preset_key
        )
        
        # Calculate date range based on preset
        today = date.today()
        if date_preset == "YTD":
            start_date = date(today.year, 1, 1)
            end_date = today
        elif date_preset == "Last 7 Days":
            start_date = today - timedelta(days=7)
            end_date = today
        elif date_preset == "Last 30 Days":
            start_date = today - timedelta(days=30)
            end_date = today
        elif date_preset == "Last 90 Days":
            start_date = today - timedelta(days=90)
            end_date = today
        elif date_preset == "Last Year":
            start_date = today - timedelta(days=365)
            end_date = today
        else:  # Custom
            # Date range selector
            date_range = st.date_input(
                "Custom Date Range",
                value=(date.today() - timedelta(days=365), date.today()),
                max_value=date.today(),
                key="analytics_custom_date_range"
            )
            if isinstance(date_range, tuple):
                start_date = date_range[0]
                end_date = date_range[1]
            else:
                start_date = date_range
                end_date = date.today()
    
    return account_id, start_date, end_date

