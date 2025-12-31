"""Dividend summary section for dashboard."""

from typing import Optional
from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.metrics import (
    calculate_dividend_income,
    calculate_dividend_yield,
    get_dividend_by_symbol,
)


def render_dividend_summary(
    account_id: Optional[int],
    start_date: date,
    end_date: date,
    db,
) -> None:
    """Render dividend summary section.
    
    Args:
        account_id: Account ID (None for all accounts).
        start_date: Start date for dividend period.
        end_date: End date for dividend period.
        db: Database instance.
    """
    st.subheader("💰 Dividend Summary")
    
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
            
            # Calculate aggregate dividend yield
            dividend_yield = (total_dividends / total_portfolio_value) if total_portfolio_value > 0 else None
        else:
            # Single account
            total_dividends = calculate_dividend_income(account_id, start_date, end_date, db)
            dividend_yield = calculate_dividend_yield(account_id, end_date, db)
            dividend_by_symbol = get_dividend_by_symbol(account_id, start_date, end_date, db)
        
        # Display metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Dividends (Period)", f"${total_dividends:,.2f}")
        
        with col2:
            st.metric("Dividend Yield", f"{dividend_yield*100:.2f}%" if dividend_yield else "N/A")
        
        # Top dividend payers
        if dividend_by_symbol:
            st.markdown("#### Top Dividend Payers")
            
            dividend_data = []
            for symbol, amount in dividend_by_symbol.items():
                dividend_data.append({
                    "Symbol": symbol,
                    "Dividend Income": f"${amount:,.2f}"
                })
            
            # Sort by amount descending
            dividend_data.sort(
                key=lambda x: float(x["Dividend Income"].replace("$", "").replace(",", "")),
                reverse=True
            )
            
            df = pd.DataFrame(dividend_data[:10])  # Top 10
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No dividend data available for this period")
            
    except Exception as e:
        st.warning(f"⚠️ Error loading dividend data: {str(e)}")

