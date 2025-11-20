"""
Question Mode Component - Simplified Conversational Tutor
"""
import re
import streamlit as st
from utils.gamification import add_xp
from utils.storage import save_user_progress, save_rating
from utils.data_collection import TutorAnalytics


# -----------------------
# State Management
# -----------------------
def _ensure_step_state():
    """Initialize minimal session state"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'user_progress' not in st.session_state:
        st.session_state.user_progress = {'level': 1, 'xp': 0, 'affinity': {}}
    if 'show_rating' not in st.session_state:
        st.session_state.show_rating = False


# -----------------------
# Smart Code Validation
# -----------------------
def looks_like_code(text):
    """Check if input appears to be code"""
    code_patterns = ['public', 'private', 'int ', 'string', 'void', 'return', '{', '}', '()', ';', '//']
    return any(pattern in text.lower() for pattern in code_patterns)


def smart_validate_java_code(user_input, conversation_context=""):
    """
    Smart validator that understands what the student is trying to build
    based on conversation context
    Returns: (is_valid, feedback_message, should_celebrate)
    """
    code = user_input.lower()

    # Extract what they're trying to do from context
    context_lower = conversation_context.lower()

    # Check for basic method structure
    has_method_signature = ('(' in code and ')' in code and
                           any(rt in code for rt in ['int', 'string', 'void', 'boolean', 'double', 'list', 'public', 'private']))

    # --- Sum/Add methods ---
    if any(word in context_lower for word in ['sum', 'add']):
        has_body = '{' in code and '}' in code
        has_return = 'return' in code
        has_addition = '+' in code

        # Just signature? Good start, but needs body
        if has_method_signature and not has_body:
            return (False, "Good signature! Now add the body with curly braces { } that adds the numbers and returns the result.", False)

        # Has signature and body but missing logic?
        if has_method_signature and has_body and not (has_return and has_addition):
            return (False, "You have the structure! Now add: 1) the addition using +, and 2) return the result.", False)

        # Complete solution!
        if has_method_signature and has_body and has_return and has_addition:
            return (True, "Perfect! Your method works correctly.", True)

    # --- Stream operations (filter, map, etc.) ---
    elif any(word in context_lower for word in ['stream', 'filter', 'map', 'collect']):
        has_stream = 'stream()' in code
        has_collect = 'collect' in code

        if has_method_signature and has_stream and has_collect:
            return (True, "Excellent! Your stream implementation looks correct.", True)
        elif has_method_signature:
            return (False, "Good start! Remember to use .stream() to convert the list, then chain your operations.", False)

    # --- Generic method check ---
    elif has_method_signature:
        has_body = '{' in code and '}' in code
        has_return = 'return' in code

        if has_body and has_return:
            return (True, "Nice work! Your method structure looks good.", True)
        else:
            return (False, "Good signature! Now add the method body with your logic and a return statement.", False)

    # Not recognizable as a complete method
    return (False, "", False)


# -----------------------
# Context Building
# -----------------------
def build_tutor_context(chat_history, persona):
    """Build simple context for the AI tutor"""

    # Get conversation so far
    conversation = ""
    for msg in chat_history:
        role = "Student" if msg["role"] == "user" else persona
        conversation += f"{role}: {msg['content']}\n\n"

    # Simple, effective instruction
    context = f"""You are {persona}, a friendly and efficient Java tutor.

CONVERSATION SO FAR:
{conversation}

YOUR TEACHING STYLE:
- Be conversational and encouraging, not pedantic
- If the student provides working code (even with minor style issues), celebrate it and move forward
- Don't obsess over naming conventions or minor style - focus on whether it works
- Give concrete, specific help when they're stuck
- Keep responses under 150 words
- Always end with a question or next step
- Use code blocks for examples

IMPORTANT RULES:
1. Review what you already said - don't repeat yourself
2. If their code is basically correct, acknowledge success and suggest what to try next
3. If they're stuck, give ONE clear hint or example
4. Don't split hairs over style - focus on functionality
5. Move the conversation forward, don't keep asking for the same thing

Respond as {persona}, keeping it friendly and moving forward:"""

    return context


# -----------------------
# Success Handling
# -----------------------
def handle_success(persona_avatars, selected_persona):
    """Handle successful code submission"""
    st.success("✅ Great work! That looks correct.")

    add_xp(st.session_state.user_progress, 15, st.session_state)
    save_user_progress(st.session_state.user_progress)

    challenges = [
        "Want to try another challenge? How about creating a method that finds the **maximum** of two integers?",
        "Nice! Ready for more? Try creating a method that **reverses a String**.",
        "Excellent! Let's level up - create a method that **filters even numbers** from a List<Integer>.",
    ]

    import random
    next_challenge = random.choice(challenges)

    response = f"Perfect! Your solution works.\n\n{next_challenge}"

    with st.chat_message("assistant", avatar=persona_avatars.get(selected_persona, "🤖")):
        st.markdown(response)
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
            "avatar": persona_avatars.get(selected_persona, "🤖")
        })


# -----------------------
# Chat Interface
# -----------------------
def render_chat_interface(selected_persona, persona_avatars, create_crew, user_level):
    """Main chat interface"""
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
    for message in st.session_state.chat_history:
        avatar = message.get("avatar", "🧑‍💻" if message["role"] == "user" else "🤖")
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input("Ask a question or paste your code...")

    if user_input:
        # Add user message
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "avatar": "🧑‍💻"
        })

        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)

        # Try to validate if it's code
        validation_result = None
        if looks_like_code(user_input):
            # Get conversation context for smart validation
            full_conversation = "\n".join([msg['content'] for msg in st.session_state.chat_history])
            is_valid, feedback, should_celebrate = smart_validate_java_code(user_input, full_conversation)

            if should_celebrate:
                # Success!
                handle_success(persona_avatars, selected_persona)
                st.rerun()
                return
            elif feedback:
                # Code detected but needs improvement - include feedback
                validation_result = f"\n**Code Feedback**: {feedback}"

        # Build context and get AI response
        context = build_tutor_context(st.session_state.chat_history, selected_persona)

        # Add validation feedback to context if available
        if validation_result:
            context += validation_result

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
    show_rating(selected_persona)


# -----------------------
# Rating
# -----------------------
def show_rating(selected_persona):
    """Rating system"""
    analytics = TutorAnalytics()

    if st.session_state.get('show_rating', False):
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