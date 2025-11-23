import streamlit as st
import sys
import os
import yaml
import traceback
from datetime import datetime

# ==========================
# 1. PATH FIXER (Crucial for your nested folder)
# ==========================
# This ensures Python finds 'utils' and 'components' even in deep folders
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
# If utils are one level up, uncomment the next line:
# sys.path.insert(0, os.path.dirname(current_dir))

# ==========================
# 2. AUTH, PAGE CONFIG & IMPORTS
# ==========================
from utils.auth import render_login_component
# Check Authentication FIRST
user = render_login_component()

if not user:
    st.stop() # Stop here if not logged in

st.set_page_config(page_title="AI Java Tutor Pro", page_icon="🧠", layout="wide")

# Import your local modules (now that paths are fixed)
try:
    from utils.storage import load_user_progress, save_user_progress, load_ratings
    from utils.data_collection import TutorAnalytics, inject_google_analytics
    from utils.gamification import (
        get_xp_for_level, get_level_tier, calculate_xp_progress, update_streak
    )
    from utils.personas import build_persona_data, get_available_personas
    from components.header import render_header
    from components.sidebar import render_sidebar
    from components.rewards import render_reward_popup
    from components.persona_selector import render_persona_selector
    from components.question_mode import render_question_mode
    from components.code_review_mode import render_code_review_mode
    from components.analytics import render_analytics
    from components.snippets_library import render_snippets_library
    from components.css import load_css
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.info("Make sure your 'utils' and 'components' folders are in the same directory as app.py")
    st.stop()

# ==========================
# 3. ANALYTICS SETUP
# ==========================
# Inject the basic tag for Page Views
inject_google_analytics()

# Initialize the robust Python-side tracker
analytics = TutorAnalytics()

# ==========================
# 4. SESSION STATE & LOAD
# ==========================
if 'user_progress' not in st.session_state:
    st.session_state.user_progress = load_user_progress()

if 'last_interaction_time' not in st.session_state:
    st.session_state.last_interaction_time = datetime.now()

if 'attempt_counter' not in st.session_state:
    st.session_state.attempt_counter = 0
# Initialize other state vars
defaults = {
    'current_persona': None,
    'active_mode': 'question',
    'active_page': 'home',
    'show_reward': None,
    'start_time': datetime.now()
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Update Streak (Runs once per load)
update_streak(st.session_state.user_progress, st.session_state)

# Load CSS
load_css()

# ==========================
# 5. LOAD AI & CONFIG
# ==========================
@st.cache_data(show_spinner=False)
def get_cached_persona_data():
    # Try multiple paths to find the config
    possible_paths = [
        os.path.join(current_dir, 'config/agents.yaml'),
        os.path.join(current_dir, 'ai_hint_project/config/agents.yaml')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return yaml.safe_load(f)
    return None

agents_config = get_cached_persona_data()

if not agents_config:
    st.error("⚠️ Could not find `config/agents.yaml`. Please check your file structure.")
    st.stop()

persona_by_level, backgrounds, persona_options, persona_avatars = build_persona_data(agents_config)

# Load Crew/AI
try:
    from ai_hint_project.crew import create_crew
except ImportError:
    def create_crew(persona, question):
        return f"🤖 [AI Mock Response] {persona} says: {question}"

# ==========================
# 6. UI LAYOUT
# ==========================

# --- REWARDS CHECK (Toast/Balloons) ---
if st.session_state.show_reward:
    render_reward_popup(st.session_state.show_reward)

# --- SIDEBAR ---
# Use empty dataframe if load_ratings fails (safe fallback)
try:
    historical_df = load_ratings()
except:
    import pandas as pd
    historical_df = pd.DataFrame()

render_sidebar(
    st.session_state.user_progress['level'], 
    st.session_state.user_progress['xp'], 
    st.session_state.user_progress['streak'], 
    persona_avatars, 
    historical_df
)

# --- GAMIFICATION DEBUGGER (Temporary - Remove later) ---
with st.sidebar.expander("🔧 Gamification Debugger"):
    st.write(f"XP: {st.session_state.user_progress['xp']}")
    st.write(f"Level: {st.session_state.user_progress['level']}")
    if st.button("➕ Force 500 XP"):
        from utils.gamification import add_xp
        # This will trigger the Toast + Balloons
        add_xp(st.session_state.user_progress, 500, st.session_state)
        st.rerun()

# --- MAIN HEADER ---
progress = st.session_state.user_progress
render_header(
    progress['level'], 
    progress['xp'], 
    progress['streak'], 
    get_xp_for_level(progress['level']), 
    calculate_xp_progress(progress['xp'], progress['level']), 
    get_level_tier(progress['level'])
)

# --- PERSONA SELECTOR ---
render_persona_selector(
    progress['level'], 
    progress.get('affinity', {}), 
    persona_avatars
)

# --- MAIN CONTENT AREA ---
if st.session_state.current_persona:
    selected_persona = st.session_state.current_persona
    
    if st.session_state.active_page == 'home':
        if st.session_state.active_mode == 'question':
            render_question_mode(selected_persona, persona_avatars, create_crew, progress['level'])
        else:
            render_code_review_mode(selected_persona, persona_avatars, create_crew)
            
    elif st.session_state.active_page == 'analytics':
        render_analytics(historical_df)

# --- FOOTER ---
st.divider()
st.checkbox("📡 Show Analytics Logs", value=True, key="debug_ga_toggle")
st.caption(f"Level {progress['level']} • {progress['streak']} Day Streak 🔥")