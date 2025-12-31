"""Transaction table rendering for transactions UI."""

from typing import List
from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.models import Transaction, Account, get_transaction_by_id
from .forms import render_edit_transaction_form, render_delete_transaction_form


def render_transactions_table(transactions: List[Transaction], accounts: List[Account], db) -> None:
    """Render transactions table.
    
    Args:
        transactions: List of Transaction instances.
        accounts: List of Account instances (for account name lookup).
        db: Database instance.
    """
    st.subheader(f"Transactions ({len(transactions)})")
    
    if not transactions:
        st.info("No transactions found matching the filters.")
        return
    
    # Create account lookup
    account_lookup = {acc.id: acc.name for acc in accounts}
    
    # Create DataFrame
    transactions_data = []
    for txn in transactions:
        account_name = account_lookup.get(txn.account_id, f"ID: {txn.account_id}")
        total = (txn.qty * txn.price + txn.fee) if txn.qty and txn.price else (txn.fee or 0.0)
        
        transactions_data.append({
            "ID": txn.id,
            "Date": txn.date.strftime("%Y-%m-%d") if isinstance(txn.date, date) else str(txn.date),
            "Account": account_name,
            "Type": txn.type,
            "Symbol": txn.symbol or "-",
            "Quantity": f"{txn.qty:,.2f}" if txn.qty else "-",
            "Price": f"${txn.price:,.2f}" if txn.price else "-",
            "Fee": f"${txn.fee:,.2f}" if txn.fee else "$0.00",
            "Total": f"${total:,.2f}",
            "Notes": txn.notes or "-",
        })
    
    df = pd.DataFrame(transactions_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Edit/Delete actions
    st.markdown("---")
    st.subheader("Manage Transaction")
    
    transaction_options = {
        f"ID {txn.id}: {txn.type} {txn.symbol or ''} on {txn.date}": txn.id
        for txn in transactions[:50]  # Limit to first 50 for performance
    }
    
    if transaction_options:
        selected_transaction_label = st.selectbox(
            "Select Transaction",
            options=list(transaction_options.keys()),
            help="Select a transaction to edit or delete"
        )
        
        if selected_transaction_label:
            selected_transaction_id = transaction_options[selected_transaction_label]
            transaction = get_transaction_by_id(selected_transaction_id, db)
            
            if transaction:
                col1, col2 = st.columns(2)
                
                with col1:
                    render_edit_transaction_form(transaction, accounts, db)
                
                with col2:
                    render_delete_transaction_form(transaction, db)

