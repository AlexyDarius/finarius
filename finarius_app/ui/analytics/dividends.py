"""Dividend analytics section for analytics page."""

from typing import Optional
from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.metrics import (
    get_dividend_history,
    calculate_dividend_income,
    calculate_dividend_yield,
    get_dividend_by_symbol,
    calculate_dividend_yield_by_symbol,
)


def render_dividend_analytics(
    account_id: Optional[int],
    start_date: date,
    end_date: date,
    db,
) -> None:
    """Render dividend analytics section.
    
    Args:
        account_id: Account ID (None for all accounts).
        start_date: Start date for calculations.
        end_date: End date for calculations.
        db: Database instance.
    """
    st.subheader("💰 Dividend Analytics")
    
    try:
        if account_id is None:
            # Aggregate dividends across all accounts
            from finarius_app.core.models import get_all_accounts
            accounts = get_all_accounts(db)
            if not accounts:
                st.info("No accounts available")
                return
            
            total_dividends = 0.0
            total_portfolio_value = 0.0
            dividend_by_symbol = {}
            dividend_history = []
            
            for acc in accounts:
                acc_dividends = calculate_dividend_income(acc.id, start_date, end_date, db)
                total_dividends += acc_dividends
                
                # Get portfolio value for yield calculation
                from finarius_app.core.engine import calculate_portfolio_value
                acc_value = calculate_portfolio_value(acc.id, end_date, db)
                total_portfolio_value += acc_value
                
                # Aggregate by symbol
                acc_by_symbol = get_dividend_by_symbol(acc.id, start_date, end_date, db)
                for symbol, amount in acc_by_symbol.items():
                    if symbol not in dividend_by_symbol:
                        dividend_by_symbol[symbol] = 0.0
                    dividend_by_symbol[symbol] += amount
                
                # Aggregate history
                acc_history = get_dividend_history(acc.id, start_date, end_date, db)
                dividend_history.extend(acc_history)
            
            # Calculate aggregate dividend yield
            dividend_yield = (total_dividends / total_portfolio_value) if total_portfolio_value > 0 else None
        else:
            # Single account
            total_dividends = calculate_dividend_income(account_id, start_date, end_date, db)
            dividend_yield = calculate_dividend_yield(account_id, end_date, db)
            dividend_by_symbol = get_dividend_by_symbol(account_id, start_date, end_date, db)
            dividend_history = get_dividend_history(account_id, start_date, end_date, db)
        
        # Display summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Dividend Income", f"${total_dividends:,.2f}")
        with col2:
            st.metric("Dividend Yield", f"{dividend_yield*100:.2f}%" if dividend_yield else "N/A")
        
        # Dividend income over time
        st.markdown("#### Dividend Income Over Time")
        if dividend_history:
            # Group by date
            dividend_by_date = {}
            for div in dividend_history:
                div_date = div["date"]
                if div_date not in dividend_by_date:
                    dividend_by_date[div_date] = 0.0
                dividend_by_date[div_date] += div["amount"]
            
            df = pd.DataFrame([
                {"Date": d, "Dividend Income": v} for d, v in sorted(dividend_by_date.items())
            ])
            
            try:
                import plotly.express as px
                fig = px.bar(
                    df,
                    x="Date",
                    y="Dividend Income",
                    title="Dividend Income Over Time",
                    labels={"Dividend Income": "Dividend Income ($)", "Date": "Date"}
                )
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.bar_chart(df.set_index("Date"))
        else:
            st.info("No dividend history data available")
        
        # Dividend by symbol
        st.markdown("#### Dividends by Symbol")
        if dividend_by_symbol:
            dividend_data = [
                {"Symbol": symbol, "Dividend Income": f"${amount:,.2f}"}
                for symbol, amount in sorted(dividend_by_symbol.items(), key=lambda x: x[1], reverse=True)
            ]
            df_dividends = pd.DataFrame(dividend_data)
            st.dataframe(df_dividends, use_container_width=True, hide_index=True)
        else:
            st.info("No dividend data by symbol available")
        
        # Dividend yield trends (simplified)
        st.markdown("#### Dividend Yield Trends")
        st.info("Dividend yield trends analysis coming soon")
        
    except Exception as e:
        st.warning(f"⚠️ Error calculating dividend analytics: {str(e)}")

