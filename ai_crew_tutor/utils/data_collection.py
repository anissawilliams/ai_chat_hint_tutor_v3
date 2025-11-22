import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid
import requests  # Required for server-side GA tracking
import streamlit.components.v1 as components


# ---------------------------------------------------------
# FIREBASE SETUP
# ---------------------------------------------------------
def initialize_firebase():
    """Initialize Firebase connection"""
    if not firebase_admin._apps:
        try:
            # Check if secrets exist
            if "firebase" not in st.secrets:
                return None

            cred = credentials.Certificate({
                "type": st.secrets["firebase"]["type"],
                "project_id": st.secrets["firebase"]["project_id"],
                "private_key": st.secrets["firebase"]["private_key"],
                "client_email": st.secrets["firebase"]["client_email"],
                "token_uri": st.secrets["firebase"]["token_uri"],
            })
            firebase_admin.initialize_app(cred)
        except Exception as e:
            # Fail silently on localhost if config is missing to avoid crash
            print(f"Firebase init skipped: {e}")
            return None

    return firestore.client()


# ---------------------------------------------------------
# GOOGLE ANALYTICS (SERVER-SIDE)
# ---------------------------------------------------------
def send_ga_event(event_name, params=None):
    """
    Send event directly to Google via Python (Bypasses Iframe issues)
    """
    ga_secrets = st.secrets.get("google_analytics", {})
    measurement_id = ga_secrets.get("measurement_id")
    api_secret = ga_secrets.get("api_secret")

    if not measurement_id or not api_secret:
        # If secrets are missing, skip GA but don't crash
        return

    client_id = st.session_state.get('session_id', str(uuid.uuid4()))
    url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"

    payload = {
        "client_id": client_id,
        "events": [{
            "name": event_name,
            "params": params or {}
        }]
    }

    try:
        requests.post(url, json=payload, timeout=1)
    except Exception as e:
        print(f"GA Send Error: {e}")


# ---------------------------------------------------------
# MAIN ANALYTICS CLASS
# ---------------------------------------------------------
class TutorAnalytics:
    def __init__(self):
        self.db = initialize_firebase()

        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.session_start = datetime.now()
            st.session_state.user_id = self._generate_user_id()
            st.session_state.interaction_count = 0
            st.session_state.clicks_tracked = []
            st.session_state.current_persona = None

            self._log_session_start()

    def _generate_user_id(self):
        return str(uuid.uuid4())

    def _log_session_start(self):
        # 1. Firebase
        if self.db:
            try:
                session_data = {
                    'session_id': st.session_state.session_id,
                    'user_id': st.session_state.user_id,
                    'start_time': st.session_state.session_start,
                    'status': 'active',
                    'platform': 'streamlit'
                }
                self.db.collection('sessions').document(st.session_state.session_id).set(session_data)
            except Exception as e:
                print(f"Firebase Error: {e}")

        # 2. Google Analytics
        send_ga_event('session_start', {'session_id': st.session_state.session_id})

    def track_persona_selection(self, persona_name):
        st.session_state.current_persona = persona_name

        # Firebase
        if self.db:
            try:
                self.db.collection('sessions').document(st.session_state.session_id).update({
                    'persona': persona_name,
                    'persona_selected_at': datetime.now()
                })
            except:
                pass

        # GA
        send_ga_event('select_persona', {'persona_name': persona_name})

    def track_question(self, question, response, persona=None):
        st.session_state.interaction_count += 1
        p = persona or st.session_state.current_persona

        # Firebase
        if self.db:
            try:
                interaction_data = {
                    'session_id': st.session_state.session_id,
                    'timestamp': datetime.now(),
                    'question': question,
                    'response_length': len(response),
                    'persona': p
                }
                self.db.collection('interactions').add(interaction_data)
            except:
                pass

        # GA
        send_ga_event('ask_question', {
            'persona': p,
            'question_length': len(question),
            'interaction_count': st.session_state.interaction_count
        })

    def track_click(self, element_name, element_type='button'):
        # Firebase
        if self.db:
            try:
                self.db.collection('clicks').add({
                    'session_id': st.session_state.session_id,
                    'element': element_name,
                    'timestamp': datetime.now()
                })
            except:
                pass

        # GA
        send_ga_event('click', {
            'element_name': element_name,
            'element_type': element_type
        })

    def track_survey_results(self, survey_data):
        """Track survey results (Restored)"""
        if not self.db:
            st.error("Firestore not initialized")
            return False

        try:
            self.db.collection("survey_responses").add({
                **survey_data,
                "session_id": st.session_state.session_id,
                "user_id": st.session_state.user_id,
                "timestamp": datetime.now()
            })
            st.success("Thanks for your feedback! Your response has been recorded.")
            return True
        except Exception as e:
            st.error(f"Error writing survey results: {e}")
            return False

    def get_session_duration(self):
        """Returns session duration in minutes"""
        delta = datetime.now() - st.session_state.session_start
        return delta.total_seconds() / 60


# In utils/data_collection.py

    def send_ga_event(event_name, params=None):
        """
        Send event directly to Google via Python
        Includes VISUAL DEBUGGING so you know it works.
        """
        ga_secrets = st.secrets.get("google_analytics", {})
        measurement_id = ga_secrets.get("measurement_id")
        api_secret = ga_secrets.get("api_secret")

        # 1. Visual Debugger Checkbox
        # This creates a checkbox in the sidebar.
        # The key="debug_ga_toggle" saves the True/False value into st.session_state
        st.sidebar.checkbox("📡 Show Analytics Logs", value=True, key="debug_ga_toggle")

        # 2. Get the value safely from GLOBAL session state
        show_logs = st.session_state.get("debug_ga_toggle", True)

        if show_logs:
            st.sidebar.caption(f"📤 Sending: `{event_name}`")

        if not measurement_id or not api_secret:
            if show_logs:
                st.sidebar.error("⚠️ Missing GA Secrets")
            return

        client_id = st.session_state.get('session_id', str(uuid.uuid4()))
        url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"

        payload = {
            "client_id": client_id,
            "events": [{
                "name": event_name,
                "params": params or {}
            }]
        }

        try:
            # Use a short timeout so we don't freeze the app if Google is slow
            resp = requests.post(url, json=payload, timeout=1)

            # Check for success (204 means accepted)
            if resp.status_code == 204:
                if show_logs:
                    st.sidebar.success(f"✅ GA Sent: {event_name}")
            else:
                if show_logs:
                    st.sidebar.warning(f"⚠️ GA Status: {resp.status_code}")

        except Exception as e:
            if show_logs:
                st.sidebar.error(f"❌ GA Failed: {e}")

# ---------------------------------------------------------
# FRONTEND INJECTION (Basic Page View Only)
# ---------------------------------------------------------
def inject_google_analytics():
    """
    Injects GA config only (Events handled by Python)
    """
    ga_id = st.secrets.get("google_analytics", {}).get("measurement_id")
    if not ga_id: return

    ga_code = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{ga_id}');
    </script>
    """
    components.html(ga_code, height=0)