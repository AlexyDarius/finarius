"""Transaction forms (create/edit/delete) for transactions UI."""

from typing import List, Optional
from datetime import date
import streamlit as st

from finarius_app.core.models import Transaction, Account, get_latest_price
from finarius_app.ui.session_state import set_error_message, set_success_message
from .constants import TRANSACTION_TYPES


def render_transaction_form(accounts: List[Account], db, transaction: Optional[Transaction] = None) -> None:
    """Render transaction form for create/edit.
    
    Args:
        accounts: List of Account instances.
        db: Database instance.
        transaction: Transaction instance for editing, None for creating.
    """
    is_edit = transaction is not None
    
    st.subheader("✏️ Edit Transaction" if is_edit else "➕ Add Transaction")
    
    with st.form(f"transaction_form_{transaction.id if transaction else 'new'}"):
        # Account selector
        account_options = {f"{acc.name} (ID: {acc.id})": acc.id for acc in accounts}
        default_account = transaction.account_id if transaction else list(account_options.values())[0]
        selected_account_label = st.selectbox(
            "Account *",
            options=list(account_options.keys()),
            index=list(account_options.values()).index(default_account) if default_account in account_options.values() else 0
        )
        account_id = account_options[selected_account_label]
        
        # Date picker
        default_date = transaction.date if transaction else date.today()
        txn_date = st.date_input("Date *", value=default_date, max_value=date.today())
        
        # Type selector
        default_type_index = TRANSACTION_TYPES.index(transaction.type) if transaction and transaction.type in TRANSACTION_TYPES else 0
        transaction_type = st.selectbox("Type *", options=TRANSACTION_TYPES, index=default_type_index)
        
        # Symbol input (required for BUY, SELL, DIVIDEND)
        requires_symbol = transaction_type in ["BUY", "SELL", "DIVIDEND"]
        symbol = st.text_input(
            "Symbol" + (" *" if requires_symbol else ""),
            value=transaction.symbol if transaction else "",
            placeholder="e.g., AAPL",
            help="Required for BUY, SELL, and DIVIDEND transactions"
        ).strip().upper()
        
        # Show current price if symbol entered
        current_price = None
        if symbol and requires_symbol:
            try:
                price_obj = get_latest_price(symbol, db)
                if price_obj:
                    current_price = price_obj.close
                    st.info(f"💡 Current price for {symbol}: ${current_price:,.2f}")
            except Exception:
                pass
        
        # Quantity (required for BUY, SELL)
        requires_qty = transaction_type in ["BUY", "SELL"]
        qty = st.number_input(
            "Quantity" + (" *" if requires_qty else ""),
            min_value=0.0,
            value=float(transaction.qty) if transaction and transaction.qty else 0.0,
            step=0.01,
            help="Required for BUY and SELL transactions"
        )
        
        # Price (required for BUY, SELL)
        requires_price = transaction_type in ["BUY", "SELL"]
        price = st.number_input(
            "Price per Unit" + (" *" if requires_price else ""),
            min_value=0.0,
            value=float(transaction.price) if transaction and transaction.price else (current_price or 0.0),
            step=0.01,
            format="%.2f",
            help="Required for BUY and SELL transactions"
        )
        
        # Fee
        fee = st.number_input(
            "Fee",
            min_value=0.0,
            value=float(transaction.fee) if transaction and transaction.fee else 0.0,
            step=0.01,
            format="%.2f"
        )
        
        # Notes
        notes = st.text_area(
            "Notes",
            value=transaction.notes if transaction else "",
            placeholder="Optional notes about this transaction"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Save Transaction", use_container_width=True, type="primary")
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if cancel:
            st.session_state.show_transaction_form = False
            st.session_state.editing_transaction_id = None
            st.rerun()
        
        if submit:
            # Validation
            if requires_symbol and not symbol:
                set_error_message("Symbol is required for this transaction type")
                st.rerun()
            
            if requires_qty and qty <= 0:
                set_error_message("Quantity must be greater than 0 for this transaction type")
                st.rerun()
            
            if requires_price and price <= 0:
                set_error_message("Price must be greater than 0 for this transaction type")
                st.rerun()
            
            try:
                if is_edit:
                    # Update existing transaction
                    transaction.date = txn_date
                    transaction.account_id = account_id
                    transaction.type = transaction_type
                    transaction.symbol = symbol if requires_symbol else None
                    transaction.qty = qty if requires_qty else None
                    transaction.price = price if requires_price else None
                    transaction.fee = fee
                    transaction.notes = notes.strip() if notes else None
                    transaction.save(db)
                    set_success_message(f"Transaction updated successfully!")
                else:
                    # Create new transaction
                    new_transaction = Transaction(
                        date=txn_date,
                        account_id=account_id,
                        transaction_type=transaction_type,
                        symbol=symbol if requires_symbol else None,
                        qty=qty if requires_qty else None,
                        price=price if requires_price else None,
                        fee=fee,
                        notes=notes.strip() if notes else None,
                    )
                    new_transaction.save(db)
                    set_success_message(f"Transaction created successfully!")
                
                st.session_state.show_transaction_form = False
                st.session_state.editing_transaction_id = None
                st.rerun()
            except Exception as e:
                set_error_message(f"Error saving transaction: {str(e)}")
                st.rerun()


def render_edit_transaction_form(transaction: Transaction, accounts: List[Account], db) -> None:
    """Render edit transaction form.
    
    Args:
        transaction: Transaction instance to edit.
        accounts: List of Account instances.
        db: Database instance.
    """
    if st.button("✏️ Edit Transaction", use_container_width=True, key=f"edit_{transaction.id}"):
        st.session_state.show_transaction_form = True
        st.session_state.editing_transaction_id = transaction.id
        st.rerun()
    
    # Re-render form if editing this transaction
    if st.session_state.get("editing_transaction_id") == transaction.id:
        render_transaction_form(accounts, db, transaction)


def render_delete_transaction_form(transaction: Transaction, db) -> None:
    """Render delete transaction form with confirmation.
    
    Args:
        transaction: Transaction instance to delete.
        db: Database instance.
    """
    st.markdown("### 🗑️ Delete Transaction")
    
    st.warning(f"⚠️ Deleting this transaction will permanently remove it from the database.")
    
    with st.form(f"delete_transaction_form_{transaction.id}"):
        confirm_text = st.text_input(
            f"Type 'DELETE' to confirm",
            key=f"delete_confirm_{transaction.id}",
            help="Enter 'DELETE' exactly to confirm deletion"
        )
        submit = st.form_submit_button(
            "🗑️ Delete Transaction",
            use_container_width=True,
            type="primary"
        )
        
        if submit:
            if confirm_text != "DELETE":
                set_error_message("Please type 'DELETE' exactly to confirm deletion")
                st.rerun()
            
            try:
                transaction_id = transaction.id
                transaction.delete(db)
                set_success_message(f"Transaction deleted successfully!")
                st.rerun()
            except Exception as e:
                set_error_message(f"Error deleting transaction: {str(e)}")
                st.rerun()

