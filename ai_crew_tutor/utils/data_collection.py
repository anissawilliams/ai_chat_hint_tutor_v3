"""
Analytics and Data Collection
Includes: Google Analytics (Server-side), Firebase Logging, and AI Feedback Loop.
"""
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid
import requests
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
# AI TRAINING FEEDBACK (The Missing Functions)
# ---------------------------------------------------------
def save_training_feedback(persona, bad_response, critique):
    """
    Saves a critique of the AI to Firebase to 'train' future responses.
    """
    db = initialize_firebase()
    if not db: return

    data = {
        "persona": persona,
        "bad_response": bad_response,
        "critique": critique,
        "timestamp": datetime.now()
    }
    try:
        db.collection('ai_training_feedback').add(data)
    except Exception as e:
        print(f"Error saving feedback: {e}")


def get_recent_feedback(persona, limit=3):
    """
    Retrieves the last few critiques to inject into the AI's prompt.
    """
    db = initialize_firebase()
    if not db: return []

    try:
        # Get feedback specific to this persona
        docs = db.collection('ai_training_feedback') \
            .where('persona', '==', persona) \
            .order_by('timestamp', direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .stream()

        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"Feedback fetch error: {e}")
        return []


# ---------------------------------------------------------
# GOOGLE ANALYTICS (SERVER-SIDE)
# ---------------------------------------------------------
def send_ga_event(event_name, params=None):
    """Send event directly to Google via Python"""
    ga_secrets = st.secrets.get("google_analytics", {})
    measurement_id = ga_secrets.get("measurement_id")
    api_secret = ga_secrets.get("api_secret")

    # Visual Debugger (Reads state, doesn't create widget)
    show_logs = st.session_state.get("debug_ga_toggle", True)

    if show_logs:
        st.sidebar.caption(f"📤 Sending: `{event_name}`")

    if not measurement_id or not api_secret:
        return

    client_id = st.session_state.get('session_id', str(uuid.uuid4()))
    url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"

    payload = {
        "client_id": client_id,
        "events": [{"name": event_name, "params": params or {}}]
    }

    try:
        requests.post(url, json=payload, timeout=1)
    except Exception:
        pass


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

            self._log_session_start()

    def _generate_user_id(self):
        return str(uuid.uuid4())

    def _log_session_start(self):
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
            except:
                pass
        send_ga_event('session_start', {'session_id': st.session_state.session_id})

    def track_persona_selection(self, persona_name):
        st.session_state.current_persona = persona_name
        if self.db:
            try:
                self.db.collection('sessions').document(st.session_state.session_id).update({
                    'persona': persona_name,
                    'persona_selected_at': datetime.now()
                })
            except:
                pass
        send_ga_event('select_persona', {'persona_name': persona_name})

    def track_question(self, question, response, persona=None):
        st.session_state.interaction_count += 1
        p = persona or st.session_state.current_persona
        if self.db:
            try:
                self.db.collection('interactions').add({
                    'session_id': st.session_state.session_id,
                    'timestamp': datetime.now(),
                    'question': question,
                    'response_length': len(response),
                    'persona': p
                })
            except:
                pass
        send_ga_event('ask_question', {
            'persona': p,
            'interaction_count': st.session_state.interaction_count
        })

    def track_click(self, element_name, element_type='button'):
        if self.db:
            try:
                self.db.collection('clicks').add({
                    'session_id': st.session_state.session_id,
                    'element': element_name,
                    'timestamp': datetime.now()
                })
            except:
                pass
        send_ga_event('click', {'element_name': element_name})

    def track_learning_outcome(self, code_input, is_correct, attempt_number, persona_name):
        now = datetime.now()
        last_interaction = st.session_state.get('last_interaction_time', st.session_state.session_start)
        seconds_taken = (now - last_interaction).total_seconds()
        st.session_state.last_interaction_time = now

        user_prof = st.session_state.user_progress.get('proficiency', 'Unknown')

        if self.db:
            try:
                self.db.collection('learning_outcomes').add({
                    'session_id': st.session_state.session_id,
                    'timestamp': now,
                    'persona': persona_name,
                    'is_correct': is_correct,
                    'attempt_number': attempt_number,
                    'seconds_taken': seconds_taken,
                    'student_proficiency': user_prof
                })
            except:
                pass

        send_ga_event('code_submission', {
            'result': 'success' if is_correct else 'failure',
            'persona': persona_name,
            'proficiency': user_prof,
            'attempt': attempt_number
        })


def inject_google_analytics():
    """Injects GA config only"""
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