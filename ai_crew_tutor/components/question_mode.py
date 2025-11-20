"""
Question Mode Component with Efficient Guided Learning
Provides scaffolded guidance in fewer interactions
"""
import re
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
# State Management
# -----------------------
def _ensure_step_state():
    """Initialize session state for tutorial steps"""
    defaults = {
        'tutor_step': {'step_id': 0, 'attempts': 0, 'last_validation_result': None},
        'show_rating': False,
        'user_progress': {'level': 1, 'xp': 0, 'affinity': {}},
        'chat_mode': True,
        'chat_history': []
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_chat():
    """Reset chat and tutorial state"""
    st.session_state.chat_history = []
    st.session_state.tutor_step = {
        'step_id': 0,
        'attempts': 0,
        'last_validation_result': None
    }


# -----------------------
# Scaffolding Logic
# -----------------------
def get_scaffolding_strategy(attempt_number):
    """Return appropriate scaffolding strategy based on attempt number"""
    strategies = {
        0: """FIRST INTERACTION - Set Direction ONLY:
⚠️ DO NOT provide any code yet - just guide conceptually!
- Acknowledge what they want to build
- Break it into 2-3 concrete sub-steps (e.g., "1. Create method signature, 2. Add the logic, 3. Return the result")
- Give ONE tiny conceptual hint (e.g., "You'll need to use the + operator")
- Ask them to try writing the method signature first
- FORBIDDEN: Do NOT show ANY code structure or method templates""",

        1: """SECOND INTERACTION - Targeted Hints ONLY:
⚠️ Still NO complete code - just specific guidance!
- Point out specifically what's missing or wrong in their attempt
- Provide API/operator hints (e.g., "You'll need the + operator to add two numbers")
- Show ONLY the method signature if they're struggling with it
- Ask them to try implementing the body
- FORBIDDEN: Do NOT show the method body or return statement""",

        2: """THIRD INTERACTION - Partial Code with Blanks:
NOW you can show partial code, but with blanks to fill in:
- Give a partial implementation like: "public int sum(int a, int b) { return ____ + ____; }"
- Explain what each blank should be
- Ask them to fill in the blanks""",

        3: """FOURTH INTERACTION - Working Solution:
NOW provide the complete working solution:
- Show full working code
- Explain each line
- Ask them to modify it slightly (e.g., "Now try multiplying instead")""",
    }

    return strategies.get(attempt_number, """FIFTH+ INTERACTION - Deep Understanding:
- Help them understand variations or debug their modifications
- Suggest extensions and edge cases
- Keep encouraging exploration""")


def build_conversation_history(chat_history, persona):
    """Build formatted conversation history string"""
    conversation = ""
    for msg in chat_history:
        role = "Student" if msg["role"] == "user" else persona
        conversation += f"{role}: {msg['content']}\n\n"
    return conversation


def build_validation_feedback(validation_result, attempt_number):
    """Build validation feedback section"""
    if not validation_result:
        return ""

    is_correct, msg = validation_result
    if is_correct:
        return "\n**✅ VALIDATION: CODE IS CORRECT - Student solved it! Congratulate and move to next challenge.**"
    else:
        return f"\n**❌ VALIDATION: Code has issues - {msg}**\n**Continue guiding based on attempt #{attempt_number + 1} strategy below.**"


def build_efficient_chat_context(chat_history, persona, step_info, validation_result=None):
    """
    Build context that includes FULL conversation history and clear scaffolding rules.
    Prevents giving away answers too early while keeping interactions efficient.
    """
    attempts = step_info['attempts']

    conversation = build_conversation_history(chat_history, persona)
    feedback_section = build_validation_feedback(validation_result, attempts)
    strategy = get_scaffolding_strategy(attempts)

    latest_message = chat_history[-1]['content'] if chat_history else 'N/A'

    context = f"""You are {persona}, an efficient Java tutor who guides students through problems progressively.

CONVERSATION SO FAR:
{conversation}

CURRENT SITUATION:
- This is attempt #{attempts + 1} at the current step
{feedback_section}

YOUR SCAFFOLDING STRATEGY FOR THIS ATTEMPT:
{strategy}

⚠️ CRITICAL RULES - FOLLOW EXACTLY:
1. READ the conversation history above to see what you already said
2. If validation shows ✅ CORRECT: Congratulate and stop giving hints
3. If validation shows ❌ INCORRECT: Follow the scaffolding strategy EXACTLY as written above
4. DO NOT SKIP AHEAD - If strategy says "no code yet", then give NO code
5. NEVER repeat yourself - each response should add new information only
6. Keep responses under 150 words and conversational
7. Always end with a specific question or directive
8. The student's latest message was: "{latest_message}"

You must follow the scaffolding level (attempt #{attempts}) strictly. Respond as {persona}:"""

    return context


# -----------------------
# Validation
# -----------------------
def looks_like_code(text):
    """Check if input looks like code"""
    code_patterns = ['public', 'private', 'return', 'void', '{', 'list',
                    'stream', 'int ', '=', ';', 'class', 'import']
    return any(pattern in text.lower() for pattern in code_patterns)


def validate_code(user_input, validator):
    """Validate user code and return (is_correct, message) tuple"""
    if not validator or not callable(validator):
        return None

    if not looks_like_code(user_input):
        return None

    result = validator(user_input)

    if isinstance(result, tuple):
        return result
    else:
        return (bool(result), "Good attempt, but not quite right yet.")


# -----------------------
# Success Handling
# -----------------------
def handle_correct_solution(selected_persona, persona_avatars):
    """Handle when student submits correct solution"""
    st.success("✅ Correct! Great work.")

    # Reset attempts and increment step
    st.session_state.tutor_step['attempts'] = 0
    st.session_state.tutor_step['step_id'] += 1

    # Award XP
    add_xp(st.session_state.user_progress, 15, st.session_state)
    save_user_progress(st.session_state.user_progress)

    # Generate next challenge
    next_challenge = get_next_challenge(st.session_state.tutor_step['step_id'])
    response = f"Perfect! Your solution works correctly.\n\n{next_challenge}"

    # Add to chat history
    with st.chat_message("assistant", avatar=persona_avatars.get(selected_persona, "🤖")):
        st.markdown(response)
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
            "avatar": persona_avatars.get(selected_persona, "🤖")
        })

    st.rerun()


