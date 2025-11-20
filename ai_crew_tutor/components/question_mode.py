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
    Build context that includes FULL conversation history and clear scaffolding rules.
    Prevents giving away answers too early while keeping interactions efficient.
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
        if is_correct:
            feedback_section = f"\n**✅ VALIDATION: CODE IS CORRECT - Student solved it! Congratulate and move to next challenge.**"
        else:
            feedback_section = f"\n**❌ VALIDATION: Code has issues - {msg}**\n**Continue guiding based on attempt #{attempts + 1} strategy below.**"

    # Progressive scaffolding strategy based on attempts
    if attempts == 0:
        strategy = """FIRST INTERACTION - Set Direction:
- Acknowledge what they want to build
- Break it into 2-3 concrete sub-steps (e.g., "1. Create method signature, 2. Use stream API, 3. Collect results")
- Give ONE small example for context (e.g., "Like how .filter() works: list.stream().filter(x -> x > 0)")
- Ask them to try the first step (be specific: "Start with the method signature - what should it accept and return?")"""
    elif attempts == 1:
        strategy = """SECOND INTERACTION - Targeted Hints:
- Point out specifically what's missing or wrong in their attempt
- Provide API hints (e.g., "You'll need .map() to transform each element")
- Show structure without solution (e.g., "The pattern is: stream() -> transform -> collect()")
- Ask them to try incorporating this specific hint"""
    elif attempts == 2:
        strategy = """THIRD INTERACTION - Partial Code:
- Give a partial implementation with blanks (e.g., "public List<Integer> transform(List<Integer> nums) { return nums.stream().map(____ -> ____ * 2).collect(____); }")
- Explain what each blank should be
- Ask them to fill in the blanks and test"""
    elif attempts == 3:
        strategy = """FOURTH INTERACTION - Working Solution with Explanation:
- Provide working code with detailed line-by-line explanation
- Explain WHY each part works
- Ask them to run it and then modify it slightly (e.g., "Now change it to triple the numbers instead of double")
- Keep encouraging them to try the variation"""
    else:
        strategy = """FIFTH+ INTERACTION - Keep Supporting:
- They have the solution now, so help them understand it better or debug their variation
- Ask what specific part is confusing
- Provide more examples or edge cases to try
- Suggest extensions: "What if the list had null values? How would you handle that?"
- NEVER give up - always find a new angle to explore or variation to try"""

    context = f"""You are {persona}, an efficient Java tutor who guides students through problems progressively.

CONVERSATION SO FAR:
{conversation}

CURRENT SITUATION:
- This is attempt #{attempts + 1} at the current step
{feedback_section}

YOUR SCAFFOLDING STRATEGY FOR THIS ATTEMPT:
{strategy}

CRITICAL RULES:
1. READ the conversation above - the student just responded with: "{chat_history[-1]['content']}"
2. If validation shows ✅ CORRECT: STOP giving hints, congratulate them, acknowledge success
3. If validation shows ❌ INCORRECT or no validation: Follow the scaffolding strategy above
4. NEVER repeat yourself - review what you said in previous messages
5. Keep responses under 150 words
6. Always end with a specific question or directive
7. Use code blocks for any code examples

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

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 💬 Chat with {persona_avatars.get(selected_persona, '🤖')} {selected_persona}")
    with col2:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.session_state.tutor_step = {
                'step_id': 0,
                'attempts': 0,
                'last_validation_result': None
            }
            st.rerun()

    st.caption("Describe what you're trying to build - I'll guide you through it step-by-step!")

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

        # Run validator if it looks like code
        validator = st.session_state.get('current_expected_pattern')
        validation_result = None

        # Only validate if input looks like code (contains common code patterns)
        # Only validate if input looks like code (contains common code patterns)
        looks_like_code = any(pattern in user_input.lower() for pattern in
                              ['public', 'private', 'return', 'void', '{', 'list', 'stream', 'int ', '=', ';'])

        if validator and callable(validator) and looks_like_code:
            res = validator(user_input)
            if isinstance(res, tuple):
                ok, msg = res
            else:
                ok, msg = bool(res), "Good attempt, but not quite right yet."

            validation_result = (ok, msg)
            st.session_state.tutor_step['last_validation_result'] = validation_result

            if ok:
                # Success! Celebrate and move on
                st.success("✅ Correct! Great work.")
                st.session_state.tutor_step['attempts'] = 0
                st.session_state.tutor_step['step_id'] += 1
                add_xp(st.session_state.user_progress, 15, st.session_state)
                save_user_progress(st.session_state.user_progress)

                # Keep conversation going with next challenge
                response = f"Perfect! Your solution works correctly.\n\n{get_next_challenge(st.session_state.tutor_step['step_id'])}"

                with st.chat_message("assistant", avatar=persona_avatars.get(selected_persona, "🤖")):
                    st.markdown(response)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response,
                        "avatar": persona_avatars.get(selected_persona, "🤖")
                    })

                st.rerun()
                return
            else:
                # Incorrect attempt - increment counter
                st.session_state.tutor_step['attempts'] += 1

        # Build context with FULL conversation history and scaffolding rules
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

        st.rerun()


def get_next_challenge(step_id):
    """Provide next learning challenge based on completed step"""
    challenges = {
        1: "Ready for the next challenge? Try creating a method that **filters only even numbers** from a List<Integer> and returns them.",
        2: "Nice! Now let's level up. Can you **chain operations**: filter even numbers AND double them in the same stream?",
        3: "Excellent! Let's tackle error handling. Modify your method to **handle null input** gracefully (return empty list instead of crashing)."
    }
    return challenges.get(step_id, "Want to try another Java concept? Just tell me what you'd like to learn!")


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