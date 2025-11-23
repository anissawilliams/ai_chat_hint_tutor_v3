"""
Sidebar component with stats and navigation (Streamlit pages compatible)
"""
import streamlit as st
from utils.personas import PERSONA_UNLOCK_LEVELS, get_next_unlock
from utils.storage import save_user_progress
# ✅ NEW: Import Analytics
from utils.data_collection import TutorAnalytics

def navigate_to(page_name: str):
    """Set query params to navigate to a page"""
    st.experimental_set_query_params(page=page_name)

def render_sidebar(user_level, user_xp, user_streak, persona_avatars, historical_df):
    """Render the sidebar with stats, controls, and page navigation"""

    # ✅ Initialize Analytics
    analytics = TutorAnalytics()

    with st.sidebar:
        st.title("⚙️ Control Center")

        # =================
        # 1. User Stats
        # =================
        st.header("📊 Your Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Level", user_level)
            st.metric("Streak", f"{user_streak} 🔥")
        with col2:
            st.metric("XP", user_xp)
            # Calculate unlocked count safely
            unlocked_count = sum(1 for p in PERSONA_UNLOCK_LEVELS if PERSONA_UNLOCK_LEVELS[p] <= user_level)
            st.metric("Tutors", f"{unlocked_count}/{len(PERSONA_UNLOCK_LEVELS)}")

        st.divider()

        # ... inside render_sidebar ...

        # =================
        # 2. Learning Settings (Sleek Version)
        # =================
        st.subheader("⚙️ Learning Settings")

        if 'user_progress' not in st.session_state:
            st.session_state.user_progress = {}

        current_proficiency = st.session_state.user_progress.get('proficiency', 'Beginner')

        # OPTIONS:
        # 1. st.pills is the modern "Chip" look (Streamlit 1.40+)
        # 2. If that fails, use st.radio(..., horizontal=True)
        try:
            selected_proficiency = st.pills(
                "Teaching Style",
                options=["Beginner", "Intermediate", "Advanced"],
                default=current_proficiency,
                selection_mode="single",
                key="prof_selector"
            )
        except AttributeError:
            # Fallback for older Streamlit versions
            selected_proficiency = st.radio(
                "Teaching Style",
                options=["Beginner", "Intermediate", "Advanced"],
                index=["Beginner", "Intermediate", "Advanced"].index(current_proficiency),
                horizontal=True,  # <--- This fixes the "funky" vertical look
                key="prof_selector"
            )

        # Logic: Save & Track if changed
        # Note: st.pills returns None if deselected, so we handle that
        if selected_proficiency and selected_proficiency != current_proficiency:
            st.session_state.user_progress['proficiency'] = selected_proficiency
            save_user_progress(st.session_state.user_progress)
            analytics.track_click(f"Changed Proficiency to {selected_proficiency}", "settings_change")
            st.rerun()

        # Helper text to explain the mode
        mode_explanations = {
            "Beginner": "🌱 Step-by-step guidance. More hints.",
            "Intermediate": "🛠️ Logic focus. Socratic questioning.",
            "Advanced": "🚀 Code reviews. Efficiency focus."
        }
        st.caption(mode_explanations.get(selected_proficiency, ""))

        st.divider()

        # =================
        # 3. Unlock Progress
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

        # =================
        # 4. History Stats
        # =================
        if not historical_df.empty:
            st.header("📈 All-Time Stats")
            # Safe check if 'clarity' exists in your historical data
            if 'clarity' in historical_df.columns:
                avg_rating = historical_df['clarity'].mean()
                st.metric("Avg Clarity", f"{avg_rating:.1f}⭐")
            st.metric("Total Questions", len(historical_df))