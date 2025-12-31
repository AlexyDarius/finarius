"""CSV import/export for transactions UI."""

from typing import List
from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.models import Transaction, Account
from finarius_app.ui.session_state import set_error_message, set_success_message
from .constants import TRANSACTION_TYPES


def generate_csv(transactions: List[Transaction]) -> str:
    """Generate CSV data from transactions.
    
    Args:
        transactions: List of Transaction instances.
    
    Returns:
        CSV string.
    """
    data = []
    for txn in transactions:
        data.append({
            "ID": txn.id,
            "Date": txn.date.isoformat() if isinstance(txn.date, date) else str(txn.date),
            "Account ID": txn.account_id,
            "Type": txn.type,
            "Symbol": txn.symbol or "",
            "Quantity": txn.qty or "",
            "Price": txn.price or "",
            "Fee": txn.fee or 0.0,
            "Notes": txn.notes or "",
        })
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False)


def render_csv_import_form(accounts: List[Account], db) -> None:
    """Render CSV import form.
    
    Args:
        accounts: List of Account instances.
        db: Database instance.
    """
    st.subheader("📥 Import Transactions from CSV")
    
    st.info("""
    **CSV Format:**
    - Required columns: Date, Account ID, Type, Symbol (for BUY/SELL/DIVIDEND), Quantity (for BUY/SELL), Price (for BUY/SELL)
    - Optional columns: Fee, Notes
    - Date format: YYYY-MM-DD
    - Type: BUY, SELL, DIVIDEND, DEPOSIT, or WITHDRAW
    """)
    
    uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            # Validate columns
            required_columns = ["Date", "Account ID", "Type"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                set_error_message(f"Missing required columns: {', '.join(missing_columns)}")
                st.rerun()
            
            # Preview
            st.subheader("Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            if st.button("📥 Import Transactions", type="primary"):
                import_transactions_from_dataframe(df, accounts, db)
        except Exception as e:
            set_error_message(f"Error reading CSV file: {str(e)}")
    
    if st.button("❌ Cancel Import"):
        st.session_state.show_csv_import = False
        st.rerun()


def import_transactions_from_dataframe(df: pd.DataFrame, accounts: List[Account], db) -> None:
    """Import transactions from DataFrame.
    
    Args:
        df: DataFrame with transaction data.
        accounts: List of Account instances.
        db: Database instance.
    """
    account_ids = {acc.id for acc in accounts}
    imported = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Parse date
            txn_date = pd.to_datetime(row["Date"]).date()
            
            # Get account ID
            account_id = int(row["Account ID"])
            if account_id not in account_ids:
                errors.append(f"Row {idx + 1}: Invalid account ID {account_id}")
                continue
            
            # Get transaction type
            transaction_type = str(row["Type"]).upper()
            if transaction_type not in TRANSACTION_TYPES:
                errors.append(f"Row {idx + 1}: Invalid transaction type {transaction_type}")
                continue
            
            # Get symbol (required for BUY, SELL, DIVIDEND)
            requires_symbol = transaction_type in ["BUY", "SELL", "DIVIDEND"]
            symbol = str(row.get("Symbol", "")).strip().upper() if requires_symbol else None
            if requires_symbol and not symbol:
                errors.append(f"Row {idx + 1}: Symbol required for {transaction_type}")
                continue
            
            # Get quantity (required for BUY, SELL)
            requires_qty = transaction_type in ["BUY", "SELL"]
            qty = float(row.get("Quantity", 0)) if requires_qty else None
            if requires_qty and (pd.isna(qty) or qty <= 0):
                errors.append(f"Row {idx + 1}: Valid quantity required for {transaction_type}")
                continue
            
            # Get price (required for BUY, SELL)
            requires_price = transaction_type in ["BUY", "SELL"]
            price = float(row.get("Price", 0)) if requires_price else None
            if requires_price and (pd.isna(price) or price <= 0):
                errors.append(f"Row {idx + 1}: Valid price required for {transaction_type}")
                continue
            
            # Get fee
            fee = float(row.get("Fee", 0)) if pd.notna(row.get("Fee")) else 0.0
            
            # Get notes
            notes = str(row.get("Notes", "")).strip() if pd.notna(row.get("Notes")) else None
            
            # Create transaction
            from finarius_app.core.models import Transaction
            transaction = Transaction(
                date=txn_date,
                account_id=account_id,
                transaction_type=transaction_type,
                symbol=symbol,
                qty=qty,
                price=price,
                fee=fee,
                notes=notes,
            )
            transaction.save(db)
            imported += 1
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
    
    if errors:
        error_msg = f"Imported {imported} transactions. Errors:\n" + "\n".join(errors[:10])
        if len(errors) > 10:
            error_msg += f"\n... and {len(errors) - 10} more errors"
        set_error_message(error_msg)
    else:
        set_success_message(f"Successfully imported {imported} transactions!")
    
    st.session_state.show_csv_import = False
    st.rerun()

