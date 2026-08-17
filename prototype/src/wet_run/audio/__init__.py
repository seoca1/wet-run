"""Audio module for Roguelike Sprawl.

Provides sound playback with zero external dependencies.
Uses subprocess + system tools (afplay on macOS, aplay on Linux).

Two-track audio system:
- SoundManager: One-shot sound effects (combat, UI, events, etc.)
- ThemePlayer: Looping background music

Configuration:
- SoundConfig: per-category on/off + master volume/mute
"""

from .config import (
    CATEGORY_KEY_BINDINGS,
    DEFAULT_CATEGORY_ENABLED,
    SOUND_CATEGORY_MAP,
    SoundCategory,
    SoundConfig,
    category_label,
)
from .sound_manager import (
    AMBIENT,
    MUSIC,
    SFX,
    VOICE,
    SoundManager,
    get_sound_config,
    get_sound_manager,
    is_available,
    list_sounds,
    play,
    safe_play,
    safe_play_with_config,
    set_mute,
    set_volume,
    stop_all,
    toggle_mute,
)
from .theme import (
    DEFAULT_THEME,
    THEMES,
    ThemePlayer,
    get_theme_player,
    play_theme,
    stop_theme,
)

__all__ = [
    # Config
    "SoundConfig",
    "SoundCategory",
    "SOUND_CATEGORY_MAP",
    "DEFAULT_CATEGORY_ENABLED",
    "CATEGORY_KEY_BINDINGS",
    "category_label",
    # Sound manager
    "SoundManager",
    "get_sound_manager",
    "get_sound_config",
    "play",
    "safe_play",
    "safe_play_with_config",
    "stop_all",
    "set_volume",
    "set_mute",
    "toggle_mute",
    "is_available",
    "list_sounds",
    "SFX",
    "AMBIENT",
    "VOICE",
    "MUSIC",
    # Theme
    "ThemePlayer",
    "get_theme_player",
    "play_theme",
    "stop_theme",
    "THEMES",
    "DEFAULT_THEME",
]
