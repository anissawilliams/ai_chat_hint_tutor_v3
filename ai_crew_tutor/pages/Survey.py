import streamlit as st
from utils.data_collection import TutorAnalytics

st.title("Java Tutorial Feedback Survey")
analytics = TutorAnalytics()
with st.form("survey_form"):
    st.write("We’d love your feedback!")

    # Multiple choice
    difficulty = st.radio(
        "How was the difficulty level?",
        ["Too easy", "Just right", "Challenging"]
    )

    # Rating slider
    clarity = st.slider("Rate the clarity of explanations", 1, 5)

    # Radio buttons
    recommends = st.radio("Would you recommend this tutorial to a friend?", ("Yes", "No"))

    # Text input
    favorite_part = st.text_input("What was your favorite part?")

    # Text area
    suggestions = st.text_area("Any suggestions for improvement?")

    # Submit button
    submitted = st.form_submit_button("Submit")

    survey_data = {
        'clarity': clarity,
        'difficulty': difficulty,
        'favorite_part': favorite_part,
        'suggestions': suggestions,
        'recommends': recommends
    }


if submitted:
    success = analytics.track_survey_response({
        "difficulty": difficulty,
        "clarity": clarity,
        "favorite_part": favorite_part,
        "suggestions": suggestions
    })
    if success:
        st.balloons()

