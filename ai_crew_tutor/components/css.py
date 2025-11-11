# ==========================
# CSS + BACKGROUND
# ==========================
import streamlit as st
def load_css():
    selected_persona = st.session_state.get("current_persona")
    # Default to Nova's background
    background = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    #if selected_persona and selected_persona in backgrounds:
     #   background = backgrounds[selected_persona]

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
        z-index: 9999; text-align: center;
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