"""
Sidebar component with stats and navigation (Streamlit pages compatible)
"""
import streamlit as st
from utils.personas import PERSONA_UNLOCK_LEVELS, get_next_unlock

from ai_crew_tutor.utils.storage import save_user_progress


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

        # ... existing sidebar code ...


        st.subheader("⚙️ Learning Settings")

        # 1. Get current value from session state (default to Beginner)
        current_proficiency = st.session_state.user_progress.get('proficiency', 'Beginner')

        # 2. The Radio Button
        selected_proficiency = st.radio(
            "Your Java Experience:",
            options=["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(current_proficiency),
            help="This changes how much the AI helps you. Beginner = more hints. Advanced = direct code reviews."
        )

        # 3. Save if changed
        if selected_proficiency != current_proficiency:
            st.session_state.user_progress['proficiency'] = selected_proficiency
            # Save to Firebase immediately
            save_user_progress(st.session_state.user_progress)
            st.rerun()  # Refresh so the AI picks up the new setting immediately

        # ... existing footer code ...
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

        # Quick stats from history
        # =================
        if not historical_df.empty:
            st.header("📈 All-Time Stats")
            avg_rating = historical_df['clarity'].mean() if 'clarity' in historical_df.columns else 0
            st.metric("Avg Clarity", f"{avg_rating:.1f}⭐")
            st.metric("Total Questions", len(historical_df))
