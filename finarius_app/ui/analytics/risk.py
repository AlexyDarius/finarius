"""Risk metrics section for analytics page."""

from typing import Optional
from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.metrics import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_volatility,
    calculate_beta,
)
from finarius_app.core.prices.downloader import PriceDownloader


def render_risk_metrics(
    account_id: Optional[int],
    start_date: date,
    end_date: date,
    db,
) -> None:
    """Render risk metrics section.
    
    Args:
        account_id: Account ID (None for all accounts).
        start_date: Start date for calculations.
        end_date: End date for calculations.
        db: Database instance.
    """
    st.subheader("⚠️ Risk Metrics")
    
    price_downloader = PriceDownloader(db=db)
    
    if account_id is None:
        from finarius_app.core.models import get_all_accounts
        accounts = get_all_accounts(db)
        if not accounts:
            st.info("No accounts available")
            return
        account_id = accounts[0].id
        st.info(f"📊 Showing risk metrics for: {accounts[0].name}")
    
    try:
        # Calculate risk metrics
        sharpe = calculate_sharpe_ratio(account_id, start_date, end_date, 0.02, db, price_downloader)
        max_dd = calculate_max_drawdown(account_id, start_date, end_date, db, price_downloader)
        volatility = calculate_volatility(account_id, start_date, end_date, db, price_downloader)
        
        # Beta calculation (requires benchmark symbol - using SPY as default)
        beta = None
        try:
            beta = calculate_beta(account_id, "SPY", start_date, end_date, db, price_downloader)
        except Exception:
            pass  # Beta calculation may fail if benchmark data unavailable
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Sharpe Ratio", f"{sharpe:.2f}" if sharpe else "N/A",
                     help="Risk-adjusted return measure (higher is better)")
        
        with col2:
            st.metric("Max Drawdown", f"{max_dd*100:.2f}%" if max_dd else "N/A",
                     help="Maximum peak-to-trough decline")
        
        with col3:
            st.metric("Volatility", f"{volatility*100:.2f}%" if volatility else "N/A",
                     help="Portfolio volatility (standard deviation of returns)")
        
        with col4:
            st.metric("Beta (vs SPY)", f"{beta:.2f}" if beta else "N/A",
                     help="Portfolio sensitivity to market movements")
        
        # Risk metrics table
        st.markdown("#### Risk Metrics Summary")
        risk_data = {
            "Metric": ["Sharpe Ratio", "Max Drawdown", "Volatility", "Beta (vs SPY)"],
            "Value": [
                f"{sharpe:.2f}" if sharpe else "N/A",
                f"{max_dd*100:.2f}%" if max_dd else "N/A",
                f"{volatility*100:.2f}%" if volatility else "N/A",
                f"{beta:.2f}" if beta else "N/A",
            ],
            "Description": [
                "Risk-adjusted return (higher is better)",
                "Maximum peak-to-trough decline",
                "Standard deviation of returns",
                "Sensitivity to market (1.0 = market average)",
            ]
        }
        df_risk = pd.DataFrame(risk_data)
        st.dataframe(df_risk, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.warning(f"⚠️ Error calculating risk metrics: {str(e)}")

