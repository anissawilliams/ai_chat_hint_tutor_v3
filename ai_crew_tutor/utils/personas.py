"""
Utils for managing Persona metadata and availability.
"""

# No more lock levels! Everyone is free!
# We keep the list here to ensure ordering, or you can grab it dynamically from the YAML.

def build_persona_data(agents_config):
    """
    Parses the agents.yaml to get avatars and background styles.
    """
    if 'agents' not in agents_config:
        return {}, {}, [], {}

    persona_avatars = {}
    backgrounds = {}
    persona_options = []

    # Sort alphabetically or define a custom order here if you want
    for name, data in agents_config['agents'].items():
        persona_options.append(name)
        persona_avatars[name] = data.get('avatar', '🤖')
        backgrounds[name] = data.get('background', 'linear-gradient(to right, #4facfe, #00f2fe)')

    # We return a simplified structure since we don't need 'persona_by_level' anymore
    return {}, backgrounds, persona_options, persona_avatars

def get_available_personas(user_level):
    """
    Legacy compatibility: Returns ALL personas regardless of level.
    """
    # This function might be called by older components, so we keep it safe.
    # But effectively, it does nothing now.
    return []

def get_next_unlock(user_level):
    """
    Legacy compatibility: There are no more unlocks.
    """
    return None, None