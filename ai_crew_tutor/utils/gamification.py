"""
Gamification logic: XP, levels, streaks, affinity
"""
from datetime import datetime, timedelta
from utils.storage import save_user_progress

def get_xp_for_level(level):
    """Calculate XP needed for a given level"""
    # Linear curve: Level 1=100, Level 5=500, Level 10=1000
    return level * 100

def get_level_tier(level):
    """Get tier information for a level"""
    if level <= 10:
        return {'name': 'Beginner', 'color': '#43e97b', 'icon': '🌱'}
    elif level <= 20:
        return {'name': 'Intermediate', 'color': '#38f9d7', 'icon': '💪'}
    else:
        return {'name': 'Advanced', 'color': '#667eea', 'icon': '🚀'}

def get_affinity_tier(affinity):
    """Get affinity tier name and level"""
    if affinity >= 100:
        return 'Platinum', 4
    elif affinity >= 75:
        return 'Gold', 3
    elif affinity >= 50:
        return 'Silver', 2
    elif affinity >= 25:
        return 'Bronze', 1
    else:
        return 'None', 0

def calculate_xp_progress(user_xp, user_level):
    """Calculate XP progress percentage for current level"""
    # Prevent divide by zero or negative logic for Level 1
    current_level_base = get_xp_for_level(user_level - 1) if user_level > 1 else 0
    next_level_goal = get_xp_for_level(user_level)

    # Avoid division by zero
    range_span = next_level_goal - current_level_base
    if range_span <= 0: range_span = 100

    xp_progress = ((user_xp - current_level_base) / range_span) * 100
    return max(0, min(100, xp_progress))

def add_xp(progress, amount, session_state):
    """Add XP and check for level up"""
    progress['xp'] += amount
    next_level_xp = get_xp_for_level(progress['level'])
    leveled_up = False

    # Check if we crossed the threshold
    if progress['xp'] >= next_level_xp:
        progress['level'] += 1
        leveled_up = True

        # Trigger the UI popup
        session_state.show_reward = {
            'type': 'level_up',
            'level': progress['level']
        }

    # CRITICAL FIX: Save happens AFTER the logic, regardless of outcome
    save_user_progress(progress)

    return leveled_up

def update_streak(progress, session_state):
    """Update daily streak"""
    today = datetime.now().date().isoformat()

    # Only update if we haven't already logged today
    if progress.get('last_visit') != today:
        last_visit_str = progress.get('last_visit')
        last_date = datetime.fromisoformat(last_visit_str).date() if last_visit_str else None
        yesterday = (datetime.now().date() - timedelta(days=1))

        if last_date == yesterday:
            # Streak continues
            progress['streak'] += 1

            # Weekly bonus
            if progress['streak'] % 7 == 0:
                session_state.show_reward = {
                    'type': 'streak',
                    'days': progress['streak']
                }
                # Use recursive call but handle the save within it
                progress['xp'] += 20
        elif last_date != datetime.now().date():
            # Streak broken (unless it's the very first visit)
            if last_date is not None:
                progress['streak'] = 1
            else:
                progress['streak'] = 1

        progress['last_visit'] = today
        save_user_progress(progress)

def add_affinity(progress, persona_name, amount, session_state):
    """Add affinity points to a persona"""
    if 'affinity' not in progress:
        progress['affinity'] = {}

    old_affinity = progress['affinity'].get(persona_name, 0)
    new_affinity = old_affinity + amount
    progress['affinity'][persona_name] = new_affinity

    # Check for tier upgrade
    old_tier_name, _ = get_affinity_tier(old_affinity)
    new_tier_name, _ = get_affinity_tier(new_affinity)

    if new_tier_name != old_tier_name and new_tier_name != 'None':
        session_state.show_reward = {
            'type': 'affinity',
            'persona': persona_name,
            'tier': new_tier_name
        }
    
    save_user_progress(progress)