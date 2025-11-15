"""
Question Mode Component with Chat-based Guided Learning
Supports both quick explanations and interactive chat guidance
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
            'step_id': 0,           # incremental logical step counter
            'attempts': 0,         # attempts at current step
            'escalation': 0        # 0=guide,1=partial,2=full
        }
    if 'hint_level' not in st.session_state:
        st.session_state.hint_level = 0  # 0 none, 1 inline hint, 2 partial/masked
    if 'peek_requested' not in st.session_state:
        st.session_state.peek_requested = False
    if 'solution_shown' not in st.session_state:
        st.session_state.solution_shown = False
    if 'show_rating' not in st.session_state:
        st.session_state.show_rating = False
    if 'user_progress' not in st.session_state:
        st.session_state.user_progress = {'level': 1, 'xp': 0, 'affinity': {}}
    if 'chat_mode' not in st.session_state:
        st.session_state.chat_mode = True


def simple_validator(expected_pattern, student_answer):
    """
    Lightweight correctness check. Replace or expand with real tests.
    - expected_pattern: regex or callable
    - student_answer: string
    Returns True if answer is acceptable.
    """
    if callable(expected_pattern):
        try:
            return bool(expected_pattern(student_answer))
        except Exception:
            return False
    if expected_pattern is None:
        return False
    return bool(re.search(expected_pattern, student_answer, re.IGNORECASE))


def mask_code(code, mask_ratio=0.6):
    """Mask roughly mask_ratio of identifiers/literals to create a fill-in-the-blank peek."""
    tokens = re.findall(r"[A-Za-z_]\w*|\d+|.", code)
    identifiers = [i for i, t in enumerate(tokens) if re.match(r"[A-Za-z_]\w*", t)]
    if not identifiers:
        return code
    to_mask = set(random.sample(identifiers, max(1, int(len(identifiers) * mask_ratio))))
    out = []
    for idx, tok in enumerate(tokens):
        out.append("____" if idx in to_mask else tok)
    return "".join(out)


def hint_for_step(step_id, escalation):
    """
    Return progressively more explicit hints for the current step.
    escalation: 0=question, 1=inline hint, 2=partial/masked
    Replace with context-aware content in production.
    """
    if escalation == 0:
        return "Think about what the method should accept and return. Focus on types."
    if escalation == 1:
        return "Hint: the method signature might use List<Integer> for input and output."
    return ("Partial skeleton: public List<Integer> transform(List<Integer> nums) { "
            "return nums.stream().map(n -> n * 2).collect(Collectors.toList()); }")


# -----------------------
# Prompt builder
# -----------------------
def build_chat_context(chat_history, persona, decisiveness=1, expected_pattern=None):
    """
    Build conversation context that reduces back-and-forth by:
    - Including short guiding question + inline hint based on attempts
    - Escalating to partial/full solution using session state and decisiveness
    - Using an optional expected_pattern for automatic correctness checks
    decisiveness: 0 (more Socratic), 1 (balanced), 2 (decisive)
    """
    _ensure_step_state()
    analytics = TutorAnalytics()

    last_user = chat_history[-1]['content'] if chat_history else ""
    step = st.session_state.tutor_step

    # If user just answered, run validator to possibly advance
    if expected_pattern and len(chat_history) >= 1 and chat_history[-1]['role'] == 'user':
        student_answer = chat_history[-1]['content']
        if simple_validator(expected_pattern, student_answer):
            # Mark correct: reset attempts and advance step
            step['attempts'] = 0
            step['step_id'] += 1
            step['escalation'] = 0
            st.session_state.tutor_step = step
            st.session_state.show_rating = True
            return (f"You’re correct. Nice work — quick praise.\n\n"
                    f"Step {step['step_id'] + 1} — [next focused question]")

    # Determine escalation threshold from decisiveness
    escalation_thresholds = {0: 3, 1: 2, 2: 1}
    escalate_after = escalation_thresholds.get(decisiveness, 2)

    # Decide current escalation level
    if step['attempts'] >= escalate_after:
        step['escalation'] = min(2, step['escalation'] + 1)

    # Build the prompt with combined guidance and compact hint
    hint_inline = ""
    if step['escalation'] == 1:
        hint_inline = "Hint: consider method signature and return type (e.g., List<Integer>)."
    elif step['escalation'] == 2:
        hint_inline = "Partial solution: show method skeleton or short pseudocode."

    context = f"""You are {persona}, a concise Java tutor using guided learning with escalation.
