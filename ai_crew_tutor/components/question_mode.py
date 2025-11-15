"""
Question Mode Component with Efficient Guided Learning
Provides scaffolded guidance in fewer interactions
"""
import re
import random
import streamlit as st
from utils.gamification import add_xp, add_affinity
from utils.storage import save_user_progress, save_rating
from utils.data_collection import TutorAnalytics
from utils.java_code_validator import (
    java_validator_factory,
    signature_check,
    content_check
)


# -----------------------
# Helpers and state init
# -----------------------
def _ensure_step_state():
    if 'tutor_step' not in st.session_state:
        st.session_state.tutor_step = {
            'step_id': 0,
            'attempts': 0,
            'last_validation_result': None
        }
    if 'show_rating' not in st.session_state:
        st.session_state.show_rating = False
    if 'user_progress' not in st.session_state:
        st.session_state.user_progress = {'level': 1, 'xp': 0, 'affinity': {}}
    if 'chat_mode' not in st.session_state:
        st.session_state.chat_mode = True


def build_efficient_chat_context(chat_history, persona, step_info, validation_result=None):
    """
    Build context that includes FULL conversation history so the LLM can see what it already said.
    This prevents repetition and allows progressive scaffolding.
    """
    attempts = step_info['attempts']

    # Build the full conversation for context
    conversation = ""
    for msg in chat_history:
        role = "Student" if msg["role"] == "user" else persona
        conversation += f"{role}: {msg['content']}\n\n"

    # Build validation feedback if available
    feedback_section = ""
    if validation_result:
        is_correct, msg = validation_result
        if not is_correct:
            feedback_section = f"\n**Validation Result**: {msg}"

    # Determine what guidance level to suggest based on attempts
    if attempts == 0:
        guidance_hint = "Start with high-level structure and one concrete example."
    elif attempts == 1:
        guidance_hint = "They've tried once. Give more specific hints: method signatures, key APIs, or a small code snippet."
    else:
        guidance_hint = "They're stuck. Provide a working skeleton with blanks or show the solution with explanations."

    context = f"""You are {persona}, an efficient Java tutor. You can see the full conversation history below.

CONVERSATION SO FAR:
{conversation}

CURRENT SITUATION:
- This is attempt #{attempts + 1} at the current step
{feedback_section}

YOUR TASK:
- Review what you've already told them (avoid repeating the same advice)
- Look at their latest attempt and give SPECIFIC feedback on what's wrong/missing
- {guidance_hint}
- Keep response under 200 words but actionable
- End with ONE clear directive: "Now try: [specific action]"

IMPORTANT: Don't repeat things you already said. Build on the conversation progressively.

Respond as {persona}:"""

    return context


# -----------------------
# Renderers
# -----------------------
def render_question_mode(selected_persona, persona_avatars, create_crew, user_level):
    """Render the question/chat mode interface"""
    _ensure_step_state()
    analytics = TutorAnalytics()

    st.divider()
    render_chat_interface(selected_persona, persona_avatars, create_crew, user_level)
    analytics.track_click("Chat Mode")
    show_rating(selected_persona)


def render_chat_interface(selected_persona, persona_avatars, create_crew, user_level):
    """Render efficient chat-based guided learning"""
    _ensure_step_state()
    analytics = TutorAnalytics()

    st.markdown(f"### 💬 Chat with {persona_avatars.get(selected_persona, '🤖')} {selected_persona}")
    st.caption("Describe what you're trying to build - I'll give you structured guidance!")

    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Configure validator for current exercise
    if 'current_expected_pattern' not in st.session_state:
        st.session_state['current_expected_pattern'] = java_validator_factory(
            method_name="doubleNumbers",
            return_type="List<Integer>",
            param_types=["List<Integer>"],
            required_tokens=["stream", "map"],
            use_ast_check=False
        )

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"],
                             avatar=message.get("avatar", "🧑‍💻" if message["role"] == "user" else "🤖")):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input("Describe what you want to build or paste your code...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input, "avatar": "🧑‍💻"})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)

        # Run validator
        validator = st.session_state.get('current_expected_pattern')
        validation_result = None

        if validator and callable(validator):
            res = validator(user_input)
            if isinstance(res, tuple):
                ok, msg = res
            else:
                ok, msg = bool(res), "Good attempt, but not quite right yet."

            validation_result = (ok, msg)
            st.session_state.tutor_step['last_validation_result'] = validation_result

            if ok:
                st.success("✅ Correct! Great work.")
                st.session_state.tutor_step['attempts'] = 0
                st.session_state.tutor_step['step_id'] += 1
                st.session_state.chat_history = []  # Reset for next problem
                add_xp(st.session_state.user_progress, 15, st.session_state)
                save_user_progress(st.session_state.user_progress)

                # Provide brief next step
                response = f"Perfect! Your solution works correctly. {get_next_challenge(st.session_state.tutor_step['step_id'])}"

                with st.chat_message("assistant", avatar=persona_avatars.get(selected_persona, "🤖")):
                    st.markdown(response)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response,
                        "avatar": persona_avatars.get(selected_persona, "🤖")
                    })

                st.rerun()
                return

        # Build context with FULL conversation history
        context = build_efficient_chat_context(
            st.session_state.chat_history,
            selected_persona,
            st.session_state.tutor_step,
            validation_result
        )

        with st.chat_message("assistant", avatar=persona_avatars.get(selected_persona, "🤖")):
            with st.spinner(f"{selected_persona} is thinking..."):
                response = create_crew(selected_persona, context)
                st.markdown(response)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "avatar": persona_avatars.get(selected_persona, "🤖")
                })
                analytics.track_question(question=user_input, response=response, persona=selected_persona)

        # Increment attempts for next round
        st.session_state.tutor_step['attempts'] += 1
        st.rerun()


def get_next_challenge(step_id):
    """Provide next learning challenge based on completed step"""
    challenges = {
        1: "Ready for the next challenge? Try creating a method that filters even numbers from a list.",
        2: "Nice! Now let's tackle error handling. Can you add validation for null/empty lists?",
        3: "Excellent progress! Want to combine operations? Try filter + map in one stream pipeline."
    }
    return challenges.get(step_id, "Want to try another Java concept?")


def show_rating(selected_persona):
    """Rating system with slider"""
    _ensure_step_state()
    analytics = TutorAnalytics()

    if st.session_state.show_rating:
        st.markdown("#### How helpful was this session?")

        rating = st.slider(
            "Rate the session",
            min_value=1,
            max_value=5,
            value=3,
            step=1,
            format="%d ⭐",
            key="rating_slider"
        )

        if st.button("Submit Rating", type="primary"):
            save_rating(selected_persona, rating)
            st.session_state.show_rating = False
            analytics.track_click("Rate")
            st.success("Thanks for your feedback!")
            st.rerun()