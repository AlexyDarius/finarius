"""Account forms (add/edit/delete) for accounts UI."""

from datetime import date
import streamlit as st

from finarius_app.core.models import Account, get_all_accounts
from finarius_app.ui.session_state import set_error_message, set_success_message
from .constants import CURRENCIES


def render_add_account_form(db) -> None:
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
                    from finarius_app.core.models import Account
                    account = Account(name=account_name, currency=currency)
                    account.save(db)
                    set_success_message(f"Account '{account_name}' created successfully!")
                    st.rerun()
                except Exception as e:
                    set_error_message(f"Error creating account: {str(e)}")
                    st.rerun()


def render_edit_account_form(account: Account, db) -> None:
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


def render_delete_account_form(account: Account, db) -> None:
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