RULES:
- Keep responses short (1-3 sentences) but decisive to reduce back-and-forth.
- Each reply should: acknowledge goal, identify one small step, ask one focused question.
- If this is attempt #{step['attempts']+1} on current step, include a short inline hint when escalation >=1.
- If escalation == 2, include a concise partial code snippet or a very short full solution if student remains stuck.
- Use "Step N —" labeling and end with a single focused question prefixed by "👉".
- Avoid repeated micro-questions; prefer one question + inline hint.

Student recent input: {last_user}

{hint_inline if hint_inline else ""}

Respond as {persona} and end with exactly one focused question using "👉".
"""

    # increment attempts for the next round (we assume this prompt will be consumed)
    step['attempts'] += 1
    st.session_state.tutor_step = step
    st.session_state.show_rating = True

    return context


# -----------------------
# Renderers
# -----------------------
def render_question_mode(selected_persona, persona_avatars, create_crew, user_level):
    """Render the question/chat mode interface"""
    _ensure_step_state()
    analytics = TutorAnalytics()

    # Mode toggle (simple by default)
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.chat_mode = True
    # with col2:
    #     if st.button("⚡ Quick Explain", ...): ...

    st.divider()

    # Dispatch to the selected interface
    if st.session_state.get('chat_mode', True):
        render_chat_interface(selected_persona, persona_avatars, create_crew, user_level)
        analytics.track_click("Chat Mode")
    else:
        render_quick_explain(selected_persona, persona_avatars, create_crew, user_level)

    show_rating(selected_persona)


def render_chat_interface(selected_persona, persona_avatars, create_crew, user_level):
    """Render interactive chat-based guided learning"""
    _ensure_step_state()
    analytics = TutorAnalytics()

    st.markdown(f"### 💬 Chat with {persona_avatars.get(selected_persona, '🤖')} {selected_persona}")
    st.caption("Describe what you're trying to build, and I'll guide you through it step-by-step!")

    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # --- Example: configure validator for this exercise ---
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
    user_input = st.chat_input("Describe what you want to build...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input, "avatar": "🧑‍💻"})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)

        # --- Run validator ---
        validator = st.session_state.get('current_expected_pattern')
        if validator and callable(validator):
            res = validator(user_input)
            if isinstance(res, tuple):
                ok, msg = res
            else:
                ok, msg = bool(res), ""

            if ok:
                st.success("✅ Correct! Moving to the next step.")
                st.session_state.tutor_step['attempts'] = 0
                st.session_state.tutor_step['step_id'] += 1
                add_xp(st.session_state.user_progress, 15, st.session_state)
                save_user_progress(st.session_state.user_progress)
            else:
                st.warning(f"⚠️ {msg}")
                st.session_state.tutor_step['attempts'] += 1

        # --- Build context and call model ---
        context = build_chat_context(st.session_state.chat_history, selected_persona,
                                     decisiveness=st.session_state.get("decisiveness", 1),
                                     expected_pattern=validator)
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


def render_quick_explain(selected_persona, persona_avatars, create_crew, user_level):
    """Render the original quick explanation mode"""
    analytics = TutorAnalytics()
    st.markdown(f"### ⚡ Quick Explanation with {persona_avatars.get(selected_persona, '🤖')} {selected_persona}")
    question = st.text_area(
        "What Java concept would you like explained?",
        placeholder="e.g., What are generics? How do ArrayLists work? Explain inheritance...",
        height=100
    )

    if st.button("Get Explanation", type="primary", disabled=not question):
        with st.spinner(f"{selected_persona} is preparing your explanation..."):
            try:
                explanation = create_crew(selected_persona, question)
                st.session_state.explanation = explanation

                # Award XP and affinity
                xp_gained = 10
                level_up = add_xp(st.session_state.user_progress, xp_gained, st.session_state)
                add_affinity(st.session_state.user_progress, selected_persona, 5, st.session_state)
                save_user_progress(st.session_state.user_progress)

                st.session_state.show_rating = True

                if level_up:
                    st.session_state.show_reward = {
                        'type': 'level_up',
                        'level': st.session_state.user_progress['level']
                    }

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.explanation = None


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
            # save_rating(selected_persona, rating)  # Uncomment when ready
            st.session_state.show_rating = False
            analytics.track_click("Rate")
            st.success("Thanks for your feedback!")
            st.rerun()
