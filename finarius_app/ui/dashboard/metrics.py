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
    
    try:
        if account_id is None:
            # For all accounts, calculate aggregate metrics
            from finarius_app.core.models import get_all_accounts
            accounts = get_all_accounts(db)
            if not accounts:
                st.info("No accounts available")
                return
            
            # Aggregate metrics by combining all accounts' data
            # Note: Some metrics like CAGR/IRR/TWRR are complex to aggregate properly
            # For now, we'll calculate for the combined portfolio
            # This requires treating all accounts as one portfolio
            
            # Get combined portfolio value over time for metrics
            from finarius_app.core.engine import calculate_portfolio_value_over_time
            combined_values = {}
            for acc in accounts:
                acc_values = calculate_portfolio_value_over_time(
                    acc.id, start_date, end_date, "daily", db, price_downloader
                )
                for date, value in acc_values.items():
                    if date not in combined_values:
                        combined_values[date] = 0.0
                    combined_values[date] += value
            
            # For aggregate, we'll show a note that metrics are calculated per-account
            # and suggest selecting a specific account for detailed metrics
            st.info("📊 Performance metrics for multiple accounts. Select a specific account for detailed metrics.")
            
            # Calculate average or weighted metrics (simplified approach)
            cagrs = []
            irrs = []
            twrrs = []
            sharpes = []
            max_dds = []
            
            for acc in accounts:
                try:
                    cagr = calculate_cagr(acc.id, start_date, end_date, db, price_downloader)
                    if cagr is not None:
                        cagrs.append(cagr)
                    irr = calculate_irr(acc.id, start_date, end_date, db, price_downloader)
                    if irr is not None:
                        irrs.append(irr)
                    twrr = calculate_twrr(acc.id, start_date, end_date, db, price_downloader)
                    if twrr is not None:
                        twrrs.append(twrr)
                    sharpe = calculate_sharpe_ratio(acc.id, start_date, end_date, 0.02, db, price_downloader)
                    if sharpe is not None:
                        sharpes.append(sharpe)
                    max_dd = calculate_max_drawdown(acc.id, start_date, end_date, db, price_downloader)
                    if max_dd is not None:
                        max_dds.append(max_dd)
                except Exception:
                    pass
            
            # Show average (or could be weighted by portfolio size)
            cagr = sum(cagrs) / len(cagrs) if cagrs else None
            irr = sum(irrs) / len(irrs) if irrs else None
            twrr = sum(twrrs) / len(twrrs) if twrrs else None
            sharpe = sum(sharpes) / len(sharpes) if sharpes else None
            max_dd = sum(max_dds) / len(max_dds) if max_dds else None
        else:
            # Single account - calculate metrics normally
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