# -----------------------
# Chat Interface
# -----------------------
def render_chat_header(selected_persona, persona_avatars):
    """Render chat header with clear button"""
    col1, col2 = st.columns([3, 1])

    with col1:
        avatar = persona_avatars.get(selected_persona, '🤖')
        st.markdown(f"### 💬 Chat with {avatar} {selected_persona}")

    with col2:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            reset_chat()
            st.rerun()

    st.caption("Describe what you're trying to build - I'll guide you through it step-by-step!")


def display_chat_history(chat_history):
    """Display all messages in chat history"""
    for message in chat_history:
        avatar = message.get("avatar", "🧑‍💻" if message["role"] == "user" else "🤖")
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])


def process_user_message(user_input, selected_persona, persona_avatars, create_crew):
    """Process user message and generate response"""
    analytics = TutorAnalytics()

    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input,
        "avatar": "🧑‍💻"
    })

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    # Validate code if applicable
    validator = st.session_state.get('current_expected_pattern')
    validation_result = validate_code(user_input, validator)

    if validation_result:
        st.session_state.tutor_step['last_validation_result'] = validation_result

        # Handle correct solution
        if validation_result[0]:
            handle_correct_solution(selected_persona, persona_avatars)
            return

    # Build context for agent
    context = build_efficient_chat_context(
        st.session_state.chat_history,
        selected_persona,
        st.session_state.tutor_step,
        validation_result
    )

    # Get agent response
    with st.chat_message("assistant", avatar=persona_avatars.get(selected_persona, "🤖")):
        with st.spinner(f"{selected_persona} is thinking..."):
            response = create_crew(selected_persona, context)
            st.markdown(response)

            # Add to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response,
                "avatar": persona_avatars.get(selected_persona, "🤖")
            })

            # Track analytics
            analytics.track_question(
                question=user_input,
                response=response,
                persona=selected_persona
            )

    # Increment attempts AFTER agent responds (only if validation failed)
    if validation_result and not validation_result[0]:
        st.session_state.tutor_step['attempts'] += 1

    st.rerun()


def initialize_validator():
    """Initialize code validator for current exercise"""
    if 'current_expected_pattern' not in st.session_state:
        st.session_state['current_expected_pattern'] = java_validator_factory(
            method_name="sum",
            return_type="int",
            param_types=["int", "int"],
            required_tokens=["+", "return"],
            use_ast_check=False
        )


def render_chat_interface(selected_persona, persona_avatars, create_crew, user_level):
    """Render efficient chat-based guided learning"""
    _ensure_step_state()
    initialize_validator()

    # Render header
    render_chat_header(selected_persona, persona_avatars)

    # Display chat history
    display_chat_history(st.session_state.chat_history)

    # Chat input
    user_input = st.chat_input("Describe what you want to build or paste your code...")

    if user_input:
        process_user_message(user_input, selected_persona, persona_avatars, create_crew)


# -----------------------
# Main Renderer
# -----------------------
def render_question_mode(selected_persona, persona_avatars, create_crew, user_level):
    """Render the question/chat mode interface"""
    _ensure_step_state()
    analytics = TutorAnalytics()

    st.divider()
    render_chat_interface(selected_persona, persona_avatars, create_crew, user_level)
    analytics.track_click("Chat Mode")
    show_rating(selected_persona)


# -----------------------
# Challenges
# -----------------------
def get_next_challenge(step_id):
    """Provide next learning challenge based on completed step"""
    challenges = {
        1: "Ready for the next challenge? Try creating a method that **filters only even numbers** from a List<Integer> and returns them.",
        2: "Nice! Now let's level up. Can you **chain operations**: filter even numbers AND double them in the same stream?",
        3: "Excellent! Let's tackle error handling. Modify your method to **handle null input** gracefully (return empty list instead of crashing)."
    }
    return challenges.get(step_id, "Want to try another Java concept? Just tell me what you'd like to learn!")


# -----------------------
# Rating System
# -----------------------
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