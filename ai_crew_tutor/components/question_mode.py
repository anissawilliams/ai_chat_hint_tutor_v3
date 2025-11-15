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
        with st.chat_message(message["role"],
                             avatar=message.get("avatar", "🧑‍💻" if message["role"] == "user" else "🤖")):
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
    """Build conversation context for the AI"""
    analytics = TutorAnalytics()
    # If this is the first message, provide initial instructions
    if len(chat_history) <= 1:
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
                add_affinity(st.session_state.user_progress, selected_persona, 5,
                             st.session_state)  # ← Add st.session_state here
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

    # # Display explanation
    # if st.session_state.explanation:
    #     st.markdown("---")
    #     st.markdown(f"""
    #     <div class="explanation-box">
    #         <h4>{persona_avatars.get(selected_persona, '🤖')} {selected_persona}'s Explanation</h4>
    #         {st.session_state.explanation}
    #     </div>
    #     """, unsafe_allow_html=True)

 def show_rating(selected_persona):
        # Rating system
        analytics = TutorAnalytics()
        if st.session_state.show_rating:
            st.markdown("#### How helpful was this session?")
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                if st.button("⭐", key="rate_1"):
                    #save_rating(selected_persona, user_input, 1)
                    st.session_state.show_rating = False
                    analytics.track_click("Rate")
                    st.success("Thanks for your feedback!")
                    st.rerun()
            with col2:
                if st.button("⭐⭐", key="rate_2"):
                    #save_rating(selected_persona, question, 2)
                    st.session_state.show_rating = False
                    analytics.track_click("Rate")
                    st.success("Thanks for your feedback!")
                    st.rerun()
            with col3:
                if st.button("⭐⭐⭐", key="rate_3"):
                    #save_rating(selected_persona, question, 3)
                    st.session_state.show_rating = False
                    analytics.track_click("Rate")
                    st.success("Thanks for your feedback!")
                    st.rerun()
            with col4:
                if st.button("⭐⭐⭐⭐", key="rate_4"):
                    #save_rating(selected_persona, question, 4)
                    st.session_state.show_rating = False
                    analytics.track_click("Rate")
                    st.success("Thanks for your feedback!")
                    st.rerun()
            with col5:
                if st.button("⭐⭐⭐⭐⭐", key="rate_5"):
                    #save_rating(selected_persona, question, 5)
                    st.session_state.show_rating = False
                    analytics.track_click("Rate")
                    st.success("Thanks for your feedback!")
                    st.rerun()
