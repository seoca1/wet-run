"""BGM Manager — per-screen background music controller (Cycle 3 polish).

Centralized BGM controller that maps screen names to theme names and
provides volume control + crossfade between themes. Wraps the
existing ThemePlayer from audio/theme.py.

Pillar 4 safe: ephemeral session preference (no meta-progression).
Death does NOT preserve BGM state (new run = fresh start).

Usage:
    from wet_run.audio.bgm_manager import get_bgm_manager
    bgm = get_bgm_manager()
    bgm.register("MENU", "finn_office")
    bgm.register("HUB", "finn_office")
    bgm.register("MATRIX", "matrix_rain")
    bgm.register("COMBAT", "industrial")
    bgm.play_for_screen("MATRIX")
    bgm.set_volume(0.7)
    bgm.fade_out(duration_ms=500)
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import SoundConfig
from .theme import (
    THEMES,
    play_theme,
    stop_theme,
)

# Default BGM volume (fraction of master).
DEFAULT_BGM_VOLUME: float = 0.6

# Crossfade duration in milliseconds.
DEFAULT_CROSSFADE_MS: int = 500


@dataclass
class BgmSettings:
    """Per-session BGM settings (Pillar 4 ephemeral)."""

    volume: float = DEFAULT_BGM_VOLUME
    muted: bool = False
    current_theme: str | None = None


class BgmManager:
    """Centralized BGM controller with per-screen mapping.

    Wraps the existing ThemePlayer to provide:
    - Per-screen BGM registration
    - Crossfade between themes
    - Volume and mute control
    - Settings tracking
    """

    def __init__(self) -> None:
        """Initialize an empty BGM manager with default settings."""
        self._screen_themes: dict[str, str] = {}
        self._settings = BgmSettings()
        self._registered = False

    def register(self, screen_name: str, theme_name: str) -> None:
        """Map a screen name to a BGM theme.

        Args:
            screen_name: Screen identifier (e.g. "MENU", "MATRIX", "COMBAT").
            theme_name: Theme name from THEMES dict (e.g. "matrix_rain", "finn_office").
        """
        if theme_name not in THEMES:
            raise ValueError(f"Unknown theme '{theme_name}'. Available: {sorted(THEMES.keys())}")
        self._screen_themes[screen_name] = theme_name
        self._registered = True

    def register_defaults(self) -> None:
        """Register default screen→theme mapping (Pillar 1/5 alignment)."""
        self.register("MENU", "finn_office")
        self.register("HUB", "finn_office")
        self.register("MATRIX", "matrix_rain")
        self.register("MATRIX_DEEP", "cyberspace")
        self.register("COMBAT", "industrial")
        self.register("COMBAT_BOSS", "hammer_alert")
        self.register("NPC", "chiba")
        self.register("SENSE_NET", "sense_net")
        self.register("LOA", "loa_drum")
        self.register("CINEMATIC", "loa_drum_fade")
        self.register("SALVATION", "manarase_drone")

    def play_for_screen(self, screen_name: str) -> bool:
        """Play the BGM theme mapped to screen_name.

        Args:
            screen_name: Screen identifier.

        Returns:
            True if theme was played, False if no mapping exists.
        """
        theme_name = self._screen_themes.get(screen_name)
        if theme_name is None:
            return False
        return self.play_theme(theme_name)

    def play_theme(self, theme_name: str) -> bool:
        """Play a BGM theme by name.

        Args:
            theme_name: Theme name from THEMES dict.

        Returns:
            True if theme was played, False on error.
        """
        if theme_name not in THEMES:
            return False
        if self._settings.muted:
            self._settings.current_theme = theme_name
            return True
        config = SoundConfig(master_volume=self._settings.volume)
        success = play_theme(theme_name, config)
        if success:
            self._settings.current_theme = theme_name
        return success

    def stop(self) -> None:
        """Stop the currently playing BGM."""
        stop_theme()
        self._settings.current_theme = None

    def fade_out(self, duration_ms: int = DEFAULT_CROSSFADE_MS) -> None:
        """Stop the currently playing BGM (simulated crossfade).

        Note: True crossfade requires async audio. This implementation
        simply stops playback — the next play_for_screen() will start
        the new theme fresh.
        """
        del duration_ms  # Unused: real crossfade deferred to async audio
        self.stop()

    def set_volume(self, volume: float) -> None:
        """Set BGM volume (0.0 to 1.0)."""
        volume = max(0.0, min(1.0, volume))
        self._settings.volume = volume
        if self._settings.current_theme is not None and not self._settings.muted:
            config = SoundConfig(master_volume=volume)
            play_theme(self._settings.current_theme, config)

    def mute(self) -> None:
        """Mute BGM (stops current playback but remembers the theme)."""
        if not self._settings.muted:
            self._settings.muted = True
            self.stop()

    def unmute(self) -> None:
        """Unmute BGM (does not auto-resume; call play_for_screen)."""
        self._settings.muted = False

    def toggle_mute(self) -> bool:
        """Toggle BGM mute, returns new muted state."""
        if self._settings.muted:
            self.unmute()
        else:
            self.mute()
        return self._settings.muted

    @property
    def current_theme(self) -> str | None:
        """Currently playing theme, or None."""
        return self._settings.current_theme

    @property
    def is_muted(self) -> bool:
        """Whether BGM is currently muted."""
        return self._settings.muted

    @property
    def volume(self) -> float:
        """Current BGM volume (0.0 to 1.0)."""
        return self._settings.volume

    @property
    def registered_screens(self) -> list[str]:
        """List of registered screen names."""
        return sorted(self._screen_themes.keys())


# Module-level singleton (Pillar 1 ephemeral).
_singleton: BgmManager | None = None


def get_bgm_manager() -> BgmManager:
    """Get the singleton BGM manager (created on first call)."""
    global _singleton
    if _singleton is None:
        _singleton = BgmManager()
    return _singleton


def reset_bgm_manager() -> None:
    """Reset the singleton (for test isolation / new run)."""
    global _singleton
    _singleton = None


__all__ = [
    "BgmManager",
    "BgmSettings",
    "DEFAULT_BGM_VOLUME",
    "DEFAULT_CROSSFADE_MS",
    "get_bgm_manager",
    "reset_bgm_manager",
]
