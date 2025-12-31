"""Recent transactions table for dashboard."""

from typing import Optional
from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.models import get_transactions_by_account, get_all_accounts


def render_recent_transactions(
    account_id: Optional[int],
    db,
    limit: int = 10,
) -> None:
    """Render recent transactions table.
    
    Args:
        account_id: Account ID (None for all accounts).
        db: Database instance.
        limit: Maximum number of transactions to display.
    """
    st.subheader("💸 Recent Transactions")
    
    try:
        if account_id is None:
            # Get transactions from all accounts
            accounts = get_all_accounts(db)
            all_transactions = []
            for acc in accounts:
                transactions = get_transactions_by_account(acc.id, None, None, db)
                all_transactions.extend(transactions)
            # Sort by date descending
            all_transactions.sort(key=lambda t: t.date, reverse=True)
            transactions = all_transactions[:limit]
        else:
            transactions = get_transactions_by_account(account_id, None, None, db)
            transactions.sort(key=lambda t: t.date, reverse=True)
            transactions = transactions[:limit]
        
        if not transactions:
            st.info("No recent transactions")
            return
        
        # Prepare data for table
        transactions_data = []
        for txn in transactions:
            transactions_data.append({
                "Date": txn.date.strftime("%Y-%m-%d") if isinstance(txn.date, date) else str(txn.date),
                "Type": txn.type,
                "Symbol": txn.symbol or "-",
                "Quantity": f"{txn.qty:,.2f}" if txn.qty else "-",
                "Price": f"${txn.price:,.2f}" if txn.price else "-",
                "Fee": f"${txn.fee:,.2f}" if txn.fee else "$0.00",
                "Total": f"${(txn.qty * txn.price + txn.fee):,.2f}" if txn.qty and txn.price else f"${txn.fee:,.2f}" if txn.fee else "$0.00",
            })
        
        df = pd.DataFrame(transactions_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.warning(f"⚠️ Error loading transactions: {str(e)}")

