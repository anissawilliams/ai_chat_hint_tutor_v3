import streamlit as st
import pandas as pd
import plotly.express as px
from utils.storage import get_db
import datetime

# ---------------------------------------------------------
# 1. SETUP & AUTH
# ---------------------------------------------------------
st.set_page_config(page_title="Dashboard", page_icon="🍎", layout="wide")

# Simple password check to keep students out
password = st.sidebar.text_input("Admin Password", type="password")
if password != st.secrets.get("ADMIN_PASSWORD", "admin123"):
    st.info("🔒 Enter admin password to view analytics.")
    st.stop()

st.title("🍎 Live Classroom Analytics")
st.markdown("Monitor student engagement, struggle points, and success rates in real-time.")

# ---------------------------------------------------------
# 2. DATA FETCHING
# ---------------------------------------------------------
db = get_db()
if not db:
    st.error("Database connection failed.")
    st.stop()


@st.cache_data(ttl=60)  # Refresh data every minute
def fetch_data():
    # 1. Fetch Learning Outcomes (The "Reasonable Way" Metric)
    outcomes_ref = db.collection('learning_outcomes').stream()
    outcomes_data = []
    for doc in outcomes_ref:
        d = doc.to_dict()
        # Handle timestamp conversion
        if 'timestamp' in d:
            d['timestamp'] = pd.to_datetime(d['timestamp'])
        outcomes_data.append(d)

    return pd.DataFrame(outcomes_data)


df = fetch_data()

if df.empty:
    st.warning("No learning data available yet. Wait for students to submit code.")
    st.stop()

# ---------------------------------------------------------
# 3. HIGH-LEVEL KPI CARDS
# ---------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Total successful code submissions
    total_success = df[df['is_correct'] == True].shape[0]
    st.metric("✅ Total Solved", total_success)

with col2:
    # "Reasonable Way" Metric: Avg Attempts per Success
    # We filter for successes, then check what the attempt number was
    if total_success > 0:
        avg_attempts = df[df['is_correct'] == True]['attempt_number'].mean()
        delta_color = "normal" if avg_attempts < 5 else "inverse"  # Red if > 5 tries
        st.metric("Avg Attempts to Solve", f"{avg_attempts:.1f}", delta_color=delta_color)
    else:
        st.metric("Avg Attempts", "-")

with col3:
    # Success Rate (Correct / Total Submissions)
    if len(df) > 0:
        rate = (total_success / len(df)) * 100
        st.metric("Success Rate", f"{rate:.1f}%")

with col4:
    # Stickiness: Unique Students
    if 'session_id' in df.columns:
        unique_students = df['session_id'].nunique()
        st.metric("Active Students", unique_students)

st.divider()

# ---------------------------------------------------------
# 4. PROFICIENCY ANALYSIS
# ---------------------------------------------------------
st.subheader("📊 Proficiency vs. Performance")
st.caption("Are 'Advanced' students actually solving problems faster?")

if 'student_proficiency' in df.columns:
    # Clean up missing data
    df['student_proficiency'] = df['student_proficiency'].fillna('Unknown')

    col_a, col_b = st.columns(2)

    with col_a:
        # Success Rate by Proficiency
        prof_success = df.groupby('student_proficiency')['is_correct'].mean().reset_index()
        prof_success['is_correct'] = prof_success['is_correct'] * 100

        fig_prof = px.bar(
            prof_success,
            x='student_proficiency',
            y='is_correct',
            title="Success Rate by Proficiency Level",
            labels={'is_correct': 'Success Rate (%)', 'student_proficiency': 'Proficiency'},
            color='student_proficiency',
            range_y=[0, 100]
        )
        st.plotly_chart(fig_prof, use_container_width=True)

    with col_b:
        # Time to Solve by Proficiency
        # Filter only correct answers to see how long it took them to get there
        success_df = df[df['is_correct'] == True]
        if not success_df.empty:
            prof_time = success_df.groupby('student_proficiency')['seconds_taken'].mean().reset_index()

            fig_time = px.bar(
                prof_time,
                x='student_proficiency',
                y='seconds_taken',
                title="Avg Time to Solve (Seconds)",
                labels={'seconds_taken': 'Seconds', 'student_proficiency': 'Proficiency'},
                color='seconds_taken',
                color_continuous_scale='Bluered'
            )
            st.plotly_chart(fig_time, use_container_width=True)
else:
    st.info("Proficiency data will appear here once students select their level.")

# ---------------------------------------------------------
# 5. PERSONA EFFECTIVENESS
# ---------------------------------------------------------
st.subheader("🤖 Persona Leaderboard")
st.caption("Which AI tutor is driving the most successes?")

if 'persona' in df.columns:
    persona_stats = df[df['is_correct'] == True]['persona'].value_counts().reset_index()
    persona_stats.columns = ['Persona', 'Solved Problems']

    fig_persona = px.pie(
        persona_stats,
        values='Solved Problems',
        names='Persona',
        hole=0.4
    )
    st.plotly_chart(fig_persona, use_container_width=True)

# ---------------------------------------------------------
# 6. RAW DATA FEED
# ---------------------------------------------------------
with st.expander("📝 View Raw Live Data"):
    st.dataframe(
        df.sort_values('timestamp', ascending=False),
        use_container_width=True
    )