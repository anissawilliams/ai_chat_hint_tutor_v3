import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid
import requests  # <--- Added for server-side Analytics
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
            # Fail silently on localhost if config is missing, to avoid crashing app
            print(f"Firebase init skipped: {e}")
            return None

    return firestore.client()

# ---------------------------------------------------------
# GOOGLE ANALYTICS SETUP (SERVER-SIDE)
# ---------------------------------------------------------
def send_ga_event(event_name, params=None):
    """
    Send event directly to Google via Python (Bypasses Iframe issues)
    """
    ga_secrets = st.secrets.get("google_analytics", {})
    measurement_id = ga_secrets.get("measurement_id")
    api_secret = ga_secrets.get("api_secret")

    if not measurement_id or not api_secret:
        print("⚠️ GA Credentials missing. Event not sent.")
        return

    # Use the session_id as the client_id so events are linked to one user
    client_id = st.session_state.get('session_id', str(uuid.uuid4()))

    url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"

    payload = {
        "client_id": client_id,
        "events": [{
            "name": event_name,
            "params": params or {}
        }]
    }

    # Send async (don't await response to keep UI fast)
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
            
            # Log start
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

        # 2. Google Analytics (Python Side)
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
            except: pass

        # Google Analytics
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
            except: pass

        # Google Analytics
        send_ga_event('ask_question', {
            'persona': p,
            'question_length': len(question), # GA4 prefers numbers/strings over buckets usually
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
            except: pass
            
        # Google Analytics
        send_ga_event('click', {
            'element_name': element_name,
            'element_type': element_type
        })
        
    def get_session_duration(self):
        """Returns session duration in minutes"""
        delta = datetime.now() - st.session_state.session_start
        return delta.total_seconds() / 60

# ---------------------------------------------------------
# FRONTEND INJECTION (Optional - For Basic Page Views)
# ---------------------------------------------------------
def inject_google_analytics():
    """
    Only used for basic Page View tracking via browser.
    Events are now handled by Python above.
    """
    ga_id = st.secrets.get("google_analytics", {}).get("measurement_id")
    if not ga_id: return

    # We only inject the CONFIG, we do not try to send events here anymore
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