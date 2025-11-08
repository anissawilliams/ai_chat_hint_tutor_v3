"""
Snippets page for Streamlit pages/ - imports the snippets renderer from components.
Filename starts with '1_' so Streamlit orders it near top.
"""
import streamlit as st
import os
import sys

base_dir = os.path.dirname(__file__) or "."
sys.path.insert(0, base_dir)

from components.snippets_library import render_snippets_library
from utils.snippets import CODE_SNIPPETS
from utils.personas import get_available_personas
from utils.gamification import get_affinity_tier, add_affinity

# Minimal page metadata
st.set_page_config(page_title="Snippets • AI Java Tutor Pro")

# Acquire data from session (app.py manages session state)
user_progress = st.session_state.get('user_progress', {})
user_level = user_progress.get('level', 1)
user_affinity = user_progress.get('affinity', {})

render_snippets_library(
    user_level=user_level,
    user_affinity=user_affinity,
    code_snippets=CODE_SNIPPETS,
    get_available_personas=get_available_personas,
    add_affinity_fn=add_affinity
)
