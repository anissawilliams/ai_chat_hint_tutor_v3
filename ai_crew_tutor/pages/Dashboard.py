import streamlit as st
import pandas as pd
import plotly.express as px
from utils.storage import get_db

# Password protect this page (optional simple check)
# You can remove this block if you just want to access it freely
password = st.sidebar.text_input("Admin Password", type="password")
if password != st.secrets.get("ADMIN_PASSWORD", "admin123"):
    st.warning("🔒 Restricted Access")
    st.stop()

st.title("🍎 Teacher Dashboard: Live Analytics")

# 1. Fetch Data from Firebase
db = get_db()
if not db:
    st.error("Database connection failed.")
    st.stop()


@st.cache_data(ttl=60)  # Refresh cache every 60 seconds
def fetch_learning_data():
    docs = db.collection('learning_outcomes').stream()
    data = []
    for doc in docs:
        d = doc.to_dict()
        d['timestamp'] = pd.to_datetime(d['timestamp'])  # Ensure time is sortable
        data.append(d)
    return pd.DataFrame(data)


df = fetch_learning_data()

if df.empty:
    st.info("Waiting for student data...")
    st.stop()

# 2. High-Level Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Interactions", len(df))
with col2:
    # Calculate Success Rate
    success_rate = (df['is_correct'].sum() / len(df)) * 100
    st.metric("Success Rate", f"{success_rate:.1f}%")
with col3:
    # Average Attempts needed
    avg_attempts = df['attempt_number'].mean()
    st.metric("Avg Attempts", f"{avg_attempts:.2f}")
with col4:
    # Avg Time spent
    avg_time = df['seconds_taken'].mean()
    st.metric("Avg Time (sec)", f"{avg_time:.0f}s")

st.divider()

# 3. Persona Performance Comparison
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🏆 Success Rate by Persona")
    # Group by persona and calculate % correct
    persona_perf = df.groupby('persona')['is_correct'].mean().reset_index()
    persona_perf['is_correct'] = persona_perf['is_correct'] * 100

    fig_perf = px.bar(
        persona_perf,
        x='persona',
        y='is_correct',
        color='persona',
        labels={'is_correct': 'Success Rate (%)'},
        range_y=[0, 100]
    )
    st.plotly_chart(fig_perf, use_container_width=True)

with col_right:
    st.subheader("⏳ Struggle Time (Avg Seconds)")
    # Who takes the longest to help?
    time_perf = df.groupby('persona')['seconds_taken'].mean().reset_index()

    fig_time = px.bar(
        time_perf,
        x='persona',
        y='seconds_taken',
        color='seconds_taken',
        color_continuous_scale='Reds'
    )
    st.plotly_chart(fig_time, use_container_width=True)

# 4. Recent Live Feed
st.subheader("📡 Live Student Feed")
st.dataframe(
    df.sort_values('timestamp', ascending=False)[
        ['timestamp', 'persona', 'is_correct', 'attempt_number', 'seconds_taken']],
    use_container_width=True,
    hide_index=True
)