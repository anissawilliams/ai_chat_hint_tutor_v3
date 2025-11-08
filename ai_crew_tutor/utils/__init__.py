"""
Utils package for AI Java Tutor Pro
"""
from .storage import load_user_progress, save_user_progress, load_ratings, save_rating
from .gamification import (
    get_xp_for_level,
    get_level_tier,
    get_affinity_tier,
    calculate_xp_progress,
    add_xp,
    update_streak,
    add_affinity
)
from .personas import (
    PERSONA_UNLOCK_LEVELS,
    build_persona_data,
    get_available_personas,
    is_persona_unlocked,
    get_next_unlock
)
from .snippets import CODE_SNIPPETS, get_persona_snippets, get_unlocked_snippets

__all__ = [
    'load_user_progress',
    'save_user_progress',
    'load_ratings',
    'save_rating',
    'get_xp_for_level',
    'get_level_tier',
    'get_affinity_tier',
    'calculate_xp_progress',
    'add_xp',
    'update_streak',
    'add_affinity',
    'PERSONA_UNLOCK_LEVELS',
    'build_persona_data',
    'get_available_personas',
    'is_persona_unlocked',
    'get_next_unlock',
    'CODE_SNIPPETS',
    'get_persona_snippets',
    'get_unlocked_snippets',
]