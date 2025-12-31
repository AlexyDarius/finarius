"""Charts section for dashboard."""

from typing import Optional
from datetime import date, timedelta
import streamlit as st
import pandas as pd

from finarius_app.core.engine import calculate_portfolio_value_over_time, get_portfolio_breakdown
from finarius_app.core.metrics import get_dividend_history
from finarius_app.core.prices.downloader import PriceDownloader


def render_charts(
    account_id: Optional[int],
    start_date: date,
    end_date: date,
    db,
) -> None:
    """Render charts section.
    
    Args:
        account_id: Account ID (None for all accounts).
        start_date: Start date for charts.
        end_date: End date for charts.
        db: Database instance.
    """
    st.subheader("📊 Charts")
    
    price_downloader = PriceDownloader(db=db)
    
    if account_id is None:
        from finarius_app.core.models import get_all_accounts
        accounts = get_all_accounts(db)
        if not accounts:
            st.info("No accounts available for charts")
            return
        account_id = accounts[0].id
        st.info(f"📊 Showing charts for: {accounts[0].name}")
    
    try:
        # Portfolio value over time
        st.markdown("#### Portfolio Value Over Time")
        value_history = calculate_portfolio_value_over_time(
            account_id, start_date, end_date, "daily", db, price_downloader
        )
        
        if value_history:
            df = pd.DataFrame([
                {"Date": d, "Value": v} for d, v in sorted(value_history.items())
            ])
            
            try:
                import plotly.express as px
                fig = px.line(
                    df,
                    x="Date",
                    y="Value",
                    title="Portfolio Value Over Time",
                    labels={"Value": "Portfolio Value ($)", "Date": "Date"}
                )
                fig.update_traces(line=dict(width=2))
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.line_chart(df.set_index("Date"))
        else:
            st.info("No portfolio value data available")
        
        # Portfolio allocation pie chart
        st.markdown("#### Portfolio Allocation")
        breakdown = get_portfolio_breakdown(account_id, end_date, db, price_downloader)
        
        if breakdown:
            allocation_data = []
            for symbol, data in breakdown.items():
                if data["current_value"] > 0:
                    allocation_data.append({
                        "Symbol": symbol,
                        "Value": data["current_value"]
                    })
            
            if allocation_data:
                df = pd.DataFrame(allocation_data)
                try:
                    import plotly.express as px
                    fig = px.pie(
                        df,
                        values="Value",
                        names="Symbol",
                        title="Portfolio Allocation by Symbol"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.bar_chart(df.set_index("Symbol"))
            else:
                st.info("No allocation data available")
        else:
            st.info("No portfolio breakdown available")
        
        # Dividend income over time
        st.markdown("#### Dividend Income Over Time")
        dividend_history = get_dividend_history(account_id, start_date, end_date, db)
        
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
            st.info("No dividend data available")
            
    except Exception as e:
        st.warning(f"⚠️ Error rendering charts: {str(e)}")

