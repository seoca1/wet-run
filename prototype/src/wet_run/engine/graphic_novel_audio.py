"""Sound cues for the graphic novel view (ADR-0032).

Maps scene-level sound names (from scene JSON files) to actual
SoundManager sounds. Provides a single entry point for playing
sounds at scene/dialogue transitions.

Scene JSON sound values are short identifiers like:
    "chiba_rain_loop", "loa_drum", "matrix_rain", "finn_office",
    "neon_hum", "jack_in_zap", "jack_out_buzz", "hammer_alert",
    "data_extract", "broadcast_static", "loa_drum_fade",
    "broadcast_out", "manarase_drone", "black_ice_roar"

These are mapped to actual DEFAULT_SOUNDS names with proper prefixes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..audio.sound_manager import SoundManager

# Map scene-level sound names → actual DEFAULT_SOUNDS keys
SCENE_SOUND_MAP: dict[str, str] = {
    # Theme (ambient backgrounds)
    "chiba_rain_loop": "theme/chiba",
    "matrix_rain": "theme/matrix_rain",
    "finn_office": "theme/finn_office",
    "loa_drum": "theme/loa_drum",
    "loa_drum_fade": "theme/loa_drum_fade",
    "loa_channel": "theme/loa_channel",
    "manarase_drone": "theme/manarase_drone",
    "industrial": "theme/industrial",
    "broadcast": "theme/broadcast",
    "hammer_alert": "theme/hammer_alert",
    "shibuya_traffic": "theme/sense_net",  # Shibuya cyberpunk → sense_net ambient
    # ADR-0049: alias scene keys that include the category prefix
    "theme_broadcast": "theme/broadcast",
    "theme_hammer_alert": "theme/hammer_alert",
    "theme_industrial": "theme/industrial",
    "theme_loa_drum": "theme/loa_drum",
    "theme_loa_drum_fade": "theme/loa_drum_fade",
    "theme_manarase_drone": "theme/manarase_drone",
    "movement_neon_hum": "movement/neon_hum",
    # Atmospheric SFX
    "neon_hum": "movement/neon_hum",
    "hvac_hum": "movement/neon_hum",  # Corporate building HVAC → ambient building hum
    # Jack-in/out
    "jack_in_zap": "movement/jack_in_zap",
    "jack_out_buzz": "movement/jack_out_buzz",
    # Data extraction
    "data_extract": "movement/data_extract",
    # ICE / boss
    "black_ice_roar": "movement/black_ice_roar",
    # Broadcast
    "broadcast_static": "movement/broadcast_static",
    "broadcast_out": "movement/broadcast_out",
}


def resolve_sound(scene_sound: str | None) -> str | None:
    """Map a scene-level sound id to a DEFAULT_SOUNDS key.

    Args:
        scene_sound: Sound id from scene JSON (e.g. "chiba_rain_loop").
            Can also be a DEFAULT_SOUNDS key directly (e.g. "theme/matrix_rain").

    Returns:
        The DEFAULT_SOUNDS key, or None if unmapped.
    """
    if scene_sound is None:
        return None
    if scene_sound in SCENE_SOUND_MAP:
        return SCENE_SOUND_MAP[scene_sound]
    # If it's already a DEFAULT_SOUNDS key, return as-is
    if "/" in scene_sound:
        return scene_sound
    return None


def play_scene_sound(
    sound_manager: SoundManager | None,
    scene_sound: str | None,
) -> bool:
    """Play a scene sound (with config respected).

    Args:
        sound_manager: Optional SoundManager instance. If None, no-op.
        scene_sound: Sound id from scene JSON.

    Returns:
        True if playback started, False otherwise.
    """
    if sound_manager is None:
        return False
    resolved = resolve_sound(scene_sound)
    if resolved is None:
        return False
    return sound_manager.play(resolved)


# Track which sounds have been played (to avoid spamming)
_played_cache: set[str] = set()


def play_once(
    sound_manager: SoundManager | None,
    scene_sound: str | None,
    *,
    reset: bool = False,
) -> bool:
    """Play a sound only once per session (per scene_id+dialogue_id combo).

    Args:
        sound_manager: Optional SoundManager.
        scene_sound: Sound id from scene JSON.
        reset: If True, clear the played cache.

    Returns:
        True if playback started, False if already played or no manager.
    """
    if reset:
        _played_cache.clear()
    if scene_sound is None:
        return False
    if scene_sound in _played_cache:
        return False
    if play_scene_sound(sound_manager, scene_sound):
        _played_cache.add(scene_sound)
        return True
    return False


def get_category(scene_sound: str | None) -> str | None:
    """Get the SoundCategory for a scene sound.

    Returns:
        Category name (e.g. "theme", "movement") or None.
    """
    resolved = resolve_sound(scene_sound)
    if resolved is None:
        return None
    if "/" in resolved:
        return resolved.split("/")[0]
    return None
