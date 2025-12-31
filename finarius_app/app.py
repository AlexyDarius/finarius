"""Main Streamlit application entry point."""

import streamlit as st

st.set_page_config(
    page_title="Finarius - Portfolio Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Finarius")
st.markdown("A fully local, privacy-first portfolio tracking and analytics application.")

st.info("🚧 Application under development. Core features coming soon!")

