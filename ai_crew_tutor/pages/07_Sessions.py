import streamlit as st
import pandas as pd
import plotly.express as px
from utils.storage import get_db

st.title("📂 Sessions")

db = get_db()
df_sessions = pd.DataFrame([doc.to_dict() for doc in db.collection("sessions").stream()])

if not df_sessions.empty:
    # Parse timestamps
    df_sessions['start_time'] = pd.to_datetime(df_sessions['start_time'], errors='coerce')

    # Group by session_id
    grouped = df_sessions.groupby('session_id').agg({
        'user_id': 'first',
        'platform': 'first',
        'status': 'last',
        'start_time': 'min'
    }).reset_index()

    # Show simplified table
    st.dataframe(grouped[['session_id','user_id','status','platform']].sort_values('start_time', ascending=False))

    # Insights
    st.subheader("Sessions by Status")
    status_counts = grouped['status'].value_counts().reset_index()
    status_counts.columns = ['Status','Count']
    fig_status = px.bar(status_counts, x='Status', y='Count', title="Active vs Completed Sessions")
    st.plotly_chart(fig_status, use_container_width=True)

    st.subheader("Sessions per User")
    user_counts = grouped['user_id'].value_counts().reset_index()
    user_counts.columns = ['User ID','Sessions']
    fig_users = px.bar(user_counts.head(20), x='User ID', y='Sessions', title="Top 20 Users by Sessions")
    st.plotly_chart(fig_users, use_container_width=True)

    st.subheader("Sessions Over Time")
    trend = grouped.groupby(grouped['start_time'].dt.date).size().reset_index(name='Sessions')
    fig_trend = px.line(trend, x='start_time', y='Sessions', title="Sessions per Day")
    st.plotly_chart(fig_trend, use_container_width=True)

    # Drill-down: select a session
    st.subheader("🔎 Drill-down: Session Details")
    selected_session = st.selectbox("Select a Session ID", grouped['session_id'].tolist())

    if selected_session:
        # Interactions
        df_interactions = pd.DataFrame([doc.to_dict() for doc in db.collection("interactions").where("session_id","==",selected_session).stream()])
        if not df_interactions.empty:
            df_interactions['timestamp'] = pd.to_datetime(df_interactions['timestamp'])
            st.write("**Interactions**")
            st.dataframe(df_interactions[['timestamp','persona','question','response_length']].sort_values('timestamp'))

        # Clicks
        df_clicks = pd.DataFrame([doc.to_dict() for doc in db.collection("clicks").where("session_id","==",selected_session).stream()])
        if not df_clicks.empty:
            df_clicks['timestamp'] = pd.to_datetime(df_clicks['timestamp'])
            st.write("**Clicks**")
            st.dataframe(df_clicks[['timestamp','element_name','element_type','user_id']].sort_values('timestamp'))

        # Events
        df_events = pd.DataFrame([doc.to_dict() for doc in db.collection("events").where("session_id","==",selected_session).stream()])
        if not df_events.empty:
            df_events['timestamp'] = pd.to_datetime(df_events['timestamp'])
            st.write("**Events**")
            st.dataframe(df_events[['timestamp','event_type','persona','user_id']].sort_values('timestamp'))
else:
    st.info("No sessions recorded yet.")