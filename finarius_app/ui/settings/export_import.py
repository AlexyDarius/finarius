"""Export/Import settings section for settings page."""

import streamlit as st
import pandas as pd
import io
from datetime import date

from finarius_app.core.models import get_all_accounts, get_transactions_by_account
from finarius_app.ui.session_state import get_db, set_success_message, set_error_message


def render_export_import_settings(db) -> None:
    """Render export/import settings section.
    
    Args:
        db: Database instance.
    """
    st.subheader("📤 Export/Import Settings")
    
    accounts = get_all_accounts(db)
    if not accounts:
        st.info("No accounts available. Create an account first.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Export Data")
        st.info("Export all your data to CSV files for backup or analysis.")
        
        # Export accounts
        if st.button("📥 Export Accounts", use_container_width=True):
            try:
                accounts_data = []
                for acc in accounts:
                    accounts_data.append({
                        "ID": acc.id,
                        "Name": acc.name,
                        "Currency": acc.currency,
                        "Created": acc.created_at.isoformat() if acc.created_at else "",
                    })
                
                df = pd.DataFrame(accounts_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download Accounts CSV",
                    data=csv,
                    file_name=f"accounts_{date.today().isoformat()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            except Exception as e:
                set_error_message(f"Error exporting accounts: {str(e)}")
        
        # Export transactions
        if st.button("📥 Export Transactions", use_container_width=True):
            try:
                all_transactions = []
                for account in accounts:
                    transactions = get_transactions_by_account(account.id, None, None, db)
                    for txn in transactions:
                        all_transactions.append({
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
                
                df = pd.DataFrame(all_transactions)
                csv = df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download Transactions CSV",
                    data=csv,
                    file_name=f"transactions_{date.today().isoformat()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            except Exception as e:
                set_error_message(f"Error exporting transactions: {str(e)}")
    
    with col2:
        st.markdown("#### Import Data")
        st.warning("⚠️ Import functionality is available in the Transactions page.")
        st.info("Use the CSV import feature in the **Transactions** page to import transaction data.")
        
        # Placeholder for future import features
        st.markdown("#### Future Import Features")
        st.info("""
        Future import features may include:
        - Import accounts from CSV
        - Bulk import prices
        - Import from other portfolio tracking tools
        """)

