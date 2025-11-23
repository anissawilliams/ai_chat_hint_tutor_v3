"""
Question Mode Component - Simplified Conversational Tutor
"""
import re
import streamlit as st
from datetime import datetime
from utils.gamification import add_xp
from utils.storage import save_user_progress
# ✅ CRITICAL FIX: Added save_training_feedback to imports
from utils.data_collection import TutorAnalytics, save_training_feedback


# -----------------------
# State Management
# -----------------------
def _ensure_step_state():
    """Initialize minimal session state"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'user_progress' not in st.session_state:
        st.session_state.user_progress = {'level': 1, 'xp': 0, 'affinity': {}, 'proficiency': 'Beginner'}
    if 'show_rating' not in st.session_state:
        st.session_state.show_rating = False

    if 'attempt_counter' not in st.session_state:
        st.session_state.attempt_counter = 0
    if 'last_interaction_time' not in st.session_state:
        st.session_state.last_interaction_time = datetime.now()


# -----------------------
# Smart Code Validation
# -----------------------
def looks_like_code(text):
    """Check if input appears to be code"""
    code_patterns = ['public', 'private', 'int ', 'string', 'void', 'return', '{', '}', '()', ';', '//']
    return any(pattern in text.lower() for pattern in code_patterns)


def smart_validate_java_code(user_input, conversation_context=""):
    """Smart validator for Java code"""
    code = user_input.lower()
    context_lower = conversation_context.lower()

    # Basic method signature check
    has_method_signature = ('(' in code and ')' in code and
                           any(rt in code for rt in ['int', 'string', 'void', 'boolean', 'double', 'list', 'public', 'private']))

    # --- Scenario 1: Sum/Add methods ---
    if any(word in context_lower for word in ['sum', 'add']):
        has_body = '{' in code and '}' in code
        has_return = 'return' in code
        has_addition = '+' in code

        if has_method_signature and not has_body:
            return (False, "Good signature! Now add the body with curly braces { }.", False)
        if has_method_signature and has_body and not (has_return and has_addition):
            return (False, "Structure looks good! Now add the logic: use '+' to add and 'return' to send it back.", False)
        if has_method_signature and has_body and has_return and has_addition:
            return (True, "Perfect! Your method works correctly.", True)

    # --- Scenario 2: Stream operations ---
    elif any(word in context_lower for word in ['stream', 'filter', 'map', 'collect']):
        has_stream = 'stream()' in code
        has_collect = 'collect' in code

        if has_method_signature and has_stream and has_collect:
            return (True, "Excellent! Your stream implementation looks correct.", True)
        elif has_method_signature:
            return (False, "Good start! Remember to use .stream() to convert the list, then chain your operations.", False)

    # --- Scenario 3: Generic Code Check (Fallback) ---
    elif has_method_signature:
        has_body = '{' in code and '}' in code
        has_return = 'return' in code

        if has_body and has_return:
            return (True, "Nice work! Your method structure looks valid.", True)
        else:
            return (False, "Good signature! Now add the method body logic.", False)

    return (False, "", False)


# -----------------------
# Context Building
# -----------------------
def build_tutor_context(chat_history, persona):
    """Build simple context."""
    conversation = ""
    recent_history = chat_history[-10:]

    for msg in recent_history:
        role = "Student" if msg["role"] == "user" else persona
        conversation += f"{role}: {msg['content']}\n\n"

    context = f"""
    The following is a conversation between a Student and {persona} (Java Tutor).
    
    CONVERSATION HISTORY:
    {conversation}
    
    Student's Last Input: {chat_history[-1]['content']}
    
    Respond as {persona}.
    """
    st.session_state.show_rating = True
    return context


# -----------------------
# Success Handling
# -----------------------
def handle_success(persona_avatars, selected_persona):
    """Handle successful code submission"""
    st.success("✅ Great work! That looks correct.")
    st.balloons()

    add_xp(st.session_state.user_progress, 15, st.session_state)

    # Import locally to avoid circular dependency issues if any
    from utils.gamification import add_affinity
    add_affinity(st.session_state.user_progress, selected_persona, 5, st.session_state)

    save_user_progress(st.session_state.user_progress)

    challenges = [
        "Want to try another? Create a method that finds the **maximum** of two integers.",
        "Nice! Ready for more? Try creating a method that **reverses a String**.",
        "Excellent! Let's level up - create a method that **filters even numbers** from a List.",
    ]
    import random
    next_challenge = random.choice(challenges)
    response = f"Perfect! Your solution works.\n\n{next_challenge}"

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response,
        "avatar": persona_avatars.get(selected_persona, "🤖")
    })


# -----------------------
# Chat Interface
# -----------------------
def render_chat_interface(selected_persona, persona_avatars, create_crew, user_level):
    """Main chat interface with Training UI"""
    _ensure_step_state()
    analytics = TutorAnalytics()

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 💬 Chat with {persona_avatars.get(selected_persona, '🤖')} {selected_persona}")
    with col2:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    st.caption("Ask me anything about Java - I'll guide you through it!")

    # Display chat history
    for i, message in enumerate(st.session_state.chat_history):
        avatar = message.get("avatar", "🧑‍💻" if message["role"] == "user" else "🤖")
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

            # === TRAINING UI ===
            if message["role"] == "assistant":
                with st.expander("🛠️ Teacher Only: Train AI"):
                    critique = st.text_input("Feedback:", key=f"critique_{i}")
                    if st.button("Submit Fix", key=f"btn_train_{i}"):
                        save_training_feedback(
                            persona=selected_persona,
                            bad_response=message["content"],
                            critique=critique
                        )
                        st.success("Feedback saved! The AI will improve.")

    # Chat input
    user_input = st.chat_input("Ask a question or paste your code...")

    if user_input:
        st.session_state.attempt_counter += 1
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "avatar": "🧑‍💻"
        })

        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)

        validation_result = None
        should_celebrate = False

        if looks_like_code(user_input):
            full_conversation = "\n".join([msg['content'] for msg in st.session_state.chat_history])
            is_valid, feedback, should_celebrate = smart_validate_java_code(user_input, full_conversation)

            analytics.track_learning_outcome(
                code_input=user_input,
                is_correct=should_celebrate,
                attempt_number=st.session_state.attempt_counter,
                persona_name=selected_persona
            )

            if should_celebrate:
                st.session_state.attempt_counter = 0
                handle_success(persona_avatars, selected_persona)
                st.rerun()
                return
            elif feedback:
                validation_result = f"\n**Code Feedback**: {feedback}"

        context = build_tutor_context(st.session_state.chat_history, selected_persona)
        if validation_result:
            context += validation_result

        proficiency = st.session_state.user_progress.get('proficiency', 'Beginner')

        with st.chat_message("assistant", avatar=persona_avatars.get(selected_persona, "🤖")):
            with st.spinner(f"{selected_persona} is thinking ({proficiency} Mode)..."):
                response = create_crew(selected_persona, context, proficiency)
                st.markdown(response)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "avatar": persona_avatars.get(selected_persona, "🤖")
                })

                analytics.track_question(question=user_input, response=response, persona=selected_persona)
        st.rerun()


# -----------------------
# Main Render
# -----------------------
def render_question_mode(selected_persona, persona_avatars, create_crew, user_level):
    """Render the chat mode interface"""
    _ensure_step_state()
    analytics = TutorAnalytics()

    st.divider()
    render_chat_interface(selected_persona, persona_avatars, create_crew, user_level)
    analytics.track_click("Chat Mode")

    st.divider()
    if st.button("📝 Give Feedback (Survey)"):
        st.switch_page("pages/Survey.py")