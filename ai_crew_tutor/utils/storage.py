import streamlit as st
import firebase_admin
from firebase_admin import firestore
import pandas as pd  # <--- Needed for load_ratings

# Default starter profile
DEFAULT_PROGRESS = {
    "level": 1,
    "xp": 0,
    "streak": 0,
    "last_visit": None,
    "affinity": {}
}


def get_db():
    """Helper to get Firestore client"""
    try:
        if not firebase_admin._apps:
            return None
        return firestore.client()
    except Exception as e:
        print(f"DB Error: {e}")
        return None


def load_user_progress():
    """Load from Firebase"""
    db = get_db()

    # If no DB or no user_id, return default
    if not db or 'user_id' not in st.session_state:
        return DEFAULT_PROGRESS.copy()

    try:
        user_id = st.session_state.user_id
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            return doc.to_dict()
        else:
            # Create new user if they don't exist
            doc_ref.set(DEFAULT_PROGRESS)
            return DEFAULT_PROGRESS.copy()
    except Exception as e:
        print(f"Load Progress Error: {e}")
        return DEFAULT_PROGRESS.copy()


def save_user_progress(progress_data):
    """Save to Firebase"""
    db = get_db()
    if not db or 'user_id' not in st.session_state:
        return

    try:
        user_id = st.session_state.user_id
        db.collection('users').document(user_id).set(progress_data, merge=True)
    except Exception as e:
        print(f"Save Progress Error: {e}")


def save_rating(persona, rating):
    """Save rating to Firebase"""
    db = get_db()
    if db:
        try:
            db.collection('ratings').add({
                "persona": persona,
                "rating": rating,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            print(f"Save Rating Error: {e}")


def load_ratings():
    """
    Load all ratings for analytics dashboard.
    Returns a Pandas DataFrame.
    """
    db = get_db()
    if not db:
        return pd.DataFrame(columns=["persona", "rating", "timestamp"])

    try:
        # Get all documents from 'ratings' collection
        docs = db.collection('ratings').stream()
        data = []
        for doc in docs:
            d = doc.to_dict()
            data.append(d)

        if not data:
            return pd.DataFrame(columns=["persona", "rating", "timestamp"])

        return pd.DataFrame(data)
    except Exception as e:
        print(f"Load Ratings Error: {e}")
        return pd.DataFrame(columns=["persona", "rating", "timestamp"])