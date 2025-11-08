"""
Reward popup component for level ups, streaks, and affinity
"""
import streamlit as st

def render_reward_popup(reward):
    """Render reward popup based on reward type"""
    if reward['type'] == 'level_up':
        st.markdown(f"""
        <div class='reward-popup'>
            <div style='font-size: 80px;'>🎉</div>
            <h1 style='color: white; margin: 20px 0;'>Level Up!</h1>
            <h2 style='color: white;'>You're now Level {reward['level']}!</h2>
            <p style='color: white; margin-top: 20px;'>Keep learning to unlock more tutors!</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Awesome!", key="close_reward", use_container_width=True):
                st.session_state.show_reward = None
                st.rerun()
        with col2:
            if st.button("✕", key="x_close_reward", use_container_width=True):
                st.session_state.show_reward = None
                st.rerun()

    elif reward['type'] == 'streak':
        st.markdown(f"""
        <div class='reward-popup'>
            <div style='font-size: 80px;'>🔥</div>
            <h1 style='color: white; margin: 20px 0;'>Streak Milestone!</h1>
            <h2 style='color: white;'>{reward['days']} Days Strong!</h2>
            <p style='color: white; margin-top: 20px;'>+20 Bonus XP!</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Keep Going!", key="close_streak", use_container_width=True):
                st.session_state.show_reward = None
                st.rerun()
        with col2:
            if st.button("✕", key="x_close_streak", use_container_width=True):
                st.session_state.show_reward = None
                st.rerun()


    elif reward['type'] == 'affinity':

        st.markdown(f"""
        <div class='reward-popup' style='max-height: 80vh; overflow-y: auto; padding: 40px;'>
            <div style='font-size: 80px;'>⭐</div>
            <h1 style='color: white; margin: 20px 0;'>Affinity Upgrade!</h1>
            <h2 style='color: white;'>{reward['tier']} Tier with {reward['persona']}!</h2>
            <p style='color: white; margin-top: 20px; margin-bottom: 30px;'>New code snippets unlocked!</p>
        </div>
        """, unsafe_allow_html=True)

        # Add some spacing
        st.markdown("<br>", unsafe_allow_html=True)
        # Create buttons in a clear, visible row
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            if st.button("📚 Check Library!", key="check_library", use_container_width=True, type="primary"):
                st.session_state.show_reward = None
                st.session_state.show_snippets = True
                st.rerun()

        with col2:
            if st.button("Continue", key="close_affinity", use_container_width=True):
                st.session_state.show_reward = None
                st.rerun()

        with col3:
            if st.button("✕", key="x_close_affinity", use_container_width=True):
                st.session_state.show_reward = None
                st.rerun()