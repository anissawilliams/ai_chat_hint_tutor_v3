"""
Analytics dashboard component
"""
import streamlit as st

def render_analytics(historical_df):
    """Render analytics dashboard page"""
    st.header("📊 Analytics Dashboard")

    if historical_df.empty:
        st.info("📊 No ratings data yet. Start asking questions!")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_clarity = historical_df['clarity'].mean() if 'clarity' in historical_df.columns else 0
        st.metric("📊 Avg Clarity", f"{avg_clarity:.2f}⭐")

    with col2:
        total = len(historical_df)
        st.metric("📝 Total Ratings", total)

    with col3:
        if 'persona' in historical_df.columns:
            best = historical_df.groupby('persona')['clarity'].mean().idxmax()
            st.metric("🏆 Top Persona", best[:12])

    with col4:
        if 'helpfulness' in historical_df.columns:
            avg_help = historical_df['helpfulness'].mean()
            st.metric("💡 Helpfulness", f"{avg_help:.2f}⭐")
