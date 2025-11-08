"""
Analytics page for Streamlit pages/ - imports analytics renderer from components.
Filename starts with '2_' so Streamlit orders it after snippets.
"""
import streamlit as st
import os
import sys

base_dir = os.path.dirname(__file__) or "."
sys.path.insert(0, base_dir)

from components.analytics import render_analytics
from utils.storage import load_ratings

st.set_page_config(page_title="Analytics • AI Java Tutor Pro")

historical_df = st.session_state.get('historical_df', None)
# If not already cached in session, load it (component can rely on this)
if historical_df is None:
    historical_df = load_ratings()
    st.session_state['historical_df'] = historical_df

render_analytics(historical_df=historical_df)
