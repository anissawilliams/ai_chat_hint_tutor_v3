"""
Question Mode Component with Chat-based Guided Learning
Supports both quick explanations and interactive chat guidance
"""
import streamlit as st
from utils.gamification import add_xp, add_affinity
from utils.storage import save_user_progress, save_rating
from utils.data_collection import TutorAnalytics


def render_question_mode(selected_persona, persona_avatars, create_crew, user_level):
    """Render the question/chat mode interface"""
    analytics = TutorAnalytics()
    # Mode toggle
    col1, col2 = st.columns(2)
    with col1:
        # if st.button("💬 Chat Mode", use_container_width=True,
        #              type="primary" if st.session_state.get('chat_mode', False) else "secondary"):
        #     st.session_state.chat_mode = True
        #     st.rerun()
        st.session_state.chat_mode = True
    # with col2:
    #     if st.button("⚡ Quick Explain", use_container_width=True,
    #                  type="primary" if not st.session_state.get('chat_mode', False) else "secondary"):
    #         st.session_state.chat_mode = False
    #         st.rerun()

    st.divider()

    # Initialize chat mode state
    if st.session_state.get('chat_mode', True):
        render_chat_interface(selected_persona, persona_avatars, create_crew, user_level)
        analytics.track_click("Chat Mode")


    # else:
    #     render_quick_explain(selected_persona, persona_avatars, create_crew, user_level)
    show_rating(selected_persona)

def render_chat_interface(selected_persona, persona_avatars, create_crew, user_level):
    """Render interactive chat-based guided learning"""

    # Initialize analytics
    analytics = TutorAnalytics()

    st.markdown(f"### 💬 Chat with {persona_avatars.get(selected_persona, '🤖')} {selected_persona}")
    st.caption("Describe what you're trying to build, and I'll guide you through it step-by-step!")

    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_chat_persona' not in st.session_state:
        st.session_state.current_chat_persona = selected_persona
        analytics.track_persona_selection(selected_persona)

    # Reset chat if persona changed
    if st.session_state.current_chat_persona != selected_persona:
        st.session_state.chat_history = []
        st.session_state.current_chat_persona = selected_persona
        analytics.track_persona_selection(selected_persona)

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(
            message["role"],
            avatar=message.get("avatar", "🧑‍💻" if message["role"] == "user" else "🤖")
        ):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input("Describe what you want to build...")

    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "avatar": "🧑‍💻"
        })

        # Display user message
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)

        # Generate AI response with context
        with st.chat_message("assistant", avatar=persona_avatars.get(selected_persona, "🤖")):
            with st.spinner(f"{selected_persona} is thinking..."):
                context = build_chat_context(st.session_state.chat_history, selected_persona)
                response = create_crew(selected_persona, context)
                st.markdown(response)

                # Add to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "avatar": persona_avatars.get(selected_persona, "🤖")
                })

                # Track the interaction
                analytics.track_question(
                    question=user_input,
                    response=response,
                    persona=selected_persona
                )

        # Award XP for engagement
        xp_gained = 5
        level_up = add_xp(st.session_state.user_progress, xp_gained, st.session_state)
        add_affinity(st.session_state.user_progress, selected_persona, 3, st.session_state)
        save_user_progress(st.session_state.user_progress)

        if level_up:
            st.session_state.show_reward = {
                'type': 'level_up',
                'level': st.session_state.user_progress['level']
            }

        st.rerun()

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", type="secondary"):
            analytics.track_click("Clear Chat", "button")
            st.session_state.chat_history = []
            st.rerun()


def build_chat_context(chat_history, persona):
    """Build conversation context for the AI with hint escalation"""

    analytics = TutorAnalytics()

    # If this is the first message, provide initial instructions
    if len(chat_history) <= 1:
        context = f"""You are {persona}, a Java tutor using guided learning methodology.

CORE PRINCIPLE: Guide through questions, NOT immediate answers. Help the student think and work.

ESCALATION RULES:
- First attempt: ask a guiding question (3–5 sentences max).
- Second attempt: provide a partial hint (e.g., method signature, pseudocode).
- Third attempt: reveal the full solution clearly.
- Always praise correct answers briefly, then move to the next step.
- If wrong: gently correct and re-ask in simpler terms.
- End each response with: "👉 [specific question]?"

RESPONSE PATTERN:
1. Acknowledge their goal briefly.
2. Identify the FIRST small step.
3. Ask a guiding question about that step.
4. If they struggle twice, escalate to a hint.
5. If still stuck, provide the full solution.

Student’s question: {chat_history[-1]['content']}

Respond as {persona} — start with a guiding question:"""

    else:
        # For ongoing conversation
        context = f"""You are {persona}, a Java tutor. Continue guiding this student with escalation.

RULES:
- Keep responses short (3–5 sentences).
- Escalate hints if the student struggles:
  • First: guiding question
  • Second: partial hint
  • Third: full solution
- Praise correct answers, then move forward.
- Gently correct wrong answers and re-ask.
- End with: "👉 [specific question]?"

Conversation history:
"""
        # Add recent conversation history (last 5 messages for focus)
        recent_history = chat_history[-5:]
        for msg in recent_history:
            if msg["role"] == "user":
                context += f"\nStudent: {msg['content']}\n"
            else:
                context += f"\n{persona}: {msg['content']}\n"

        context += f"\n{persona} (guide with escalation, end with one focused question):"
        st.session_state.show_rating = True

    return context

def render_quick_explain(selected_persona, persona_avatars, create_crew, user_level):
    """Render the original quick explanation mode"""

    st.markdown(f"### ⚡ Quick Explanation with {persona_avatars.get(selected_persona, '🤖')} {selected_persona}")
    analytics = TutorAnalytics()
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
    analytics = TutorAnalytics()
    if st.session_state.show_rating:
        st.markdown("#### How helpful was this session?")

        rating = st.slider(
            "Rate the session",
            min_value=1,
            max_value=5,
            value=3,
            step=1,
            format="%d ⭐"
        )

        if st.button("Submit Rating", type="primary"):
            # save_rating(selected_persona, rating)  # Uncomment when ready
            st.session_state.show_rating = False
            analytics.track_click("Rate")
            st.success("Thanks for your feedback!")
            st.rerun()
