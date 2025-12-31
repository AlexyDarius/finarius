"""Account statistics rendering for accounts UI."""

from datetime import date
import streamlit as st
import pandas as pd

from finarius_app.core.models import Account
from finarius_app.core.engine import calculate_portfolio_value


def render_account_statistics(accounts: list[Account], db) -> None:
    """Render account statistics section.
    
    Args:
        accounts: List of Account instances.
        db: Database instance.
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Accounts", len(accounts))
    
    with col2:
        currencies = len(set(acc.currency for acc in accounts)) if accounts else 0
        st.metric("Currencies", currencies)
    
    with col3:
        # Calculate total portfolio value across all accounts
        total_value = 0.0
        today = date.today()
        for account in accounts:
            try:
                value = calculate_portfolio_value(account.id, today, db)
                total_value += value
            except Exception:
                # If calculation fails, skip this account
                pass
        st.metric("Total Portfolio Value", f"${total_value:,.2f}" if total_value > 0 else "$0.00")
    
    with col4:
        st.metric("Status", "✅ Active" if accounts else "⚠️ No accounts")
    
    # Account breakdown chart (if accounts exist)
    if accounts:
        st.markdown("---")
        render_account_breakdown_chart(accounts, db)


def render_account_breakdown_chart(accounts: list[Account], db) -> None:
    """Render account breakdown pie chart.
    
    Args:
        accounts: List of Account instances.
        db: Database instance.
    """
    try:
        import plotly.express as px
        
        today = date.today()
        account_values = []
        account_names = []
        
        for account in accounts:
            try:
                value = calculate_portfolio_value(account.id, today, db)
                if value > 0:
                    account_values.append(value)
                    account_names.append(account.name)
            except Exception:
                # Skip accounts with calculation errors
                pass
        
        if account_values:
            st.subheader("Portfolio Value by Account")
            df = pd.DataFrame({
                "Account": account_names,
                "Value": account_values
            })
            
            fig = px.pie(
                df,
                values="Value",
                names="Account",
                title="Account Value Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        # Plotly not available, skip chart
        pass
    except Exception:
        # Chart rendering failed, skip
        pass

