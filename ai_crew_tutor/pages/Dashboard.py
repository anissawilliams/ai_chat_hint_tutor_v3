import streamlit as st
import pandas as pd
import plotly.express as px
from utils.storage import get_db

# ---------------------------------------------------------
# 1. SETUP & AUTH
# ---------------------------------------------------------
st.set_page_config(page_title="Teacher Dashboard", page_icon="🍎", layout="wide")

password = st.sidebar.text_input("Admin Password", type="password")
if password != st.secrets.get("ADMIN_PASSWORD", "admin123"):
    st.info("🔒 Enter admin password to view analytics.")
    st.stop()

st.title("🍎 Live Classroom Analytics")

# ---------------------------------------------------------
# 2. DATA FETCHING
# ---------------------------------------------------------
db = get_db()
if not db:
    st.error("Database connection failed.")
    st.stop()


@st.cache_data(ttl=60)
def fetch_analytics_data():
    # 1. Fetch Learning Outcomes (Performance)
    outcomes_ref = db.collection('learning_outcomes').stream()
    outcomes_data = []
    for doc in outcomes_ref:
        d = doc.to_dict()
        if 'timestamp' in d: d['timestamp'] = pd.to_datetime(d['timestamp'])
        outcomes_data.append(d)

    # 2. Fetch Users (Engagement/Retention)
    users_ref = db.collection('users').stream()
    users_data = []
    for doc in users_ref:
        d = doc.to_dict()
        users_data.append(d)

    return pd.DataFrame(outcomes_data), pd.DataFrame(users_data)


df_outcomes, df_users = fetch_analytics_data()

# ---------------------------------------------------------
# 3. ENGAGEMENT & RETENTION (New Section)
# ---------------------------------------------------------
st.header("🔥 Engagement & Retention")

if not df_users.empty:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_students = len(df_users)
        st.metric("Total Students", total_students)

    with col2:
        # Retention: Students with a streak > 1 day
        returning_students = df_users[df_users['streak'] > 1].shape[0]
        retention_rate = (returning_students / total_students) * 100 if total_students > 0 else 0
        st.metric("Returning Students (Streak > 1)", f"{returning_students} ({retention_rate:.0f}%)")

    with col3:
        # Gamification: Total XP earned by the class
        class_xp = df_users['xp'].sum()
        st.metric("Total Class XP", f"{class_xp:,}")

    with col4:
        # Level distribution
        avg_level = df_users['level'].mean()
        st.metric("Avg Student Level", f"{avg_level:.1f}")

    # Proficiency Pie Chart
    if 'proficiency' in df_users.columns:
        st.subheader("Student Proficiency Breakdown")
        st.caption("Self-reported experience levels")

        # Fill NA with 'Beginner' (default)
        df_users['proficiency'] = df_users['proficiency'].fillna('Beginner')

        prof_counts = df_users['proficiency'].value_counts().reset_index()
        prof_counts.columns = ['Level', 'Count']

        fig_prof = px.pie(prof_counts, values='Count', names='Level', hole=0.4, color='Level',
                          color_discrete_map={'Beginner': '#43e97b', 'Intermediate': '#38f9d7', 'Advanced': '#667eea'})
        st.plotly_chart(fig_prof, use_container_width=True)

else:
    st.info("No user data yet.")

st.divider()

# ---------------------------------------------------------
# 4. LEARNING OUTCOMES (Performance)
# ---------------------------------------------------------
st.header("🧠 Learning Performance")

if not df_outcomes.empty:
    col_a, col_b = st.columns(2)

    with col_a:
        # Success Rate
        success_count = df_outcomes[df_outcomes['is_correct'] == True].shape[0]
        total_attempts = len(df_outcomes)
        rate = (success_count / total_attempts) * 100 if total_attempts > 0 else 0

        st.metric("Global Success Rate", f"{rate:.1f}%")

        # Success by Persona
        st.caption("Success Rate by AI Persona")
        persona_perf = df_outcomes.groupby('persona')['is_correct'].mean().reset_index()
        persona_perf['is_correct'] = persona_perf['is_correct'] * 100
        fig_p = px.bar(persona_perf, x='persona', y='is_correct', range_y=[0, 100])
        st.plotly_chart(fig_p, use_container_width=True)

    with col_b:
        # Struggle Metric (Avg Attempts)
        success_only = df_outcomes[df_outcomes['is_correct'] == True]
        if not success_only.empty:
            avg_tries = success_only['attempt_number'].mean()
            st.metric("Avg Tries to Solution", f"{avg_tries:.1f}")

            st.caption("Avg Time to Solve (Seconds)")
            time_perf = success_only.groupby('persona')['seconds_taken'].mean().reset_index()
            fig_t = px.bar(time_perf, x='persona', y='seconds_taken')
            st.plotly_chart(fig_t, use_container_width=True)
else:
    st.info("No learning outcomes recorded yet.")