import streamlit as st
import time


def render_reward_popup(reward_data):
    """
    Non-blocking reward notification using Toast + Balloons.
    Safe for Streamlit Cloud.
    """
    if not reward_data:
        return

    # Clear the state immediately so it doesn't loop forever
    st.session_state.show_reward = None

    # 1. Level Up Event
    if reward_data.get('type') == 'level_up':
        level = reward_data.get('level')
        st.toast(f"🎉 LEVEL UP! You are now Level {level}!", icon="🆙")
        st.balloons()

    # 2. Streak Event
    elif reward_data.get('type') == 'streak':
        days = reward_data.get('days')
        st.toast(f"🔥 {days} Day Streak! Keep it up!", icon="🔥")
        if days % 7 == 0:
            st.snow()

    # 3. Affinity Event
    elif reward_data.get('type') == 'affinity':
        persona = reward_data.get('persona')
        tier = reward_data.get('tier')
        st.toast(f"🌟 New Bond: You are now {tier} tier with {persona}!", icon="🤝")