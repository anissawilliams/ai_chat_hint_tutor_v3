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

    # Count how many messages (to determine if this is the first interaction)
    is_first_message = len([m for m in chat_history if m["role"] == "user"]) == 1

    # Adjust guidance based on whether student has submitted code yet
    has_submitted_code = any(looks_like_code(msg["content"]) for msg in chat_history if msg["role"] == "user")

    if is_first_message and not has_submitted_code:
        # First interaction - they're asking what to build
        context = f"""You are {persona}, a Java tutor using guided learning methodology.

        CORE PRINCIPLE: Guide through questions, NOT answers. Make the student think and work.

        STRICT RULES:
        - Keep responses SHORT (3-5 sentences max)
        - Break problems into tiny, manageable steps
        - ONLY give the full solution when the student has provided the correct and complete answer
        - Wait for student's answer before proceeding
        - Use "Step X —" structure when guiding
        - End EVERY response with a focused question using: "👉 [specific question]?"
        - If student is stuck, ask a simpler leading question
        - Check understanding by asking them to explain back

        RESPONSE PATTERN:
        1. Acknowledge their goal briefly
        2. Identify the FIRST small step
        3. Ask a question about that step only
        4. Show their answer in code blocks
        5. Wait for their response

        EXAMPLE:
        "Got it! You need to double each number in a List.

        Step 1 — First, let's think about the method signature. 

        👉 What should this method accept as input, and what should it return?"

        Student's question: {chat_history[-1]['content']}

        Respond as {persona} - ask ONE question to start:"""
    else:
        # For ongoing conversation
        context = f"""You are {persona}, a Java tutor. Continue guiding this student in your unique way.

        CRITICAL - ONLY GIVE FULL SOLUTIONS WHEN STUDENTS PROVIDE THE CORRECT ANSWER:
        - Respond in 3-5 sentences max
        - If they answered correctly: praise briefly, then ask about the NEXT step
        - If they're stuck: ask a simpler leading question
        - If they're wrong: gently correct and ask them to try again
        - Only reveal code when they've worked through the logic of the previous hint
        - User triple backticks (```) to format code blocks
        - Check understanding: ask them to explain their reasoning
        - End with: "👉 [one specific question]?"
        - Respond ONLY as {persona}

        Conversation history:
        """
        # Add recent conversation history (last 8 messages for better context)
        recent_history = chat_history[-8:]
        for msg in recent_history:
            if msg["role"] == "user":
                context += f"\nStudent: {msg['content']}\n"
            else:
                context += f"\n{persona}: {msg['content']}\n"

        context += f"\n{persona} (guide with ONE question, wait for response):"
        st.session_state.show_rating = True
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
            #save_rating(selected_persona, rating)
            st.session_state.show_rating = False
            analytics.track_click("Rate")
            st.success("Thanks for your feedback!")
            st.rerun()


if st.button("Go to Survey"):
    st.button("Go to Survey", on_click=lambda: st.switch_page("pages/Survey.py"))

