"""Top positions table for dashboard."""

from typing import Optional
from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.engine import get_portfolio_breakdown
from finarius_app.core.prices.downloader import PriceDownloader


def render_top_positions(
    account_id: Optional[int],
    end_date: date,
    db,
    limit: int = 10,
) -> None:
    """Render top positions table.
    
    Args:
        account_id: Account ID (None for all accounts).
        end_date: Date for positions.
        db: Database instance.
        limit: Maximum number of positions to display.
    """
    st.subheader("💼 Top Positions")
    
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
        
        # Prepare data for table
        positions_data = []
        for symbol, data in breakdown.items():
            if data["qty"] > 0:
                current_value = data["current_value"]
                cost_basis = data.get("cost_basis", 0.0)
                unrealized_gain = data.get("unrealized_gain", current_value - cost_basis)
                return_pct = (unrealized_gain / cost_basis * 100) if cost_basis > 0 else 0.0
                current_price = current_value / data["qty"] if data["qty"] > 0 else 0.0
                
                positions_data.append({
                    "Symbol": symbol,
                    "Quantity": f"{data['qty']:,.2f}",
                    "Current Price": f"${current_price:,.2f}",
                    "Cost Basis": f"${cost_basis:,.2f}",
                    "Current Value": f"${current_value:,.2f}",
                    "Unrealized G/L": f"${unrealized_gain:,.2f}",
                    "Return %": f"{return_pct:.2f}%",
                })
        
        # Sort by current value descending
        positions_data.sort(key=lambda x: float(x["Current Value"].replace("$", "").replace(",", "")), reverse=True)
        
        # Limit to top N
        positions_data = positions_data[:limit]
        
        if positions_data:
            df = pd.DataFrame(positions_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No positions to display")
            
    except Exception as e:
        st.warning(f"⚠️ Error loading positions: {str(e)}")

