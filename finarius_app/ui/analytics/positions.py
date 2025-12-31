"""Position analytics section for analytics page."""

from typing import Optional
from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.engine import get_portfolio_breakdown
from finarius_app.core.prices.downloader import PriceDownloader


def render_position_analytics(
    account_id: Optional[int],
    end_date: date,
    db,
) -> None:
    """Render position analytics section.
    
    Args:
        account_id: Account ID (None for all accounts).
        end_date: Date for position analysis.
        db: Database instance.
    """
    st.subheader("💼 Position Analytics")
    
    price_downloader = PriceDownloader(db=db)
    
    try:
        if account_id is None:
            # Aggregate positions across all accounts
            from finarius_app.core.models import get_all_accounts
            accounts = get_all_accounts(db)
            if not accounts:
                st.info("No accounts available")
                return
            
            aggregated_breakdown = {}
            for acc in accounts:
                acc_breakdown = get_portfolio_breakdown(acc.id, end_date, db, price_downloader)
                for symbol, data in acc_breakdown.items():
                    if symbol not in aggregated_breakdown:
                        aggregated_breakdown[symbol] = {
                            "qty": 0.0,
                            "cost_basis": 0.0,
                            "current_value": 0.0,
                            "unrealized_gain": 0.0,
                        }
                    aggregated_breakdown[symbol]["qty"] += data["qty"]
                    aggregated_breakdown[symbol]["cost_basis"] += data["cost_basis"]
                    aggregated_breakdown[symbol]["current_value"] += data["current_value"]
                    aggregated_breakdown[symbol]["unrealized_gain"] += data["unrealized_gain"]
            breakdown = aggregated_breakdown
        else:
            breakdown = get_portfolio_breakdown(account_id, end_date, db, price_downloader)
        
        if not breakdown:
            st.info("No positions found")
            return
        
        # Calculate position metrics
        total_value = sum(data["current_value"] for data in breakdown.values())
        
        position_data = []
        for symbol, data in breakdown.items():
            if data["qty"] > 0:
                current_value = data["current_value"]
                weight = (current_value / total_value * 100) if total_value > 0 else 0.0
                
                position_data.append({
                    "Symbol": symbol,
                    "Quantity": f"{data['qty']:,.2f}",
                    "Current Value": f"${current_value:,.2f}",
                    "Weight %": f"{weight:.2f}%",
                })
        
        # Sort by value descending
        position_data.sort(
            key=lambda x: float(x["Current Value"].replace("$", "").replace(",", "")),
            reverse=True
        )
        
        # Position size analysis
        st.markdown("#### Position Size Analysis")
        if position_data:
            df = pd.DataFrame(position_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Concentration risk (top 5 positions)
            top_5_weight = sum(
                float(p["Weight %"].replace("%", "")) for p in position_data[:5]
            )
            st.metric("Top 5 Positions Concentration", f"{top_5_weight:.2f}%",
                     help="Percentage of portfolio in top 5 positions")
            
            # Diversification metrics
            st.markdown("#### Diversification Metrics")
            num_positions = len(position_data)
            num_symbols = len(set(p["Symbol"] for p in position_data))
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Number of Positions", num_positions)
            with col2:
                st.metric("Number of Symbols", num_symbols)
        else:
            st.info("No position data available")
            
    except Exception as e:
        st.warning(f"⚠️ Error calculating position analytics: {str(e)}")

