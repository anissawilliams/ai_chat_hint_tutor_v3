import streamlit as st
import requests
import json

FIREBASE_WEB_API_KEY = st.secrets["firebase"]["web_api_key"]

def sign_in_with_email_and_password(email, password):
    request_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"email": email, "password": password, "returnSecureToken": True}

    resp = requests.post(request_url, headers=headers, json=data)
    if resp.status_code == 200:
        return resp.json()  # Returns localId (uid), idToken, etc.
    else:
        return None


def sign_up_with_email_and_password(email, password):
    request_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"email": email, "password": password, "returnSecureToken": True}

    resp = requests.post(request_url, headers=headers, json=data)
    if resp.status_code == 200:
        return resp.json()
    else:
        return None


def render_login_component():
    """Renders the Login/Signup UI"""
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None

    if st.session_state.user_info:
        return st.session_state.user_info  # Already logged in

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user = sign_in_with_email_and_password(email, password)
            if user:
                st.success("Success!")
                st.session_state.user_info = user
                st.session_state.user_id = user['localId']  # CRITICAL: Overwrite the random UUID
                st.rerun()
            else:
                st.error("Invalid email or password")

    with tab2:
        new_email = st.text_input("Email", key="signup_email")
        new_pass = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Create Account"):
            user = sign_up_with_email_and_password(new_email, new_pass)
            if user:
                st.success("Account created! Logging in...")
                st.session_state.user_info = user
                st.session_state.user_id = user['localId']
                st.rerun()
            else:
                st.error("Could not create account (Email might be taken)")

    return None