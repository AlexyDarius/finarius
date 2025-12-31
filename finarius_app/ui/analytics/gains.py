"""Gains/losses analysis section for analytics page."""

from typing import Optional
from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.metrics import (
    calculate_realized_gains,
    calculate_unrealized_gains,
    get_realized_gains_by_symbol,
    get_unrealized_gains_by_symbol,
    get_realized_gains_history,
    get_unrealized_gains_history,
)
from finarius_app.core.prices.downloader import PriceDownloader


def render_gains_analysis(
    account_id: Optional[int],
    start_date: date,
    end_date: date,
    db,
) -> None:
    """Render gains/losses analysis section.
    
    Args:
        account_id: Account ID (None for all accounts).
        start_date: Start date for calculations.
        end_date: End date for calculations.
        db: Database instance.
    """
    st.subheader("💰 Gains/Losses Analysis")
    
    price_downloader = PriceDownloader(db=db)
    
    try:
        if account_id is None:
            # Aggregate gains across all accounts
            from finarius_app.core.models import get_all_accounts
            accounts = get_all_accounts(db)
            if not accounts:
                st.info("No accounts available")
                return
            
            realized = 0.0
            unrealized = 0.0
            realized_by_symbol = {}
            unrealized_by_symbol = {}
            realized_history = {}
            unrealized_history = {}
            
            for acc in accounts:
                acc_realized = calculate_realized_gains(acc.id, start_date, end_date, db)
                realized += acc_realized
                
                acc_unrealized = calculate_unrealized_gains(acc.id, end_date, db, price_downloader)
                unrealized += acc_unrealized
                
                # Aggregate by symbol
                acc_realized_by_symbol = get_realized_gains_by_symbol(acc.id, start_date, end_date, db)
                for symbol, gains in acc_realized_by_symbol.items():
                    if symbol not in realized_by_symbol:
                        realized_by_symbol[symbol] = 0.0
                    realized_by_symbol[symbol] += gains
                
                acc_unrealized_by_symbol = get_unrealized_gains_by_symbol(acc.id, end_date, db, price_downloader)
                for symbol, gains in acc_unrealized_by_symbol.items():
                    if symbol not in unrealized_by_symbol:
                        unrealized_by_symbol[symbol] = 0.0
                    unrealized_by_symbol[symbol] += gains
                
                # Aggregate histories
                acc_realized_hist = get_realized_gains_history(acc.id, start_date, end_date, db)
                for date, value in acc_realized_hist.items():
                    if date not in realized_history:
                        realized_history[date] = 0.0
                    realized_history[date] += value
                
                acc_unrealized_hist = get_unrealized_gains_history(acc.id, start_date, end_date, db, price_downloader)
                for date, value in acc_unrealized_hist.items():
                    if date not in unrealized_history:
                        unrealized_history[date] = 0.0
                    unrealized_history[date] += value
            
            total_pnl = realized + unrealized
        else:
            # Single account
            realized = calculate_realized_gains(account_id, start_date, end_date, db)
            unrealized = calculate_unrealized_gains(account_id, end_date, db, price_downloader)
            total_pnl = realized + unrealized
            realized_by_symbol = get_realized_gains_by_symbol(account_id, start_date, end_date, db)
            unrealized_by_symbol = get_unrealized_gains_by_symbol(account_id, end_date, db, price_downloader)
            realized_history = get_realized_gains_history(account_id, start_date, end_date, db)
            unrealized_history = get_unrealized_gains_history(account_id, start_date, end_date, db, price_downloader)
        
        # Display summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Realized Gains/Losses", f"${realized:,.2f}")
        with col2:
            st.metric("Unrealized Gains/Losses", f"${unrealized:,.2f}")
        with col3:
            st.metric("Total P&L", f"${total_pnl:,.2f}")
        
        # Realized gains breakdown by symbol
        st.markdown("#### Realized Gains by Symbol")
        
        if realized_by_symbol:
            realized_data = [
                {"Symbol": symbol, "Realized Gains": f"${gains:,.2f}"}
                for symbol, gains in sorted(realized_by_symbol.items(), key=lambda x: x[1], reverse=True)
            ]
            df_realized = pd.DataFrame(realized_data)
            st.dataframe(df_realized, use_container_width=True, hide_index=True)
        else:
            st.info("No realized gains data available")
        
        # Unrealized gains breakdown by symbol
        st.markdown("#### Unrealized Gains by Symbol")
        
        if unrealized_by_symbol:
            unrealized_data = [
                {"Symbol": symbol, "Unrealized Gains": f"${gains:,.2f}"}
                for symbol, gains in sorted(unrealized_by_symbol.items(), key=lambda x: x[1], reverse=True)
            ]
            df_unrealized = pd.DataFrame(unrealized_data)
            st.dataframe(df_unrealized, use_container_width=True, hide_index=True)
        else:
            st.info("No unrealized gains data available")
        
        # Combined PnL chart
        st.markdown("#### Gains/Losses Over Time")
        
        if realized_history or unrealized_history:
            # Combine histories (sample weekly for performance)
            all_dates = set()
            if realized_history:
                all_dates.update(realized_history.keys())
            if unrealized_history:
                all_dates.update(unrealized_history.keys())
            
            # Sample dates (weekly)
            sampled_dates = sorted([d for i, d in enumerate(sorted(all_dates)) if i % 7 == 0])
            
            chart_data = []
            for d in sampled_dates:
                row = {"Date": d}
                row["Realized"] = realized_history.get(d, 0.0)
                row["Unrealized"] = unrealized_history.get(d, 0.0)
                row["Total P&L"] = row["Realized"] + row["Unrealized"]
                chart_data.append(row)
            
            if chart_data:
                df = pd.DataFrame(chart_data)
                try:
                    import plotly.express as px
                    fig = px.line(
                        df,
                        x="Date",
                        y=["Realized", "Unrealized", "Total P&L"],
                        title="Gains/Losses Over Time",
                        labels={"value": "Gains/Losses ($)", "Date": "Date"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.line_chart(df.set_index("Date"))
        else:
            st.info("No gains history data available")
            
    except Exception as e:
        st.warning(f"⚠️ Error calculating gains analysis: {str(e)}")

