"""
Storage utilities for user progress and ratings
"""
import json
import os
import pandas as pd
from datetime import datetime

def get_base_dir():
    """Get the base directory of the application"""
    return os.path.dirname(os.path.dirname(__file__))

def load_user_progress():
    """Load user progress from JSON file"""
    filepath = os.path.join(get_base_dir(), "user_progress.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading progress: {e}")
    return {
        'level': 1,
        'xp': 0,
        'streak': 0,
        'last_visit': None,
        'affinity': {}
    }

def save_user_progress(data):
    """Save user progress to JSON file"""
    filepath = os.path.join(get_base_dir(), "user_progress.json")
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving progress: {e}")
        return False

def load_ratings():
    """Load historical ratings from JSON lines file"""
    filepath = os.path.join(get_base_dir(), "ratings.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = [json.loads(line) for line in f if line.strip()]
                if data:
                    return pd.DataFrame(data)
        except Exception as e:
            print(f"Error loading ratings: {e}")
    return pd.DataFrame()

def save_rating(rating_data):
    """Append a rating to the ratings file"""
    filepath = os.path.join(get_base_dir(), "ratings.json")
    try:
        with open(filepath, "a") as f:
            f.write(json.dumps(rating_data) + "\n")
        return True
    except Exception as e:
        print(f"Error saving rating: {e}")
        return False