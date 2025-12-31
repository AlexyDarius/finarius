"""Performance metrics section for dashboard."""

from typing import Optional
from datetime import date
import streamlit as st

from finarius_app.core.metrics import (
    calculate_cagr,
    calculate_irr,
    calculate_twrr,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
)
from finarius_app.core.prices.downloader import PriceDownloader


def render_performance_metrics(
    account_id: Optional[int],
    start_date: date,
    end_date: date,
    db,
) -> None:
    """Render performance metrics section.
    
    Args:
        account_id: Account ID (None for all accounts).
        start_date: Start date for calculations.
        end_date: End date for calculations.
        db: Database instance.
    """
    st.subheader("📈 Performance Metrics")
    
    price_downloader = PriceDownloader(db=db)
    
    if account_id is None:
        # For all accounts, show aggregate or first account
        from finarius_app.core.models import get_all_accounts
        accounts = get_all_accounts(db)
        if not accounts:
            st.info("No accounts available")
            return
        # Use first account for now (could aggregate later)
        account_id = accounts[0].id
        st.info(f"📊 Showing metrics for: {accounts[0].name} (aggregate metrics coming soon)")
    
    try:
        # Calculate metrics
        cagr = calculate_cagr(account_id, start_date, end_date, db, price_downloader)
        irr = calculate_irr(account_id, start_date, end_date, db, price_downloader)
        twrr = calculate_twrr(account_id, start_date, end_date, db, price_downloader)
        sharpe = calculate_sharpe_ratio(account_id, start_date, end_date, 0.02, db, price_downloader)
        max_dd = calculate_max_drawdown(account_id, start_date, end_date, db, price_downloader)
        
        # Display in columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("CAGR", f"{cagr*100:.2f}%" if cagr else "N/A")
        
        with col2:
            st.metric("IRR", f"{irr*100:.2f}%" if irr else "N/A")
        
        with col3:
            st.metric("TWRR", f"{twrr*100:.2f}%" if twrr else "N/A")
        
        with col4:
            st.metric("Sharpe Ratio", f"{sharpe:.2f}" if sharpe else "N/A")
        
        with col5:
            st.metric("Max Drawdown", f"{max_dd*100:.2f}%" if max_dd else "N/A")
            
    except Exception as e:
        st.warning(f"⚠️ Some metrics could not be calculated: {str(e)}")

