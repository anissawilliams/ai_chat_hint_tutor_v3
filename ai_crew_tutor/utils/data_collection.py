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
            print(f"Firebase init skipped: {e}")
            return None
    return firestore.client()


# ---------------------------------------------------------
# GOOGLE ANALYTICS (SERVER-SIDE)
# ---------------------------------------------------------
def send_ga_event(event_name, params=None):
    """
    Send event directly to Google via Python
    """
    ga_secrets = st.secrets.get("google_analytics", {})
    measurement_id = ga_secrets.get("measurement_id")
    api_secret = ga_secrets.get("api_secret")

    # FIX: We DO NOT create the checkbox here anymore (prevents DuplicateKey error).
    # We just read the state. If the key doesn't exist, we default to True (Show logs).
    show_logs = st.session_state.get("debug_ga_toggle", True)

    if show_logs:
        # We use st.sidebar.write or caption, which IS allowed multiple times
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
        resp = requests.post(url, json=payload, timeout=1)
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

            # This is safe to call now
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
            st.success("Thanks for your feedback!")
            return True
        except Exception as e:
            st.error(f"Error writing survey results: {e}")
            return False

    def get_session_duration(self):
        delta = datetime.now() - st.session_state.session_start
        return delta.total_seconds() / 60

    # Add this inside class TutorAnalytics in utils/data_collection.py

    def track_learning_outcome(self, code_input, is_correct, attempt_number, persona_name):
        """
        Track student performance on code challenges.

        Args:
            code_input (str): The code the student wrote.
            is_correct (bool): Did they get it right?
            attempt_number (int): How many tries did this take?
            persona_name (str): Which tutor were they using?
        """
        if not self.db:
            return

        # Calculate time since last interaction (Time to Answer)
        now = datetime.now()
        last_interaction = st.session_state.get('last_interaction_time', st.session_state.session_start)
        seconds_taken = (now - last_interaction).total_seconds()

        # Update last interaction time for the next cycle
        st.session_state.last_interaction_time = now

        # 1. Firebase (Detailed for your dashboard)
        outcome_data = {
            'session_id': st.session_state.session_id,
            'timestamp': now,
            'persona': persona_name,
            'is_correct': is_correct,
            'attempt_number': attempt_number,
            'seconds_taken': seconds_taken,
            'code_length': len(code_input),
            # Optional: Store the actual code to analyze common mistakes later
             'student_code': code_input
        }

        try:
            self.db.collection('learning_outcomes').add(outcome_data)
        except:
            pass

        # 2. Google Analytics (Aggregated for trends)
        send_ga_event('code_submission', {
            'result': 'success' if is_correct else 'failure',
            'persona': persona_name,
            'attempt': attempt_number,
            'time_spent_seconds': int(seconds_taken)
        })


# ---------------------------------------------------------
# FRONTEND INJECTION
# ---------------------------------------------------------
def inject_google_analytics():
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