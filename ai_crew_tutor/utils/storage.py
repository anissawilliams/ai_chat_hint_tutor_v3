import streamlit as st
import json
import os
from firebase_admin import firestore

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
        return firestore.client()
    except:
        return None

def load_user_progress():
    """Load from Firebase (Robust) instead of JSON"""
    db = get_db()

    # If no DB or no user_id, return default
    if not db or 'user_id' not in st.session_state:
        return DEFAULT_PROGRESS.copy()

    user_id = st.session_state.user_id
    doc_ref = db.collection('users').document(user_id)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    else:
        # Create new user if they don't exist
        doc_ref.set(DEFAULT_PROGRESS)
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
        print(f"Save Error: {e}")

def save_rating(persona, rating):
    """Save rating to Firebase"""
    db = get_db()
    if db:
        db.collection('ratings').add({
            "persona": persona,
            "rating": rating,
            "timestamp": firestore.SERVER_TIMESTAMP
        })