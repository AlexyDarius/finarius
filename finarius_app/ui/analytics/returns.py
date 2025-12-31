"""Returns analysis section for analytics page."""

from typing import Optional
from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.metrics import (
    calculate_total_return,
    calculate_total_return_percentage,
    calculate_cagr,
    calculate_irr,
    calculate_twrr,
    get_cagr_history,
    get_irr_history,
    get_twrr_history,
)
from finarius_app.core.prices.downloader import PriceDownloader


def render_returns_analysis(
    account_id: Optional[int],
    start_date: date,
    end_date: date,
    db,
) -> None:
    """Render returns analysis section.
    
    Args:
        account_id: Account ID (None for all accounts).
        start_date: Start date for calculations.
        end_date: End date for calculations.
        db: Database instance.
    """
    st.subheader("📊 Returns Analysis")
    
    price_downloader = PriceDownloader(db=db)
    
    if account_id is None:
        from finarius_app.core.models import get_all_accounts
        accounts = get_all_accounts(db)
        if not accounts:
            st.info("No accounts available")
            return
        account_id = accounts[0].id
        st.info(f"📊 Showing returns analysis for: {accounts[0].name}")
    
    try:
        # Calculate current returns
        total_return = calculate_total_return(account_id, start_date, end_date, db, price_downloader)
        total_return_pct = calculate_total_return_percentage(account_id, start_date, end_date, db, price_downloader)
        cagr = calculate_cagr(account_id, start_date, end_date, db, price_downloader)
        irr = calculate_irr(account_id, start_date, end_date, db, price_downloader)
        twrr = calculate_twrr(account_id, start_date, end_date, db, price_downloader)
        
        # Display summary
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Return", f"${total_return:,.2f}")
        with col2:
            st.metric("Total Return %", f"{total_return_pct*100:.2f}%")
        with col3:
            st.metric("CAGR", f"{cagr*100:.2f}%" if cagr else "N/A")
        with col4:
            st.metric("IRR", f"{irr*100:.2f}%" if irr else "N/A")
        with col5:
            st.metric("TWRR", f"{twrr*100:.2f}%" if twrr else "N/A")
        
        # Returns over time chart
        st.markdown("#### Returns Over Time")
        
        cagr_history = get_cagr_history(account_id, start_date, end_date, db, price_downloader)
        irr_history = get_irr_history(account_id, start_date, end_date, db, price_downloader)
        twrr_history = get_twrr_history(account_id, start_date, end_date, db, price_downloader)
        
        if cagr_history or irr_history or twrr_history:
            # Combine histories
            all_dates = set()
            if cagr_history:
                all_dates.update(cagr_history.keys())
            if irr_history:
                all_dates.update(irr_history.keys())
            if twrr_history:
                all_dates.update(twrr_history.keys())
            
            # Sample dates (weekly for performance)
            sampled_dates = sorted([d for i, d in enumerate(sorted(all_dates)) if i % 7 == 0])
            
            chart_data = []
            for d in sampled_dates:
                row = {"Date": d}
                if d in cagr_history:
                    row["CAGR"] = cagr_history[d] * 100
                if d in irr_history:
                    row["IRR"] = irr_history[d] * 100 if irr_history[d] else None
                if d in twrr_history:
                    row["TWRR"] = twrr_history[d] * 100
                chart_data.append(row)
            
            if chart_data:
                df = pd.DataFrame(chart_data)
                try:
                    import plotly.express as px
                    fig = px.line(
                        df,
                        x="Date",
                        y=["CAGR", "IRR", "TWRR"],
                        title="Returns Metrics Over Time",
                        labels={"value": "Return (%)", "Date": "Date"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.line_chart(df.set_index("Date"))
        else:
            st.info("No returns history data available")
            
    except Exception as e:
        st.warning(f"⚠️ Error calculating returns analysis: {str(e)}")

