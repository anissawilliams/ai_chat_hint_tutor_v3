"""
Persona selection grid component
"""
import streamlit as st
from utils.personas import PERSONA_UNLOCK_LEVELS

def render_persona_selector(user_level, user_affinity, persona_avatars):
    """Render persona selection grid"""
    st.subheader("🎯 Choose Your Tutor")
    
    cols_per_row = 3
    persona_list = list(PERSONA_UNLOCK_LEVELS.keys())
    
    for i in range(0, len(persona_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(persona_list):
                persona_name = persona_list[i + j]
                unlock_level = PERSONA_UNLOCK_LEVELS[persona_name]
                is_unlocked = unlock_level <= user_level
                affinity = user_affinity.get(persona_name, 0)
                affinity_stars = min(5, affinity // 20)
                
                with col:
                    if is_unlocked:
                        if st.button(
                            f"{persona_avatars[persona_name]} {persona_name}",
                            key=f"persona_{persona_name}",
                            use_container_width=True,
                            type="primary" if st.session_state.current_persona == persona_name else "secondary"
                        ):
                            st.session_state.current_persona = persona_name
                            st.rerun()
                        
                        # Show affinity
                        if affinity > 0:
                            st.markdown(f"""
                            <div style='text-align: center;'>
                                <small>{'⭐' * affinity_stars}{'☆' * (5 - affinity_stars)}</small>
                                <div class='affinity-bar'>
                                    <div class='affinity-fill' style='width: {min(affinity, 100)}%;'></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class='persona-card locked-persona' style='text-align: center; padding: 15px;'>
                            <div style='font-size: 40px;'>{persona_avatars[persona_name]}</div>
                            <div>🔒 Level {unlock_level}</div>
                            <small>{persona_name}</small>
                        </div>
                        """, unsafe_allow_html=True)