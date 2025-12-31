"""Main dashboard page rendering."""

from datetime import date
import streamlit as st

from finarius_app.core.models import get_all_accounts
from finarius_app.ui.session_state import get_db
from finarius_app.ui.error_handler import error_handler
from .filters import render_filters
from .overview import render_portfolio_overview
from .metrics import render_performance_metrics
from .charts import render_charts
from .positions import render_top_positions
from .transactions import render_recent_transactions
from .dividends import render_dividend_summary


@error_handler
def render_dashboard_page() -> None:
    """Render dashboard page."""
    st.title("📊 Dashboard")
    
    db = get_db()
    if db is None:
        st.error("Database not initialized")
        return
    
    # Get all accounts
    accounts = get_all_accounts(db)
    
    if not accounts:
        st.warning("⚠️ No accounts found. Please create an account first.")
        st.info("Go to the **Accounts** page to create your first account.")
        return
    
    # Filters
    account_id, start_date, end_date = render_filters(db)
    
    st.markdown("---")
    
    # Portfolio overview
    render_portfolio_overview(account_id, end_date, start_date, db)
    
    st.markdown("---")
    
    # Performance metrics
    render_performance_metrics(account_id, start_date, end_date, db)
    
    st.markdown("---")
    
    # Charts
    render_charts(account_id, start_date, end_date, db)
    
    st.markdown("---")
    
    # Two columns for positions and transactions
    col1, col2 = st.columns(2)
    
    with col1:
        render_top_positions(account_id, end_date, db)
    
    with col2:
        render_recent_transactions(account_id, db)
    
    st.markdown("---")
    
    # Dividend summary
    render_dividend_summary(account_id, start_date, end_date, db)

