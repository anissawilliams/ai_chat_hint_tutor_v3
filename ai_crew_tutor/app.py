"""
AI Java Tutor Pro - Main Application
Gamified learning experience with persona-based tutoring
"""
import streamlit as st
import sys
import os
import yaml
import traceback
from datetime import datetime

# Setup paths
base_dir = os.path.dirname(__file__)
sys.path.insert(0, base_dir)

# ==========================
# IMPORT UTILITIES
# ==========================
from utils.storage import load_user_progress, save_user_progress, load_ratings, save_rating
from utils.gamification import (
    get_xp_for_level, get_level_tier, get_affinity_tier,
    calculate_xp_progress, add_xp, update_streak, add_affinity
)
from utils.personas import build_persona_data, get_available_personas, PERSONA_UNLOCK_LEVELS
from utils.snippets import CODE_SNIPPETS, get_persona_snippets

# ==========================
# IMPORT COMPONENTS
# ==========================
from components.header import render_header
from components.sidebar import render_sidebar
from components.rewards import render_reward_popup
from components.persona_selector import render_persona_selector
from components.question_mode import render_question_mode
from components.code_review_mode import render_code_review_mode
from components.snippets_library import render_snippets_library
from components.analytics import render_analytics

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(page_title="AI Java Tutor Pro V2_a", page_icon="🧠", layout="wide")

# ==========================
# SESSION STATE INIT
# ==========================
def init_session_state():
    if 'user_progress' not in st.session_state:
        st.session_state.user_progress = load_user_progress()
    if 'current_persona' not in st.session_state:
        st.session_state.current_persona = None
    if 'active_mode' not in st.session_state:
        st.session_state.active_mode = 'question'
    if 'active_page' not in st.session_state:
        st.session_state.active_page = 'home'
    if 'explanation' not in st.session_state:
        st.session_state.explanation = None
    if 'code_review' not in st.session_state:
        st.session_state.code_review = None
    if 'show_reward' not in st.session_state:
        st.session_state.show_reward = None
    if 'show_rating' not in st.session_state:
        st.session_state.show_rating = False
    if 'snippet_to_paste' not in st.session_state:
        st.session_state.snippet_to_paste = None

init_session_state()
update_streak(st.session_state.user_progress, st.session_state)

# ==========================
# LOAD DATA
# ==========================
@st.cache_data(show_spinner=False)
def get_cached_persona_data():
    yaml_path = os.path.join(base_dir, 'ai_hint_project/config/agents.yaml')
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

@st.cache_data(ttl=60)
def load_historical_ratings():
    return load_ratings()

try:
    agents_config = get_cached_persona_data()
    persona_by_level, backgrounds, persona_options, persona_avatars = build_persona_data(agents_config)
except Exception as e:
    st.error(f"⚠️⚠️ Failed to load agents: {e}")
    st.stop()

historical_df = load_historical_ratings()
progress = st.session_state.user_progress
user_level = progress['level']
user_xp = progress['xp']
user_streak = progress['streak']
user_affinity = progress.get('affinity', {})
next_level_xp = get_xp_for_level(user_level)
xp_progress = calculate_xp_progress(user_xp, user_level)
tier = get_level_tier(user_level)

# ==========================
# LOAD AI CREW
# ==========================
try:
    from ai_hint_project.crew import create_crew
    AI_AVAILABLE = True
    print("✅ Successfully imported create_crew")
except ImportError as e:
    st.warning(f"⚠️⚠️ AI crew module not found: {e}")
    AI_AVAILABLE = False
    def create_crew(persona, question):
        return f"[Demo Mode] {persona} would explain: {question[:50]}..."
except Exception as e:
    st.error(f"❌ Error loading AI crew: {e}")
    st.error(f"Full traceback: {traceback.format_exc()}")
    AI_AVAILABLE = False

    def create_crew(persona, question):
        return f"[Demo Mode] {persona} would explain: {question[:50]}..."

