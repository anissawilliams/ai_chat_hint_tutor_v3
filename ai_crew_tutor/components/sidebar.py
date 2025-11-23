"""
Sidebar component with stats, learning settings, and badge tracking.
"""
import streamlit as st
from utils.storage import save_user_progress
from utils.data_collection import TutorAnalytics
from utils.gamification import get_affinity_tier

def render_sidebar(user_level, user_xp, user_streak, persona_avatars, historical_df):
    """
    Render the sidebar with User Profile, Stats, Learning Settings, and Badges.
    """
    # Initialize Analytics
    analytics = TutorAnalytics()

    with st.sidebar:
        # ---------------------------------------------------------
        # 1. USER PROFILE HEADER
        # ---------------------------------------------------------
        username = st.session_state.get('username', 'Student')

        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="font-size: 3rem;">🎓</div>
            <h3>{username}</h3>
            <div style="padding: 5px 10px; border-radius: 15px; display: inline-block;">
                <small>Level {user_level}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ---------------------------------------------------------
        # 2. GAMIFICATION STATS
        # ---------------------------------------------------------
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔥 Streak", f"{user_streak} Days")
        with col2:
            st.metric("✨ XP", user_xp)

        # Tutors Count (Always Full since we unlocked everyone)
        total_tutors = len(persona_avatars)
        st.caption(f"Tutors Available: {total_tutors}/{total_tutors}")

        st.divider()

        # ---------------------------------------------------------
        # 3. ⚙️ LEARNING SETTINGS (Sleek Selector)
        # ---------------------------------------------------------
        st.subheader("⚙️ Learning Mode")

        if 'user_progress' not in st.session_state:
             st.session_state.user_progress = {}

        current_proficiency = st.session_state.user_progress.get('proficiency', 'Beginner')

        # Try to use st.pills (Streamlit 1.40+), fallback to radio
        try:
            selected_proficiency = st.pills(
                "Teaching Style",
                options=["Beginner", "Intermediate", "Advanced"],
                default=current_proficiency,
                selection_mode="single",
                key="prof_selector"
            )
        except AttributeError:
            # Fallback for older versions
            selected_proficiency = st.radio(
                "Teaching Style",
                options=["Beginner", "Intermediate", "Advanced"],
                index=["Beginner", "Intermediate", "Advanced"].index(current_proficiency),
                horizontal=True,
                key="prof_selector"
            )

        # Logic: Save & Track if changed
        # Note: st.pills returns None if deselected, so we check availability
        if selected_proficiency and selected_proficiency != current_proficiency:
            # 1. Update State
            st.session_state.user_progress['proficiency'] = selected_proficiency

            # 2. Save to Firebase
            save_user_progress(st.session_state.user_progress)

            # 3. Track Event
            analytics.track_click(f"Changed Proficiency to {selected_proficiency}", "settings_change")

            # 4. Refresh
            st.rerun()

        # Mode Explanation
        mode_icons = {"Beginner": "🌱", "Intermediate": "🛠️", "Advanced": "🚀"}
        st.caption(f"{mode_icons.get(current_proficiency, '')} {current_proficiency} Mode active")

        st.divider()

        # ---------------------------------------------------------
        # 4. 🏆 BADGES (Replaces Unlock Progress)
        # ---------------------------------------------------------
        st.subheader("🏆 Your Badges")

        # Calculate Medal Counts based on Affinity
        affinity_map = st.session_state.user_progress.get('affinity', {})
        medals = {'Gold': 0, 'Silver': 0, 'Bronze': 0}

        for _, points in affinity_map.items():
            tier, _ = get_affinity_tier(points)
            if tier in medals:
                medals[tier] += 1

        b_col1, b_col2, b_col3 = st.columns(3)
        b_col1.metric("🥇", medals['Gold'], help="Gold Badges (75+ Affinity)")
        b_col2.metric("🥈", medals['Silver'], help="Silver Badges (50+ Affinity)")
        b_col3.metric("🥉", medals['Bronze'], help="Bronze Badges (25+ Affinity)")

        st.divider()

        # ---------------------------------------------------------
        # 5. RECENT HISTORY
        # ---------------------------------------------------------
        if historical_df is not None and not historical_df.empty:
            st.subheader("📜 Recent History")

            # Calculate Avg Clarity safely
            if 'rating' in historical_df.columns:
                # Ensure numeric
                numeric_ratings = pd.to_numeric(historical_df['rating'], errors='coerce')
                avg_rating = numeric_ratings.mean()
                if not pd.isna(avg_rating):
                    st.metric("Avg Session Rating", f"{avg_rating:.1f}⭐")

            st.caption(f"Total Interactions: {len(historical_df)}")

            # Show last 3 sessions
            recent = historical_df.tail(3).iloc[::-1]
            for _, row in recent.iterrows():
                persona = row.get('persona', 'Unknown')
                avatar = persona_avatars.get(persona, '🤖')
                st.markdown(f"<small>{avatar} {persona}</small>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # 6. LOGOUT
        # ---------------------------------------------------------
        st.divider()
        if st.button("🚪 Log Out", use_container_width=True):
            from utils.auth import logout
            logout()