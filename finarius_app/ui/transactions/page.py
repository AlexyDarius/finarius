"""Main transactions page rendering."""

from datetime import date
import streamlit as st

from finarius_app.core.models import get_all_accounts
from finarius_app.ui.session_state import get_db
from finarius_app.ui.error_handler import error_handler
from .filters import render_filters, get_filtered_transactions
from .table import render_transactions_table
from .forms import render_transaction_form
from .csv import render_csv_import_form, generate_csv


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
    filters = render_filters(accounts, db)
    
    st.markdown("---")
    
    # Get filtered transactions
    transactions = get_filtered_transactions(filters, db)
    
    # Display transactions table
    render_transactions_table(transactions, accounts, db)
    
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
            csv_data = generate_csv(transactions)
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
        render_transaction_form(accounts, db)
    
    # CSV import form
    if st.session_state.get("show_csv_import", False):
        st.markdown("---")
        render_csv_import_form(accounts, db)

