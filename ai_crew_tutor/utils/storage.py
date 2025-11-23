import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

# Default starter profile
DEFAULT_PROGRESS = {
    "level": 1,
    "xp": 0,
    "streak": 0,
    "last_visit": None,
    "affinity": {},
    "proficiency": "Beginner"  # Added this so new users have a default
}


def get_db():
    """Helper to get Firestore client safely"""
    try:
        # Check if already initialized (by data_collection.py)
        if not firebase_admin._apps:
            # If not, try to initialize
            if "firebase" in st.secrets:
                cred = credentials.Certificate({
                    "type": st.secrets["firebase"]["type"],
                    "project_id": st.secrets["firebase"]["project_id"],
                    "private_key": st.secrets["firebase"]["private_key"],
                    "client_email": st.secrets["firebase"]["client_email"],
                    "token_uri": st.secrets["firebase"]["token_uri"],
                })
                firebase_admin.initialize_app(cred)
            else:
                return None
        return firestore.client()
    except Exception as e:
        # If running locally without secrets or connection issues
        print(f"DB Error: {e}")
        return None


def load_user_progress():
    """Load user progress from Firebase"""
    db = get_db()

    # Use real User ID if logged in, otherwise session ID
    user_id = st.session_state.get('user_id', st.session_state.get('session_id'))

    # If no DB or no ID, return default
    if not db or not user_id:
        return DEFAULT_PROGRESS.copy()

    try:
        doc_ref = db.collection('users').document(str(user_id))
        doc = doc_ref.get()

        if doc.exists:
            # Merge with default to ensure new keys (like 'proficiency') exist
            data = doc.to_dict()
            merged = DEFAULT_PROGRESS.copy()
            merged.update(data)
            return merged
        else:
            # Create new user if they don't exist
            doc_ref.set(DEFAULT_PROGRESS)
            return DEFAULT_PROGRESS.copy()
    except Exception as e:
        print(f"Load Progress Error: {e}")
        return DEFAULT_PROGRESS.copy()


def save_user_progress(progress_data):
    """Save user progress to Firebase"""
    db = get_db()

    user_id = st.session_state.get('user_id', st.session_state.get('session_id'))

    if not db or not user_id:
        return

    try:
        db.collection('users').document(str(user_id)).set(progress_data, merge=True)
    except Exception as e:
        print(f"Save Progress Error: {e}")


def save_rating(persona, rating, comment=""):
    """Save a simple rating"""
    db = get_db()
    if db:
        try:
            db.collection('ratings').add({
                "persona": persona,
                "rating": rating,
                "comment": comment,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            print(f"Save Rating Error: {e}")


# ✅ THIS IS THE MISSING FUNCTION
def load_ratings():
    """
    Load ratings history for the sidebar.
    Returns a Pandas DataFrame.
    """
    db = get_db()
    if not db:
        return pd.DataFrame()

    try:
        # Get recent ratings (limit to last 50 to keep it fast)
        docs = db.collection('ratings').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50).stream()

        data = []
        for doc in docs:
            d = doc.to_dict()
            data.append(d)

        if not data:
            return pd.DataFrame()

        return pd.DataFrame(data)
    except Exception as e:
        print(f"Load Ratings Error: {e}")
        return pd.DataFrame()