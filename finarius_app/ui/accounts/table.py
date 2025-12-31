"""Account table rendering for accounts UI."""

from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.models import Account, get_account_by_id
from finarius_app.core.engine import calculate_portfolio_value
from .forms import render_edit_account_form, render_delete_account_form


def render_accounts_table(accounts: list[Account], db) -> None:
    """Render accounts table with edit/delete actions.
    
    Args:
        accounts: List of Account instances.
        db: Database instance.
    """
    st.subheader("Account List")
    
    if not accounts:
        st.info("No accounts yet. Create your first account using the form above.")
        return
    
    # Create DataFrame for display
    accounts_data = []
    for acc in accounts:
        # Calculate portfolio value
        portfolio_value = 0.0
        try:
            portfolio_value = calculate_portfolio_value(acc.id, date.today(), db)
        except Exception:
            pass
        
        accounts_data.append({
            "ID": acc.id,
            "Name": acc.name,
            "Currency": acc.currency,
            "Portfolio Value": f"${portfolio_value:,.2f}" if portfolio_value > 0 else "$0.00",
            "Created": pd.to_datetime(acc.created_at).strftime("%Y-%m-%d") if acc.created_at else "N/A",
        })
    
    df = pd.DataFrame(accounts_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Edit/Delete actions
    st.markdown("---")
    st.subheader("Manage Accounts")
    
    # Account selector for edit/delete
    account_options = {f"{acc.name} (ID: {acc.id})": acc.id for acc in accounts}
    selected_account_label = st.selectbox(
        "Select Account",
        options=list(account_options.keys()),
        help="Select an account to edit or delete"
    )
    
    if selected_account_label:
        selected_account_id = account_options[selected_account_label]
        account = get_account_by_id(selected_account_id, db)
        
        if account:
            col1, col2 = st.columns(2)
            
            with col1:
                render_edit_account_form(account, db)
            
            with col2:
                render_delete_account_form(account, db)