# ==========================
# CSS + BACKGROUND
# ==========================
def load_css():
    selected_persona = st.session_state.get("current_persona")
    # Default to Nova's background
    background = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    if selected_persona and selected_persona in backgrounds:
        background = backgrounds[selected_persona]

    st.markdown(f"""
    <style>
    /* Full app background */
    .stApp {{
        background: {background};
        background-attachment: fixed;
        background-size: cover;
        background-repeat: no-repeat;
        min-height: 100vh;
        color: white;
        font-family: 'Segoe UI', sans-serif;
    }}
    /* Dark overlay for readability */
    .stApp::before {{
        content: "";
        position: fixed;
        top:0; left:0; right:0; bottom:0;
        background: rgba(0,0,0,0.4);
        pointer-events: none;
        z-index: -1;
    }}

    /* Compact level card */
    .level-card {{
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
        padding: 12px 15px;
        border-radius: 10px;
        border: 2px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 12px;
        color: white;
        text-shadow: 0 0 5px rgba(0,0,0,0.7);
    }}

    /* XP bar */
    .xp-bar {{
        height: 20px;
        background: rgba(255,255,255,0.15);
        border-radius: 10px;
        overflow: hidden;
        position: relative;
        width: 100%;
    }}
    .xp-fill {{
        height: 100%;
        background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%);
        width: 0;
        transition: width 1s ease;
    }}
    .xp-text {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-weight: bold;
        font-size: 12px;
        color: white;
        text-shadow: 0 0 6px rgba(0,0,0,0.7);
    }}

    /* Streak badge pulse */
    .streak-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 6px 12px;
        border-radius: 12px;
        font-size: 16px;
        font-weight: bold;
        color: white;
        text-shadow: 0 0 3px rgba(0,0,0,0.7);
        animation: pulse 1.2s infinite;
    }}
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.08); }}
        100% {{ transform: scale(1); }}
    }}

    /* Compact persona cards in grid */
    .persona-card {{
        background: rgba(0,0,0,0.5);
        color: white;
        padding: 8px;
        border-radius: 8px;
        margin: 3px;
        transition: all 0.3s;
        border: 2px solid rgba(255,255,255,0.3);
        backdrop-filter: blur(10px);
        text-align: center;
        text-shadow: 0 0 3px rgba(0,0,0,0.7);
        cursor: pointer;
        min-height: 70px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    .persona-card:hover {{ 
        transform: translateY(-3px);
        border-color: rgba(255,255,255,0.6);
        box-shadow: 0 5px 20px rgba(0,0,0,0.3);
    }}
    .locked-persona {{ 
        opacity: 0.35; 
        filter: grayscale(100%);
        cursor: not-allowed;
    }}
    .locked-persona:hover {{
        transform: none;
    }}
    .persona-avatar {{
        font-size: 28px;
        margin-bottom: 3px;
    }}
    .persona-name {{
        font-size: 12px;
        font-weight: bold;
        margin: 2px 0;
        line-height: 1.2;
    }}
    .persona-level {{
        font-size: 10px;
        opacity: 0.7;
    }}
    
    /* App title */
    .app-title {{
        text-align: center;
        padding: 20px 0 10px 0;
        margin: 0;
    }}
    .app-title h1 {{
        font-size: 48px;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        letter-spacing: 1px;
    }}
    .app-title p {{
        font-size: 18px;
        color: rgba(255,255,255,0.9);
        margin: 5px 0 0 0;
        text-shadow: 0 0 10px rgba(0,0,0,0.7);
    }}

    /* Affinity bars */
    .affinity-bar {{ 
        height: 6px; 
        background: rgba(255,255,255,0.3); 
        border-radius: 3px; 
        overflow: hidden; 
        margin-top: 5px;
        width: 100%;
    }}
    .affinity-fill {{ 
        height: 100%; 
        background: linear-gradient(90deg, #ffd93d 0%, #f5576c 100%); 
        transition: width 0.8s ease; 
    }}

    /* Reward popup */
    .reward-popup {{
        position: fixed; top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px; border-radius: 20px;
        box-shadow: 0 10px 50px rgba(0,0,0,0.5);
        z-index: 1000; text-align: center;
        animation: bounceIn 0.5s;
        color: white; text-shadow: 0 0 5px rgba(0,0,0,0.7);
    }}
    @keyframes bounceIn {{
        0% {{ transform: translate(-50%, -50%) scale(0.3); }}
        50% {{ transform: translate(-50%, -50%) scale(1.05); }}
        100% {{ transform: translate(-50%, -50%) scale(1); }}
    }}

    /* Persona selector container */
    .persona-selector {{
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(12px);
        padding: 15px;
        border-radius: 12px;
        border: 2px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 15px;
    }}

    /* Compact header text */
    .level-card h1 {{
        font-size: 22px;
        margin: 0 0 8px 0;
    }}
    .level-card h3 {{
        font-size: 16px;
        margin: 5px 0;
    }}
    
    /* Button text visibility fix */
    .stButton > button {{
        color: white !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.5) !important;
        border: 2px solid rgba(255,255,255,0.3) !important;
        background: rgba(0,0,0,0.4) !important;
        backdrop-filter: blur(10px) !important;
    }}
    .stButton > button:hover {{
        border-color: rgba(255,255,255,0.6) !important;
        background: rgba(255,255,255,0.1) !important;
        transform: translateY(-2px);
    }}
    /* Radio option container */
    div[data-baseweb="radio"] {{
        background: rgba(0, 0, 0, 0.4);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        border: 2px solid rgba(255, 255, 255, 0.2);
    }}

/* Radio label text */
    div[data-baseweb="radio"] label {{
        color: white !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.7) !important;
    }}


    /* Radio button text visibility */
    .stRadio label {{
        color: white !important;
        font-weight: 500 !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.7) !important;
        background: rgba(0,0,0,0.4); /* adds contrast */
        padding: 6px 12px;
        border-radius: 8px;
        margin-bottom: 4px;
    }}
    
    /* Selectbox text visibility */
    .stSelectbox label {{
        color: white !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.7) !important;
    }}
    
    /* Text input labels */
    .stTextArea label, .stTextInput label {{
        color: white !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.7) !important;
    }}
    </style>

    """, unsafe_allow_html=True)
