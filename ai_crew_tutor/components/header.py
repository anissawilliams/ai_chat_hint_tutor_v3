"""
Header component with level, XP bar, and streak display
"""
import streamlit as st

def render_header(user_level, user_xp, user_streak, next_level_xp, xp_progress, tier):
    """Render the header with XP bar and stats"""
    st.markdown(f"""
    <div class='level-card'>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>
            <div style='display: flex; align-items: center; gap: 20px;'>
                <div style='font-size: 60px;'>{tier['icon']}</div>
                <div>
                    <h1 style='color: white; margin: 0;'>Level {user_level} {tier['name']}</h1>
                    <p style='color: rgba(255,255,255,0.8); margin: 0;'>Java Programming Tutor</p>
                </div>
            </div>
            <div style='display: flex; gap: 30px; align-items: center;'>
                <div style='text-align: center;'>
                    <div class='streak-badge'>
                        🔥 {user_streak}
                    </div>
                    <p style='color: rgba(255,255,255,0.8); margin-top: 5px; font-size: 12px;'>day streak</p>
                </div>
                <div style='text-align: right;'>
                    <p style='color: rgba(255,255,255,0.8); margin: 0; font-size: 14px;'>XP Progress</p>
                    <p style='color: white; margin: 0; font-size: 24px; font-weight: bold;'>{user_xp} / {next_level_xp}</p>
                </div>
            </div>
        </div>
        <div class='xp-bar'>
            <div class='xp-fill' style='width: {xp_progress}%;'></div>
            <div class='xp-text'>{int(xp_progress)}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)