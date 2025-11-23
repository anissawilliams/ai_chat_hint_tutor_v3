"""
Persona selection grid component
Displays all tutors (unlocked) with earned affinity badges.
"""
import streamlit as st
from utils.data_collection import TutorAnalytics
from utils.gamification import get_affinity_tier

def render_persona_selector(user_level, user_affinity, persona_avatars):
    """Render persona selection grid with Affinity Badges"""
    analytics = TutorAnalytics()
    st.subheader("🎯 Choose Your Tutor")

    # 1. Get all personas (No filtering/unlocking)
    persona_list = list(persona_avatars.keys())

    # 2. Create Grid (3 columns)
    cols = st.columns(3)

    for i, persona_name in enumerate(persona_list):
        # Calculate which column this card goes into (0, 1, 2)
        col = cols[i % 3]

        with col:
            # 3. Calculate Badge Status
            # We use the user's affinity score to determine the badge
            current_affinity = user_affinity.get(persona_name, 0)
            tier_name, _ = get_affinity_tier(current_affinity)

            # Map Tier to Icon
            badge_icon = ""
            if tier_name == 'Bronze': badge_icon = "🥉"
            elif tier_name == 'Silver': badge_icon = "🥈"
            elif tier_name == 'Gold': badge_icon = "🥇"
            elif tier_name == 'Platinum': badge_icon = "💎"

            # 4. Determine Button Style
            # Highlight if currently selected
            is_selected = (st.session_state.get('current_persona') == persona_name)
            type_style = "primary" if is_selected else "secondary"

            # 5. Render Button
            # Label format: "🤖 Batman 🥇"
            button_label = f"{persona_avatars.get(persona_name, '🤖')} {persona_name} {badge_icon}"

            if st.button(
                button_label,
                key=f"persona_{persona_name}",
                use_container_width=True,
                type=type_style
            ):
                st.session_state.current_persona = persona_name
                analytics.track_click("Select Persona")
                analytics.track_persona_selection(persona_name)
                st.rerun()

            # 6. Optional: Mini Progress Bar (Only if they have some points but no Platinum yet)
            if 0 < current_affinity < 100:
                st.progress(min(current_affinity, 100) / 100)