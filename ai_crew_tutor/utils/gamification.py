"""
Gamification logic: XP, levels, streaks, affinity
"""
from datetime import datetime, timedelta
from .storage import save_user_progress

def get_xp_for_level(level):
    """Calculate XP needed for a given level"""
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
    current_level_xp = get_xp_for_level(user_level - 1) if user_level > 1 else 0
    next_level_xp = get_xp_for_level(user_level)
    xp_progress = ((user_xp - current_level_xp) / (next_level_xp - current_level_xp)) * 100
    return max(0, min(100, xp_progress))

def add_xp(progress, amount, session_state):
    """Add XP and check for level up"""
    progress['xp'] += amount
    next_level_xp = get_xp_for_level(progress['level'])
    
    if progress['xp'] >= next_level_xp:
        progress['level'] += 1
        session_state.show_reward = {
            'type': 'level_up',
            'level': progress['level']
        }
        return True  # Level up occurred
    
    save_user_progress(progress)
    return False

def update_streak(progress, session_state):
    """Update daily streak"""
    today = datetime.now().date().isoformat()
    
    if progress['last_visit'] != today:
        last_date = datetime.fromisoformat(progress['last_visit']).date() if progress['last_visit'] else None
        yesterday = (datetime.now().date() - timedelta(days=1))
        
        if last_date == yesterday:
            progress['streak'] += 1
            if progress['streak'] % 7 == 0:
                session_state.show_reward = {
                    'type': 'streak',
                    'days': progress['streak']
                }
                add_xp(progress, 20, session_state)  # Bonus XP
        elif last_date != datetime.now().date():
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
    old_tier, _ = get_affinity_tier(old_affinity)
    new_tier, _ = get_affinity_tier(new_affinity)
    
    if new_tier != old_tier and new_tier != 'None':
        session_state.show_reward = {
            'type': 'affinity',
            'persona': persona_name,
            'tier': new_tier
        }
    
    save_user_progress(progress)