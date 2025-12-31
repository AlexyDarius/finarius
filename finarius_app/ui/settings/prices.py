"""Price update settings section for settings page."""

import streamlit as st

from finarius_app.core.prices.downloader import PriceDownloader
from finarius_app.core.prices.scheduler import get_all_portfolio_symbols, update_prices_for_symbol, update_all_prices
from finarius_app.core.models import get_all_accounts
from finarius_app.ui.session_state import get_db, set_success_message, set_error_message


def render_price_settings(db) -> None:
    """Render price update settings section.
    
    Args:
        db: Database instance.
    """
    st.subheader("📈 Price Update Settings")
    
    # Auto-update frequency (placeholder - would need scheduler implementation)
    st.markdown("#### Auto-Update Frequency")
    st.info("Auto-update frequency configuration coming soon. For now, use manual updates.")
    
    # Manual update
    st.markdown("---")
    st.markdown("#### Manual Price Update")
    
    # Get all symbols from portfolio
    all_symbols = get_all_portfolio_symbols(db)
    
    if not all_symbols:
        st.info("No symbols found in transactions. Add transactions first to update prices.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_symbol = st.selectbox(
            "Select Symbol to Update",
            options=sorted(all_symbols),
            help="Select a symbol to update its latest price"
        )
        
        if st.button("🔄 Update Selected Symbol", use_container_width=True):
            try:
                result = update_prices_for_symbol(selected_symbol, db=db, force_update=True)
                if result["success"]:
                    set_success_message(f"Updated {result['prices_downloaded']} prices for {selected_symbol}")
                else:
                    set_error_message(f"Error updating {selected_symbol}: {result.get('error', 'Unknown error')}")
                st.rerun()
            except Exception as e:
                set_error_message(f"Error updating price for {selected_symbol}: {str(e)}")
                st.rerun()
    
    with col2:
        st.markdown("#### Update All Prices")
        st.warning("⚠️ This may take a while if you have many symbols.")
        
        if st.button("🔄 Update All Prices", use_container_width=True, type="primary"):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def progress_callback(current, total, symbol):
                    status_text.text(f"Updating {symbol} ({current}/{total})...")
                    progress_bar.progress(current / total if total > 0 else 0)
                
                result = update_all_prices(
                    db=db,
                    force_update=True,
                    progress_callback=progress_callback
                )
                
                status_text.empty()
                progress_bar.empty()
                
                set_success_message(
                    f"Price update completed: {result['successful']} successful, "
                    f"{result['failed']} failed, {result['total_prices']} prices downloaded"
                )
                st.rerun()
            except Exception as e:
                set_error_message(f"Error updating prices: {str(e)}")
                st.rerun()

