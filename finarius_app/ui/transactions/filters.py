"""Transaction filtering for transactions UI."""

from typing import List, Dict, Optional
from datetime import date, timedelta
import streamlit as st

from finarius_app.core.models import Account, Transaction, get_all_accounts, get_transactions_by_account
from .constants import TRANSACTION_TYPES


def render_filters(accounts: List[Account], db) -> dict:
    """Render filtering options.
    
    Args:
        accounts: List of Account instances.
        db: Database instance.
    
    Returns:
        Dictionary with filter values.
    """
    st.subheader("🔍 Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Account filter
        account_options = ["All Accounts"] + [f"{acc.name} (ID: {acc.id})" for acc in accounts]
        selected_account = st.selectbox("Account", account_options)
        account_id = None
        if selected_account != "All Accounts":
            account_id = int(selected_account.split("(ID: ")[1].split(")")[0])
    
    with col2:
        # Quick date range selector
        date_preset_key = "transaction_date_preset"
        if date_preset_key not in st.session_state:
            st.session_state[date_preset_key] = "Last Year"
        
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
            # Date range filter - default to wider range (1 year) to show more transactions
            # This ensures transactions from earlier dates are visible by default
            default_start_date = date.today() - timedelta(days=365)
            default_end_date = date.today()
            
            # Use session state to remember user's date range preference
            # Initialize default value only if not already set by widget
            date_range_key = "transaction_date_range"
            default_value = (default_start_date, default_end_date)
            
            # Get the value from session_state if it exists, otherwise use default
            # The widget will manage its own state after first creation
            if date_range_key in st.session_state:
                # Widget already exists, use its value
                date_range = st.date_input(
                    "Custom Date Range",
                    value=st.session_state[date_range_key],
                    max_value=date.today(),
                    key=date_range_key
                )
            else:
                # First time, set default value
                date_range = st.date_input(
                    "Custom Date Range",
                    value=default_value,
                    max_value=date.today(),
                    key=date_range_key
                )
            
            start_date = date_range[0] if isinstance(date_range, tuple) else date_range
            end_date = date_range[1] if isinstance(date_range, tuple) else date.today()
    
    with col3:
        # Symbol filter
        symbol_filter = st.text_input("Symbol", placeholder="e.g., AAPL", value="").strip().upper()
        symbol = symbol_filter if symbol_filter else None
    
    with col4:
        # Type filter
        type_options = ["All Types"] + TRANSACTION_TYPES
        selected_type = st.selectbox("Type", type_options)
        transaction_type = None if selected_type == "All Types" else selected_type
    
    return {
        "account_id": account_id,
        "start_date": start_date,
        "end_date": end_date,
        "symbol": symbol,
        "type": transaction_type,
    }


def get_filtered_transactions(filters: dict, db) -> List[Transaction]:
    """Get filtered transactions based on filters.
    
    Args:
        filters: Dictionary with filter values.
        db: Database instance.
    
    Returns:
        List of Transaction instances.
    """
    # Start with all transactions or account-specific
    if filters["account_id"]:
        transactions = get_transactions_by_account(
            filters["account_id"],
            filters["start_date"],
            filters["end_date"],
            db
        )
    else:
        # Get transactions from all accounts
        accounts = get_all_accounts(db)
        transactions = []
        for account in accounts:
            account_transactions = get_transactions_by_account(
                account.id,
                filters["start_date"],
                filters["end_date"],
                db
            )
            transactions.extend(account_transactions)
        # Sort by date descending
        transactions.sort(key=lambda t: t.date, reverse=True)
    
    # Apply symbol filter
    if filters["symbol"]:
        transactions = [t for t in transactions if t.symbol and t.symbol.upper() == filters["symbol"]]
    
    # Apply type filter
    if filters["type"]:
        transactions = [t for t in transactions if t.type == filters["type"]]
    
    return transactions

