"""
Code review mode component
"""
import streamlit as st
from utils.gamification import add_xp, add_affinity
from utils.storage import save_user_progress

def render_code_review_mode(selected_persona, persona_avatars, create_crew):
    """Render code review interface"""
    st.subheader("📝 Code Review")
    st.caption(f"{persona_avatars[selected_persona]} {selected_persona} will review your Java code")
    
    user_code = st.text_area(
        "Paste your Java code here:",
        height=250,
        placeholder="""public class Example {
    public static void main(String[] args) {
        // Your code here
    }
}""",
        key="code_input"
    )
    
    if st.button("🔍 Get Code Review (+15 XP)", type="primary", use_container_width=True):
        if not user_code.strip():
            st.warning("⚠️ Please paste some code first!")
        else:
            try:
                with st.spinner(f"{persona_avatars[selected_persona]} Analyzing your code..."):
                    review_prompt = f"Review this Java code and provide feedback:\n\n{user_code}"
                    result = create_crew(selected_persona, review_prompt)
                
                st.session_state.code_review = result
                
                # Award XP and affinity
                leveled_up = add_xp(st.session_state.user_progress, 15, st.session_state)
                add_affinity(st.session_state.user_progress, selected_persona, 15, st.session_state)
                
                st.success("✅ Code review complete! +15 XP, +15 Affinity")
                if leveled_up:
                    save_user_progress(st.session_state.user_progress)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Display code review
    if st.session_state.code_review:
        st.divider()
        st.markdown("### 🔍 Code Review Results")
        st.markdown(f"""
        <div class='code-review-box'>
            {st.session_state.code_review}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear Review", use_container_width=True):
            st.session_state.code_review = None
            st.rerun()