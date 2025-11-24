import streamlit as st
from datetime import datetime
import sys
import os

# Fix path imports just in case
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data_collection import TutorAnalytics
from utils.gamification import add_xp
from utils.storage import save_user_progress

st.set_page_config(page_title="Feedback Station", page_icon="📝", layout="centered")

# ---------------------------------------------------------
# 1. CUSTOM CSS (The "Card" Look)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Style the form container */
    [data-testid="stForm"] {
        background-color: #262730;
        padding: 30px;
        border-radius: 20px;
        border: 1px solid #4e4e4e;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    /* Make the submit button full width and green */
    [data-testid="stFormSubmitButton"] > button {
        width: 100%;
        background-color: #43e97b;
        color: black;
        font-weight: bold;
        border: none;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #38f9d7;
        color: black;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. HEADER & GAMIFICATION
# ---------------------------------------------------------
st.title("📝 Help Us Level Up!")
st.caption("Your feedback helps train our AI agents to be better tutors.")

# Show the Reward
st.info("💎 **Reward:** Complete this survey to earn **+50 XP**!")

# ---------------------------------------------------------
# 3. THE FORM
# ---------------------------------------------------------
analytics = TutorAnalytics()

with st.form("feedback_form"):
    st.subheader("How was your session?")

    # Row 1: Difficulty & Clarity
    col1, col2 = st.columns(2)

    with col1:
        difficulty = st.radio(
            "Difficulty Level",
            ["Too Easy", "Just Right", "Too Hard"],
            index=1,
            horizontal=True
        )

    with col2:
        clarity = st.slider(
            "Clarity of Explanations",
            min_value=1, max_value=5, value=4,
            format="%d ⭐"
        )

    st.divider()

    # Row 2: Recommendation
    recommend = st.radio(
        "Would you recommend this to a friend?",
        ["Absolutely! 🚀", "Maybe 🤔", "Not yet 👎"],
        horizontal=True
    )

    st.divider()

    st.subheader("🔬 Research Questions")
    st.caption("Please rate how much you agree with the following statements:")

    # Q1: Scaffolding / Zone of Proximal Development
    # Hypothesis: The AI helps them solve problems they couldn't solve alone.
    q1 = st.select_slider(
        "1. The AI helped me find my own mistakes rather than just giving me the answer.",
        options=["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
        value="Neutral"
    )

    # Q2: Emotional/Social Presence (The Personas)
    # Hypothesis: Personas reduce anxiety compared to a blank terminal.
    q2 = st.select_slider(
        "2. Using a Persona (like Batman/Yoda) made the learning feel less stressful.",
        options=["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
        value="Neutral"
    )

    # Q3: Self-Efficacy
    # Hypothesis: The tool builds confidence.
    q3 = st.select_slider(
        "3. I feel more confident writing Java syntax now than before this session.",
        options=["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
        value="Neutral"
    )

    st.divider()

    # Row 3: Open Text
    fav_part = st.text_input("What was the best part?", placeholder="e.g. The Batman metaphors...")
    suggestions = st.text_area("Any suggestions for improvement?", placeholder="e.g. I want more practice problems...")

    # Submit Button
    submitted = st.form_submit_button("🚀 Submit Feedback & Claim XP")

    if submitted:
        # 1. Prepare Data
        survey_data = {
            "difficulty": difficulty,
            "clarity": clarity,
            "recommend": recommend,
            "favorite_part": fav_part,
            "suggestions": suggestions,
            "research_scaffolding": q1,
            "research_persona": q2,
            "research_confidence": q3,
            "timestamp": datetime.now()
        }

        # 2. Save to Firebase (via Analytics class)
        success = analytics.track_survey_results(survey_data)

        if success:
            # 3. Gamification Reward
            if 'user_progress' not in st.session_state:
                from utils.storage import load_user_progress

                st.session_state.user_progress = load_user_progress()

            add_xp(st.session_state.user_progress, 50, st.session_state)
            save_user_progress(st.session_state.user_progress)

            # 4. Celebration
            st.balloons()
            st.success("Feedback received! +50 XP added to your profile.")
        else:
            st.error("Something went wrong saving your feedback. Please try again.")

# ---------------------------------------------------------
# 4. NAVIGATION
# ---------------------------------------------------------
if st.button("⬅️ Back to Tutor"):
    st.switch_page("app.py")