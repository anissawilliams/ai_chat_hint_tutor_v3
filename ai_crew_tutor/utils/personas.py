"""
Persona configuration and utilities
"""

# Persona unlock levels
PERSONA_UNLOCK_LEVELS = {
    'Nova': 1,
    'Spider-Gwen': 1,
    'Yoda': 1,
    'Elsa': 1,
    'Batman': 11,
    'Wednesday Addams': 11,
    'Shuri': 21,
    'Iron Man': 21,
    'Katniss Everdeen': 21
}

def build_persona_data(agents_config):
    """Build persona data structures from YAML config"""
    agents = agents_config.get('agents', {})
    
    persona_by_level = {}
    backgrounds = {}
    persona_options = {}
    persona_avatars = {}
    
    for name, data in agents.items():
        if not isinstance(data, dict):
            continue
        
        unlock_level = PERSONA_UNLOCK_LEVELS.get(name, 1)
        level_tier = 1 if unlock_level == 1 else (3 if unlock_level == 11 else 5)
        
        persona_by_level.setdefault(level_tier, []).append(name)
        
        # Make backgrounds TRANSPARENT
        bg = data.get('background', "linear-gradient(135deg, #667eea 0%, #764ba2 100%)")
        if 'rgb(' in bg:
            bg = bg.replace('rgb(', 'rgba(').replace(')', ', 0.85)')
        elif '#' in bg and 'gradient' in bg:
            bg = f"linear-gradient(rgba(0,0,0,0.15), rgba(0,0,0,0.15)), {bg}"
        
        backgrounds[name] = bg
        persona_options[name] = f"{data.get('role', name)} — {data.get('goal', '')}"
        persona_avatars[name] = data.get('avatar', "🧠")
    
    return persona_by_level, backgrounds, persona_options, persona_avatars

def get_available_personas(user_level):
    """Get list of personas available at current user level"""
    return [p for p, lvl in PERSONA_UNLOCK_LEVELS.items() if lvl <= user_level]

def is_persona_unlocked(persona_name, user_level):
    """Check if a persona is unlocked at current level"""
    return PERSONA_UNLOCK_LEVELS.get(persona_name, 1) <= user_level

def get_next_unlock(user_level):
    """Get the next persona to unlock and at what level"""
    for persona, level in sorted(PERSONA_UNLOCK_LEVELS.items(), key=lambda x: x[1]):
        if level > user_level:
            return persona, level
    return None, None