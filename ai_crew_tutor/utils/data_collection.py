"""
Analytics and data collection module for AI Tutor
Handles Firebase and Google Analytics integration
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid
import streamlit.components.v1 as components


def initialize_firebase():
    """
    Initialize Firebase connection using Streamlit secrets

    Returns:
        firestore.Client: Firestore database client
    """
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate({
                "type": st.secrets["firebase"]["type"],
                "project_id": st.secrets["firebase"]["project_id"],
                "private_key": st.secrets["firebase"]["private_key"],
                "client_email": st.secrets["firebase"]["client_email"],
                "token_uri": st.secrets["firebase"]["token_uri"],
            })
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Failed to initialize Firebase: {e}")
            return None

    return firestore.client()


def inject_google_analytics():
    """Inject Google Analytics with debug mode enabled"""
    try:
        ga_id = st.secrets.get("google_analytics", {}).get("measurement_id", None)

        if not ga_id:
            st.warning("⚠️ Google Analytics measurement ID not found")
            return

        ga_code = f"""
        <!-- Google tag (gtag.js) with debug -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());
          gtag('config', '{ga_id}', {{
            'debug_mode': true,
            'send_page_view': true
          }});
          console.log('📊 Google Analytics initialized:', '{ga_id}');
        </script>
        """
        components.html(ga_code, height=0)

    except Exception as e:
        st.error(f"GA initialization error: {e}")
    pass
def track_ga_event(event_name, event_params=None):
    """
    Send custom events to Google Analytics
    """
    if event_params is None:
        event_params = {}

    try:
        params_str = ", ".join([f"'{k}': '{v}'" for k, v in event_params.items()])

        ga_event = f"""
        <script>
          (function() {{
            console.log('🔵 Attempting to send GA event: {event_name}');
            if (typeof gtag !== 'undefined') {{
              gtag('event', '{event_name}', {{{params_str}}});
              console.log('✅ GA event sent: {event_name}');
            }} else {{
              console.error('❌ gtag not defined for event: {event_name}');
            }}
          }})();
        </script>
        """
        components.html(ga_event, height=0)
    except Exception as e:
        st.sidebar.error(f"GA Error: {e}")
    pass

class TutorAnalytics:
    """
    Main analytics class for tracking user interactions and session data
    Handles both Firebase (detailed) and Google Analytics (aggregated) tracking
    """

    def __init__(self):
        """Initialize analytics and session tracking"""
        self.db = initialize_firebase()

        # Initialize session state variables
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.session_start = datetime.now()
            st.session_state.user_id = self._generate_user_id()
            st.session_state.interaction_count = 0
            st.session_state.clicks_tracked = []
            st.session_state.current_persona = None

            # Log session start
            self._log_session_start()

    def _generate_user_id(self):
        """
        Generate a unique user ID for the session

        Returns:
            str: UUID string for user identification
        """
        # You can enhance this with cookies or persistent storage
        return str(uuid.uuid4())

    def _log_session_start(self):
        """Log the start of a new user session"""
        if not self.db:
            return

        session_data = {
            'session_id': st.session_state.session_id,
            'user_id': st.session_state.user_id,
            'start_time': st.session_state.session_start,
            'status': 'active',
            'interaction_count': 0,
            'total_clicks': 0
        }

        try:
            self.db.collection('sessions').document(
                st.session_state.session_id
            ).set(session_data)

            # Track in Google Analytics
            track_ga_event('session_start', {
                'session_id': st.session_state.session_id[:8]
            })
        except Exception as e:
            st.error(f"Error logging session start: {e}")

    def track_persona_selection(self, persona_name):
        """
        Track when a user selects a tutor persona

        Args:
            persona_name (str): Name of the selected persona
        """
        if not self.db:
            return

        st.session_state.current_persona = persona_name

        event_data = {
            'session_id': st.session_state.session_id,
            'user_id': st.session_state.user_id,
            'timestamp': datetime.now(),
            'event_type': 'persona_selected',
            'persona': persona_name
        }

        try:
            # Firebase - detailed tracking
            self.db.collection('events').add(event_data)
            self.db.collection('sessions').document(
                st.session_state.session_id
            ).update({
                'persona': persona_name,
                'persona_selected_at': datetime.now()
            })

            # Google Analytics - aggregated tracking
            track_ga_event('persona_selected', {
                'persona_name': persona_name
            })
        except Exception as e:
            st.error(f"Error tracking persona selection: {e}")

    def track_question(self, question, response, persona=None):
        """
        Track each question asked and the AI response

        Args:
            question (str): User's question text
            response (str): AI tutor's response text
            persona (str, optional): Persona used for response
        """
        if not self.db:
            return

        st.session_state.interaction_count += 1

        interaction_data = {
            'session_id': st.session_state.session_id,
            'user_id': st.session_state.user_id,
            'timestamp': datetime.now(),
            'interaction_number': st.session_state.interaction_count,
            'question': question,
            'response': response,
            'response_length': len(response),
            'persona': persona or st.session_state.current_persona,
            'question_length': len(question)
        }

        try:
            # Firebase - store full interaction
            self.db.collection('interactions').add(interaction_data)

            # Update session interaction count
            self.db.collection('sessions').document(
                st.session_state.session_id
            ).update({
                'interaction_count': st.session_state.interaction_count,
                'last_interaction_at': datetime.now()
            })

            # Google Analytics - aggregated metrics (no PII)
            track_ga_event('question_asked', {
                'persona': persona or st.session_state.current_persona or 'none',
                'question_length_bucket': self._length_bucket(len(question)),
                'interaction_number': str(st.session_state.interaction_count)
            })
        except Exception as e:
            st.error(f"Error tracking question: {e}")

    def track_rating(self, rating, feedback_text=None, interaction_id=None):
        """
        Track user ratings and optional text feedback

        Args:
            rating (int): Star rating (1-5)
            feedback_text (str, optional): Additional text feedback
            interaction_id (str, optional): ID of the interaction being rated
        """
        if not self.db:
            return

        rating_data = {
            'session_id': st.session_state.session_id,
            'user_id': st.session_state.user_id,
            'timestamp': datetime.now(),
            'rating': rating,
            'feedback_text': feedback_text,
            'interaction_id': interaction_id,
            'persona': st.session_state.current_persona
        }

        try:
            # Firebase - detailed feedback
            self.db.collection('ratings').add(rating_data)

            # Update session with rating info
            self.db.collection('sessions').document(
                st.session_state.session_id
            ).update({
                'last_rating': rating,
                'rated_at': datetime.now(),
                'has_feedback_text': feedback_text is not None
            })

            # Google Analytics - rating metrics
            track_ga_event('rating_submitted', {
                'rating_value': str(rating) if rating else 'none',
                'has_feedback': 'yes' if feedback_text else 'no',
                'persona': st.session_state.current_persona or 'none'
            })
        except Exception as e:
            st.error(f"Error tracking rating: {e}")

    def track_click(self, element_name, element_type='button'):
        """
        Track button clicks and UI interactions

        Args:
            element_name (str): Name/label of the clicked element
            element_type (str): Type of element (button, link, etc.)
        """
        if not self.db:
            return

        click_data = {
            'session_id': st.session_state.session_id,
            'user_id': st.session_state.user_id,
            'timestamp': datetime.now(),
            'element_name': element_name,
            'element_type': element_type
        }

        st.session_state.clicks_tracked.append(element_name)

        try:
            # Firebase - detailed click data
            self.db.collection('clicks').add(click_data)

            # Update session click count
            self.db.collection('sessions').document(
                st.session_state.session_id
            ).update({
                'total_clicks': len(st.session_state.clicks_tracked)
            })

            # Google Analytics - click events
            track_ga_event('button_click', {
                'element_name': element_name,
                'element_type': element_type
            })
        except Exception as e:
            # Silently fail for click tracking
            pass

    def end_session(self):
        """Log session end and calculate final metrics"""
        if not self.db:
            return

        session_end = datetime.now()
        duration_seconds = (
                session_end - st.session_state.session_start
        ).total_seconds()

        session_summary = {
            'end_time': session_end,
            'duration_seconds': duration_seconds,
            'duration_minutes': round(duration_seconds / 60, 2),
            'total_interactions': st.session_state.interaction_count,
            'total_clicks': len(st.session_state.clicks_tracked),
            'status': 'completed'
        }

        try:
            # Firebase - update session
            self.db.collection('sessions').document(
                st.session_state.session_id
            ).update(session_summary)

            # Google Analytics - session metrics
            track_ga_event('session_end', {
                'duration_minutes': str(round(duration_seconds / 60, 1)),
                'total_interactions': str(st.session_state.interaction_count),
                'engagement_level': self._engagement_level(
                    st.session_state.interaction_count
                )
            })
        except Exception as e:
            st.error(f"Error ending session: {e}")

    def get_session_duration(self):
        """
        Get current session duration

        Returns:
            float: Session duration in minutes
        """
        duration = datetime.now() - st.session_state.session_start
        return duration.total_seconds() / 60

    def _length_bucket(self, length):
        """
        Categorize text length into buckets for analytics

        Args:
            length (int): Character count

        Returns:
            str: Length category (short, medium, long)
        """
        if length < 50:
            return 'short'
        elif length < 150:
            return 'medium'
        else:
            return 'long'

    def _engagement_level(self, interaction_count):
        """
        Calculate user engagement level based on interactions

        Args:
            interaction_count (int): Number of interactions

        Returns:
            str: Engagement level (none, low, medium, high)
        """
        if interaction_count == 0:
            return 'none'
        elif interaction_count <= 2:
            return 'low'
        elif interaction_count <= 5:
            return 'medium'
        else:
            return 'high'

    def track_survey_results(self, survey_data):
        """Track survey results"""
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
