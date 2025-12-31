"""Portfolio overview metrics for dashboard."""

from typing import Optional
from datetime import date
import streamlit as st

from finarius_app.core.engine import calculate_portfolio_value, get_portfolio_breakdown
from finarius_app.core.engine.positions import get_positions
from finarius_app.core.metrics import (
    calculate_unrealized_gains,
    calculate_realized_gains,
    calculate_total_return,
    calculate_total_return_percentage,
)
from finarius_app.core.prices.downloader import PriceDownloader


def render_portfolio_overview(
    account_id: Optional[int],
    end_date: date,
    start_date: date,
    db,
) -> None:
    """Render portfolio overview section.
    
    Args:
        account_id: Account ID (None for all accounts).
        end_date: End date for calculations.
        start_date: Start date for calculations.
        db: Database instance.
    """
    st.subheader("📊 Portfolio Overview")
    
    price_downloader = PriceDownloader(db=db)
    
    if account_id is None:
        # Aggregate across all accounts
        from finarius_app.core.models import get_all_accounts
        accounts = get_all_accounts(db)
        
        total_value = 0.0
        total_cost_basis = 0.0
        total_unrealized = 0.0
        total_realized = 0.0
        total_return = 0.0
        total_return_pct = 0.0
        all_positions = {}
        num_symbols = set()
        
        for acc in accounts:
            try:
                value = calculate_portfolio_value(acc.id, end_date, db, price_downloader)
                total_value += value
                
                # Get positions for cost basis
                positions = get_positions(acc.id, end_date, db)
                for symbol, pos in positions.items():
                    if pos["qty"] > 0:
                        total_cost_basis += pos["cost_basis"]
                        num_symbols.add(symbol)
                        if symbol not in all_positions:
                            all_positions[symbol] = {"qty": 0.0, "cost_basis": 0.0}
                        all_positions[symbol]["qty"] += pos["qty"]
                        all_positions[symbol]["cost_basis"] += pos["cost_basis"]
                
                unrealized = calculate_unrealized_gains(acc.id, end_date, db, price_downloader)
                total_unrealized += unrealized
                
                realized = calculate_realized_gains(acc.id, start_date, end_date, db)
                total_realized += realized
                
                ret = calculate_total_return(acc.id, start_date, end_date, db, price_downloader)
                total_return += ret
                
            except Exception:
                pass
        
        total_cost_basis = sum(pos["cost_basis"] for pos in all_positions.values())
        if total_cost_basis > 0:
            total_return_pct = ((total_value - total_cost_basis) / total_cost_basis) * 100
        num_positions = len(all_positions)
    else:
        # Single account
        try:
            total_value = calculate_portfolio_value(account_id, end_date, db, price_downloader)
            
            positions = get_positions(account_id, end_date, db)
            total_cost_basis = sum(pos["cost_basis"] for pos in positions.values() if pos["qty"] > 0)
            
            total_unrealized = calculate_unrealized_gains(account_id, end_date, db, price_downloader)
            total_realized = calculate_realized_gains(account_id, start_date, end_date, db)
            total_return = calculate_total_return(account_id, start_date, end_date, db, price_downloader)
            total_return_pct = calculate_total_return_percentage(account_id, start_date, end_date, db, price_downloader) * 100
            
            num_positions = len([p for p in positions.values() if p["qty"] > 0])
            num_symbols = len([s for s in positions.keys() if positions[s]["qty"] > 0])
        except Exception as e:
            st.error(f"Error calculating portfolio metrics: {str(e)}")
            return
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Portfolio Value", f"${total_value:,.2f}")
        st.metric("Total Cost Basis", f"${total_cost_basis:,.2f}")
    
    with col2:
        st.metric("Unrealized Gains/Losses", f"${total_unrealized:,.2f}", 
                 delta=f"{total_unrealized/total_cost_basis*100:.2f}%" if total_cost_basis > 0 else "0%")
        st.metric("Realized Gains/Losses", f"${total_realized:,.2f}")
    
    with col3:
        st.metric("Total Return", f"${total_return:,.2f}")
        st.metric("Total Return %", f"{total_return_pct:.2f}%",
                 delta=f"{total_return_pct:.2f}%")
    
    with col4:
        st.metric("Number of Positions", num_positions)
        st.metric("Number of Symbols", num_symbols if isinstance(num_symbols, int) else len(num_symbols))

