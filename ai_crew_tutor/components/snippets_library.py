"""
Code snippets library component
"""
import streamlit as st
from utils.snippets import CODE_SNIPPETS, get_persona_snippets
from utils.gamification import get_affinity_tier
from utils.personas import get_available_personas

def render_snippets_library(user_level, user_affinity):
    """Render code snippets library page"""
    st.header("💾 Code Snippets Library")
    st.markdown("Unlock code snippets by building affinity with your tutors!")
    
    available_personas = get_available_personas(user_level)
    
    for persona_name in available_personas:
        if persona_name not in CODE_SNIPPETS:
            continue
        
        persona_data = CODE_SNIPPETS[persona_name]
        affinity = user_affinity.get(persona_name, 0)
        tier_name, tier_level = get_affinity_tier(affinity)
        
        with st.expander(f"{persona_data['icon']} {persona_data['name']} - {tier_name} Tier ({affinity} affinity)", expanded=False):
            st.progress(min(affinity / 100, 1.0))
            
            if affinity == 0:
                st.info(f"💡 Ask questions with {persona_name} to unlock their snippets!")
            
            for snippet in persona_data['snippets']:
                is_unlocked = affinity >= snippet['tier']
                
                if is_unlocked:
                    st.markdown(f"### ✅ {snippet['title']}")
                    st.caption(snippet['description'])
                    st.code(snippet['code'], language='java')
                else:
                    st.markdown(f"""
                    <div class='snippet-card snippet-locked'>
                        <h4>🔒 {snippet['title']}</h4>
                        <p>{snippet['description']}</p>
                        <small>Unlock at {snippet['tier']} affinity</small>
                    </div>
                    """, unsafe_allow_html=True)
