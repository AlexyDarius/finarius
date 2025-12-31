"""Accounts management UI for Finarius Streamlit app."""

from typing import Optional
from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.models import Account, get_all_accounts, get_account_by_id
from finarius_app.core.engine import calculate_portfolio_value
from finarius_app.ui.session_state import get_db, set_error_message, set_success_message
from finarius_app.ui.error_handler import error_handler


# Supported currencies
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY"]


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
    _render_account_statistics(accounts, db)
    
    st.markdown("---")
    
    # Add account form
    _render_add_account_form(db)
    
    st.markdown("---")
    
    # Display accounts table with actions
    _render_accounts_table(accounts, db)


def _render_account_statistics(accounts: list[Account], db) -> None:
    """Render account statistics section.
    
    Args:
        accounts: List of Account instances.
        db: Database instance.
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Accounts", len(accounts))
    
    with col2:
        currencies = len(set(acc.currency for acc in accounts)) if accounts else 0
        st.metric("Currencies", currencies)
    
    with col3:
        # Calculate total portfolio value across all accounts
        total_value = 0.0
        today = date.today()
        for account in accounts:
            try:
                value = calculate_portfolio_value(account.id, today, db)
                total_value += value
            except Exception:
                # If calculation fails, skip this account
                pass
        st.metric("Total Portfolio Value", f"${total_value:,.2f}" if total_value > 0 else "$0.00")
    
    with col4:
        st.metric("Status", "✅ Active" if accounts else "⚠️ No accounts")
    
    # Account breakdown chart (if accounts exist)
    if accounts:
        st.markdown("---")
        _render_account_breakdown_chart(accounts, db)


def _render_account_breakdown_chart(accounts: list[Account], db) -> None:
    """Render account breakdown pie chart.
    
    Args:
        accounts: List of Account instances.
        db: Database instance.
    """
    try:
        import plotly.express as px
        
        today = date.today()
        account_values = []
        account_names = []
        
        for account in accounts:
            try:
                value = calculate_portfolio_value(account.id, today, db)
                if value > 0:
                    account_values.append(value)
                    account_names.append(account.name)
            except Exception:
                # Skip accounts with calculation errors
                pass
        
        if account_values:
            st.subheader("Portfolio Value by Account")
            df = pd.DataFrame({
                "Account": account_names,
                "Value": account_values
            })
            
            fig = px.pie(
                df,
                values="Value",
                names="Account",
                title="Account Value Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        # Plotly not available, skip chart
        pass
    except Exception:
        # Chart rendering failed, skip
        pass


def _render_add_account_form(db) -> None:
    """Render add account form.
    
    Args:
        db: Database instance.
    """
    with st.expander("➕ Add New Account", expanded=False):
        with st.form("add_account_form", clear_on_submit=True):
            account_name = st.text_input(
                "Account Name",
                placeholder="e.g., My Investment Account",
                help="Enter a unique account name"
            )
            currency = st.selectbox(
                "Currency",
                options=CURRENCIES,
                index=0,
                help="Select the account currency"
            )
            submit = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit:
                if not account_name or not account_name.strip():
                    set_error_message("Account name is required")
                    st.rerun()
                
                account_name = account_name.strip()
                
                # Check if account already exists
                existing = get_all_accounts(db)
                if any(acc.name.lower() == account_name.lower() for acc in existing):
                    set_error_message(f"Account '{account_name}' already exists")
                    st.rerun()
                
                try:
                    account = Account(name=account_name, currency=currency)
                    account.save(db)
                    set_success_message(f"Account '{account_name}' created successfully!")
                    st.rerun()
                except Exception as e:
                    set_error_message(f"Error creating account: {str(e)}")
                    st.rerun()


def _render_accounts_table(accounts: list[Account], db) -> None:
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
                _render_edit_account_form(account, db)
            
            with col2:
                _render_delete_account_form(account, db)


def _render_edit_account_form(account: Account, db) -> None:
    """Render edit account form.
    
    Args:
        account: Account instance to edit.
        db: Database instance.
    """
    st.markdown("### ✏️ Edit Account")
    
    with st.form(f"edit_account_form_{account.id}"):
        new_name = st.text_input(
            "Account Name",
            value=account.name,
            key=f"edit_name_{account.id}"
        )
        new_currency = st.selectbox(
            "Currency",
            options=CURRENCIES,
            index=CURRENCIES.index(account.currency) if account.currency in CURRENCIES else 0,
            key=f"edit_currency_{account.id}"
        )
        submit = st.form_submit_button("Update Account", use_container_width=True)
        
        if submit:
            if not new_name or not new_name.strip():
                set_error_message("Account name is required")
                st.rerun()
            
            new_name = new_name.strip()
            
            # Check if name changed and conflicts with existing account
            if new_name.lower() != account.name.lower():
                existing = get_all_accounts(db)
                if any(acc.id != account.id and acc.name.lower() == new_name.lower() for acc in existing):
                    set_error_message(f"Account name '{new_name}' already exists")
                    st.rerun()
            
            try:
                account.name = new_name
                account.currency = new_currency
                account.save(db)
                set_success_message(f"Account '{new_name}' updated successfully!")
                st.rerun()
            except Exception as e:
                set_error_message(f"Error updating account: {str(e)}")
                st.rerun()


def _render_delete_account_form(account: Account, db) -> None:
    """Render delete account form with confirmation.
    
    Args:
        account: Account instance to delete.
        db: Database instance.
    """
    st.markdown("### 🗑️ Delete Account")
    
    st.warning(f"⚠️ Deleting account '{account.name}' will permanently remove it and all associated data.")
    
    # Check if account has transactions
    from finarius_app.core.models import get_transactions_by_account
    transactions = get_transactions_by_account(account.id, None, None, db)
    has_transactions = len(transactions) > 0
    
    if has_transactions:
        st.error(f"⚠️ This account has {len(transactions)} transaction(s). Deleting it will also delete all transactions.")
    
    with st.form(f"delete_account_form_{account.id}"):
        confirm_name = st.text_input(
            f"Type '{account.name}' to confirm deletion",
            key=f"delete_confirm_{account.id}",
            help="Enter the account name exactly to confirm deletion"
        )
        submit = st.form_submit_button(
            "🗑️ Delete Account",
            use_container_width=True,
            type="primary"
        )
        
        if submit:
            if confirm_name != account.name:
                set_error_message(f"Confirmation name does not match. Please type '{account.name}' exactly.")
                st.rerun()
            
            try:
                account_name = account.name
                account.delete(db)
                set_success_message(f"Account '{account_name}' deleted successfully!")
                st.rerun()
            except Exception as e:
                set_error_message(f"Error deleting account: {str(e)}")
                st.rerun()

