import streamlit as st

# ---------------------------------------------------------
# 1. SETUP & AUTH
# ---------------------------------------------------------
st.set_page_config(
    page_title="Teacher Dashboard",
    page_icon="🍎",
    layout="wide"
)

# Simple admin authentication
password = st.sidebar.text_input("Admin Password", type="password")
if password != st.secrets.get("ADMIN_PASSWORD", "admin123"):
    st.info("🔒 Enter admin password to view analytics.")
    st.stop()

# ---------------------------------------------------------
# 2. LANDING PAGE
# ---------------------------------------------------------
st.title("🍎 Live Classroom Analytics")

st.write("""
Welcome to the Teacher Dashboard.  

This dashboard provides insights into classroom engagement, performance, and AI tutor feedback.  
Use the sidebar to navigate between pages:

- **Users** → Engagement & Retention metrics  
- **Learning Outcomes** → Student performance analytics  
- **Training Feedback** → AI tutor critique loop  
- **Interactions** → Lesson transcripts and response trends  
- **Clicks** → UI engagement patterns  
- **Events** → System actions (persona selections, mode changes)  
- **Sessions** → Session summaries and drill‑downs
""")

st.success("✅ Select a page from the sidebar to begin exploring your analytics.")