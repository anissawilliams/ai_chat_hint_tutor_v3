import streamlit as st
from streamlit_modal import Modal

def render_reward_popup(reward):
    modal = Modal("🎁 Reward Unlocked!", key="reward_modal", max_width="600px")
    modal.open()  # Always open if reward is set

    if modal.is_open():
        with modal.container():
            if reward['type'] == 'level_up':
                st.markdown(f"## 🎉 Level Up!\nYou're now Level {reward['level']}!\nKeep learning to unlock more tutors!")
                st.button("Awesome!", on_click=lambda: close_reward())

            elif reward['type'] == 'streak':
                st.markdown(f"## 🔥 Streak Milestone!\n{reward['days']} Days Strong!\n+20 Bonus XP!")
                st.button("Keep Going!", on_click=lambda: close_reward())

            elif reward['type'] == 'affinity':
                st.markdown(f"## ⭐ Affinity Upgrade!\n{reward['tier']} Tier with {reward['persona']}!\nNew code snippets unlocked!")
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.button("📚 Check Library!", on_click=lambda: check_library())
                with col2:
                    st.button("Continue", on_click=lambda: close_reward())

def close_reward():
    st.session_state.show_reward = None

def check_library():
    st.session_state.show_reward = None
    st.session_state.show_snippets = True