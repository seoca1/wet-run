"""Settings UI: volume, mute, and audio preferences.

Provides helper functions for global hotkeys:
- M = master mute toggle
- +/- = master volume up/down
- T/E/K/B/V/I = per-category toggle (theme/events/keys/combat/movement/items)
"""

from __future__ import annotations

import tcod.console

from ..audio import sound_manager
from ..audio.config import SoundCategory, SoundConfig


def get_volume() -> float:
    """Get current master volume (0.0 - 1.0)."""
    return sound_manager.get_sound_manager().volume


def set_volume(volume: float) -> None:
    """Set master volume (clamped to 0.0 - 1.0)."""
    sound_manager.set_volume(volume)


def adjust_volume(delta: float) -> float:
    """Adjust master volume by delta. Returns new volume.

    Args:
        delta: Signed adjustment. +0.1 = louder, -0.1 = quieter.

    Returns:
        New volume value (0.0 - 1.0).
    """
    sm = sound_manager.get_sound_manager()
    new_vol = max(0.0, min(1.0, sm.volume + delta))
    sm.set_volume(new_vol)
    return new_vol


def is_muted() -> bool:
    """Return True if audio is muted."""
    return sound_manager.get_sound_manager().muted


def toggle_mute() -> bool:
    """Toggle mute. Returns new muted state."""
    return sound_manager.toggle_mute()


def get_sound_config() -> SoundConfig:
    """Get the singleton SoundConfig (creates default if missing).

    Delegates to the audio module's get_sound_config() to ensure a
    single source of truth.
    """
    from ..audio import get_sound_config as _get_sound_config

    return _get_sound_config()


def ensure_sound_config(state: object) -> SoundConfig:
    """Get state.sound_config, creating if missing.

    Args:
        state: AppState (or any object with a sound_config attribute).
    """
    cfg: SoundConfig | None = getattr(state, "sound_config", None)
    if cfg is None:
        cfg = SoundConfig()
        state.sound_config = cfg  # type: ignore[attr-defined]
    return cfg


def toggle_category(category: SoundCategory | str) -> bool:
    """Toggle a sound category on/off. Returns the new state."""
    config = get_sound_config()
    return config.toggle_category(category)


def set_category(category: SoundCategory | str, enabled: bool) -> None:
    """Set a sound category on or off."""
    config = get_sound_config()
    config.set_category_enabled(category, enabled)


def render_settings_overlay(console: tcod.console.Console, x: int, y: int) -> None:
    """Render a small audio status overlay.

    Args:
        console: tcod console to draw on.
        x: X coordinate.
        y: Y coordinate.
    """
    sm = sound_manager.get_sound_manager()
    mute_label = "MUTED" if sm.muted else "ON"
    vol_pct = int(sm.volume * 100)
    console.print(x=x, y=y, string=f"Audio: {mute_label}  Volume: {vol_pct}%", fg=(200, 200, 200))
