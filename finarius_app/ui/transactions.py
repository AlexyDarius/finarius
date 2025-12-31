"""Transactions management UI for Finarius Streamlit app."""

from typing import Optional, List
from datetime import date, datetime, timedelta
import streamlit as st
import pandas as pd
import io

from finarius_app.core.models import (
    Transaction,
    get_all_accounts,
    get_transaction_by_id,
    get_transactions_by_account,
    get_transactions_by_symbol,
    get_latest_price,
)
from finarius_app.core.prices.downloader import PriceDownloader
from finarius_app.ui.session_state import get_db, set_error_message, set_success_message
from finarius_app.ui.error_handler import error_handler


# Transaction types
TRANSACTION_TYPES = ["BUY", "SELL", "DIVIDEND", "DEPOSIT", "WITHDRAW"]


@error_handler
def render_transactions_page() -> None:
    """Render transactions management page."""
    st.title("💸 Transactions")
    
    db = get_db()
    if db is None:
        st.error("Database not initialized")
        return
    
    # Get all accounts for filtering
    accounts = get_all_accounts(db)
    
    if not accounts:
        st.warning("⚠️ No accounts found. Please create an account first.")
        st.info("Go to the **Accounts** page to create your first account.")
        return
    
    # Filtering section
    filters = _render_filters(accounts, db)
    
    st.markdown("---")
    
    # Get filtered transactions
    transactions = _get_filtered_transactions(filters, db)
    
    # Display transactions table
    _render_transactions_table(transactions, accounts, db)
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Add Transaction", use_container_width=True):
            st.session_state.show_transaction_form = True
            st.session_state.editing_transaction_id = None
            st.rerun()
    
    with col2:
        if st.button("📥 Import CSV", use_container_width=True):
            st.session_state.show_csv_import = True
            st.rerun()
    
    with col3:
        if transactions:
            csv_data = _generate_csv(transactions)
            st.download_button(
                "📤 Export CSV",
                data=csv_data,
                file_name=f"transactions_{date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # Transaction form (create/edit)
    if st.session_state.get("show_transaction_form", False):
        st.markdown("---")
        _render_transaction_form(accounts, db)
    
    # CSV import form
    if st.session_state.get("show_csv_import", False):
        st.markdown("---")
        _render_csv_import_form(accounts, db)


def _render_filters(accounts: List, db) -> dict:
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
        # Date range filter
        date_range = st.date_input(
            "Date Range",
            value=(date.today() - timedelta(days=30), date.today()),
            max_value=date.today()
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


def _get_filtered_transactions(filters: dict, db) -> List[Transaction]:
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
        from finarius_app.core.models import get_all_accounts
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


def _render_transactions_table(transactions: List[Transaction], accounts: List, db) -> None:
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
                    _render_edit_transaction_form(transaction, accounts, db)
                
                with col2:
                    _render_delete_transaction_form(transaction, db)


def _render_transaction_form(accounts: List, db, transaction: Optional[Transaction] = None) -> None:
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


def _render_edit_transaction_form(transaction: Transaction, accounts: List, db) -> None:
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
        _render_transaction_form(accounts, db, transaction)


def _render_delete_transaction_form(transaction: Transaction, db) -> None:
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


def _generate_csv(transactions: List[Transaction]) -> str:
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


def _render_csv_import_form(accounts: List, db) -> None:
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
                _import_transactions_from_dataframe(df, accounts, db)
        except Exception as e:
            set_error_message(f"Error reading CSV file: {str(e)}")
    
    if st.button("❌ Cancel Import"):
        st.session_state.show_csv_import = False
        st.rerun()


def _import_transactions_from_dataframe(df: pd.DataFrame, accounts: List, db) -> None:
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

