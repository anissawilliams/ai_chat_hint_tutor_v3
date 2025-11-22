"""
Sidebar component with stats and navigation (Streamlit pages compatible)
"""
import streamlit as st
from utils.personas import PERSONA_UNLOCK_LEVELS, get_next_unlock

def navigate_to(page_name: str):
    """Set query params to navigate to a page"""
    st.experimental_set_query_params(page=page_name)

def render_sidebar(user_level, user_xp, user_streak, persona_avatars, historical_df):
    """Render the sidebar with stats, controls, and page navigation"""
    with st.sidebar:
        st.title("⚙️ Control Center")

        # =================
        # User Stats
        # =================
        st.header("📊 Your Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Level", user_level)
            st.metric("Streak", f"{user_streak} 🔥")
        with col2:
            st.metric("XP", user_xp)
            unlocked_count = sum(1 for p in PERSONA_UNLOCK_LEVELS if PERSONA_UNLOCK_LEVELS[p] <= user_level)
            st.metric("Tutors", f"{unlocked_count}/{len(PERSONA_UNLOCK_LEVELS)}")

        st.divider()



        # =================
        # Unlock Progress
        # =================
        st.header("🔓 Unlock Progress")
        next_persona, next_level = get_next_unlock(user_level)

        if next_persona:
            levels_needed = next_level - user_level
            st.info(f"**Next unlock:** {persona_avatars.get(next_persona, '🧠')} {next_persona}")
            st.caption(f"Reach level {next_level} ({levels_needed} levels to go!)")
        else:
            st.success("🎉 All tutors unlocked!")

        st.divider()
        # Add this inside render_sidebar or temporary in app.py
        with st.sidebar.expander("🔧 Gamification Debugger"):
            st.write(f"Current XP: {st.session_state.user_progress['xp']}")
            st.write(f"Current Level: {st.session_state.user_progress['level']}")

            if st.button("➕ Force Add 500 XP"):
                # Import locally to ensure we have access
                from utils.gamification import add_xp
                from utils.storage import save_user_progress

                # Force add XP
                add_xp(st.session_state.user_progress, 500, st.session_state)
                save_user_progress(st.session_state.user_progress)
                st.success("Added 500 XP! Refreshing...")
                st.rerun()
        # =================
        # Quick stats from history
        # =================
        if not historical_df.empty:
            st.header("📈 All-Time Stats")
            avg_rating = historical_df['clarity'].mean() if 'clarity' in historical_df.columns else 0
            st.metric("Avg Clarity", f"{avg_rating:.1f}⭐")
            st.metric("Total Questions", len(historical_df))
