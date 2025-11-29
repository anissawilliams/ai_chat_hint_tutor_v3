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
# 2. DB CONNECTION
# ---------------------------------------------------------
db = get_db()
if not db:
    st.error("Database connection failed.")
    st.stop()

@st.cache_data(ttl=60)
def fetch_table(collection_name, parse_timestamp=True):
    ref = db.collection(collection_name).stream()
    data = []
    for doc in ref:
        d = doc.to_dict()
        if parse_timestamp and 'timestamp' in d:
            d['timestamp'] = pd.to_datetime(d['timestamp'])
        data.append(d)
    return pd.DataFrame(data)

# ---------------------------------------------------------
# 3. TABS
# ---------------------------------------------------------
tab_users, tab_outcomes, tab_feedback = st.tabs([
    "Users", "Learning Outcomes", "Training Feedback"
])

# ---------------- USERS TAB ----------------
with tab_users:
    df_users = fetch_table("users", parse_timestamp=False)
    st.header("🔥 Engagement & Retention")

    if not df_users.empty:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_students = len(df_users)
            st.metric("Total Students", total_students)

        with col2:
            returning_students = df_users[df_users['streak'] > 1].shape[0]
            retention_rate = (returning_students / total_students) * 100 if total_students > 0 else 0
            st.metric("Returning Students (Streak > 1)", f"{returning_students} ({retention_rate:.0f}%)")

        with col3:
            class_xp = df_users['xp'].sum()
            st.metric("Total Class XP", f"{class_xp:,}")

        with col4:
            avg_level = df_users['level'].mean()
            st.metric("Avg Student Level", f"{avg_level:.1f}")

        if 'proficiency' in df_users.columns:
            st.subheader("Student Proficiency Breakdown")
            df_users['proficiency'] = df_users['proficiency'].fillna('Beginner')
            prof_counts = df_users['proficiency'].value_counts().reset_index()
            prof_counts.columns = ['Level', 'Count']
            fig_prof = px.pie(prof_counts, values='Count', names='Level', hole=0.4,
                              color='Level',
                              color_discrete_map={'Beginner': '#43e97b',
                                                  'Intermediate': '#38f9d7',
                                                  'Advanced': '#667eea'})
            st.plotly_chart(fig_prof, use_container_width=True)
    else:
        st.info("No user data yet.")

# ---------------- OUTCOMES TAB ----------------
with tab_outcomes:
    df_outcomes = fetch_table("learning_outcomes")
    st.header("🧠 Learning Performance")

    if not df_outcomes.empty:
        col_a, col_b = st.columns(2)

        with col_a:
            success_count = df_outcomes[df_outcomes['is_correct'] == True].shape[0]
            total_attempts = len(df_outcomes)
            rate = (success_count / total_attempts) * 100 if total_attempts > 0 else 0
            st.metric("Global Success Rate", f"{rate:.1f}%")

            st.caption("Success Rate by AI Persona")
            persona_perf = df_outcomes.groupby('persona')['is_correct'].mean().reset_index()
            persona_perf['is_correct'] = persona_perf['is_correct'] * 100
            fig_p = px.bar(persona_perf, x='persona', y='is_correct', range_y=[0, 100])
            st.plotly_chart(fig_p, use_container_width=True)

        with col_b:
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

# ---------------- FEEDBACK TAB ----------------
with tab_feedback:
    df_feedback = fetch_table("ai_training_feedback")
    st.header("📝 AI Training Feedback")

    if not df_feedback.empty:
        st.subheader("Recent Feedback Records")
        st.dataframe(df_feedback[['timestamp', 'persona', 'bad_response', 'critique']].sort_values('timestamp', ascending=False))

        st.subheader("Critiques per Persona")
        critique_counts = df_feedback.groupby('persona')['critique'].count().reset_index()
        fig_c = px.bar(critique_counts, x='persona', y='critique', title="Number of Critiques by Persona")
        st.plotly_chart(fig_c, use_container_width=True)

        st.subheader("Bad Response Length Over Time")
        df_feedback['bad_length'] = df_feedback['bad_response'].apply(lambda x: len(x) if isinstance(x, str) else 0)
        length_trend = df_feedback.groupby(df_feedback['timestamp'].dt.date)['bad_length'].mean().reset_index()
        fig_l = px.line(length_trend, x='timestamp', y='bad_length', title="Avg Bad Response Length per Day")
        st.plotly_chart(fig_l, use_container_width=True)
    else:
        st.info("No training feedback recorded yet.")