load_css()

# ==========================
# REWARD POPUP
# ==========================
if st.session_state.show_reward:
    render_reward_popup(st.session_state.show_reward)
    if st.session_state.show_reward:
        st.balloons()

# ==========================
# SIDEBAR
# ==========================
render_sidebar(user_level, user_xp, user_streak, persona_avatars, historical_df)

# ==========================
# MAIN CONTENT
# ==========================

# Add App Title
st.markdown("""
<div class="app-title">
    <h1>🧠 AI Java Tutor Pro</h1>
    <p>Master Java with Personalized AI Mentors</p>
</div>
""", unsafe_allow_html=True)

# Header FIRST (compact level/XP display above personas)
render_header(user_level, user_xp, user_streak, next_level_xp, xp_progress, tier)

# Persona selector SECOND (background changes on selection)
render_persona_selector(user_level, user_affinity, persona_avatars)

# Content appears after persona selected
if st.session_state.current_persona:
    selected_persona = st.session_state.current_persona

    # Active page content
    if st.session_state.active_page == 'home':
        if st.session_state.active_mode == 'question':
            render_question_mode(selected_persona, persona_avatars, create_crew, user_level)
        else:
            render_code_review_mode(selected_persona, persona_avatars, create_crew)

    elif st.session_state.active_page == 'analytics':
        render_analytics(historical_df)

    elif st.session_state.active_page == 'snippets':
        render_snippets_library(user_level, user_affinity, persona_avatars,
                                get_available_personas, get_affinity_tier)

# ==========================
# FOOTER
# ==========================
st.divider()
st.caption(f"🧠 AI Java Tutor Pro | Level {user_level} • {user_streak} day streak 🔥")