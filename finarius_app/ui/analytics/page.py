"""Main analytics page rendering."""

from datetime import date
import streamlit as st

from finarius_app.core.models import get_all_accounts
from finarius_app.ui.session_state import get_db
from finarius_app.ui.error_handler import error_handler
from .filters import render_filters
from .performance import render_performance_analytics
from .gains import render_gains_analysis
from .returns import render_returns_analysis
from .risk import render_risk_metrics
from .dividends import render_dividend_analytics
from .positions import render_position_analytics


@error_handler
def render_analytics_page() -> None:
    """Render analytics page."""
    st.title("📈 Analytics")
    
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
    
    # Performance analytics
    render_performance_analytics(account_id, start_date, end_date, db)
    
    st.markdown("---")
    
    # Gains/losses analysis
    render_gains_analysis(account_id, start_date, end_date, db)
    
    st.markdown("---")
    
    # Returns analysis
    render_returns_analysis(account_id, start_date, end_date, db)
    
    st.markdown("---")
    
    # Risk metrics
    render_risk_metrics(account_id, start_date, end_date, db)
    
    st.markdown("---")
    
    # Dividend analytics
    render_dividend_analytics(account_id, start_date, end_date, db)
    
    st.markdown("---")
    
    # Position analytics
    render_position_analytics(account_id, end_date, db)

