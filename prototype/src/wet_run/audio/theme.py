"""Theme music / ambient sound system.

Background music that loops. Different scenes have different themes:
- matrix_rain: Surface cyberspace (default)
- cyberspace: Deeper cyberspace
- chiba: Sprawl streets (NPC encounter)
- sense_net: Corporate data fortress (Data node)
- finn_office: Hub / menu

Implementation:
- Theme is a regular sound file (WAV)
- Plays in a separate thread that loops
- Can be stopped, faded, swapped
- Volume controlled by SoundConfig (theme_enabled + master_volume)
from __future__ import annotations

"""

import sys
import threading
import time
from pathlib import Path

from .config import SoundCategory, SoundConfig
from .sound_manager import (
    DEFAULT_SOUNDS,
    get_sound_manager,
)


def _log_warning(message: str, context: str = "") -> None:
    """Log a theme-subsystem warning without importing engine at module load.

    Engine imports can create circular dependencies (audio → engine → audio),
    so we lazily import the global logger.
    """
    try:
        from ..engine.logger import get_logger

        get_logger().warning(message, context)
    except Exception:
        # Last-resort fallback: stderr (logger itself may be unavailable
        # during interpreter shutdown or test setup).
        sys.stderr.write(f"[theme] WARN: {message} ({context})\n")
        sys.stderr.flush()


# Theme name → file path (relative to sounds_dir)
# NOTE: filenames use "theme_" prefix (e.g. theme_matrix_rain.wav), not "_theme" suffix
THEMES: dict[str, str] = {
    "matrix_rain": "theme_matrix_rain.wav",
    "cyberspace": "theme_cyberspace.wav",
    "chiba": "theme_chiba.wav",
    "sense_net": "theme_sense_net.wav",
    "finn_office": "theme_finn_office.wav",
    "loa_drum": "theme_loa_drum.wav",
    "loa_drum_fade": "theme_loa_drum_fade.wav",
    "loa_channel": "theme_loa_channel.wav",
    "manarase_drone": "theme_manarase_drone.wav",
    "industrial": "theme_industrial.wav",
    "broadcast": "theme_broadcast.wav",
    "hammer_alert": "theme_hammer_alert.wav",
}

# Default theme (when nothing is playing)
DEFAULT_THEME = "matrix_rain"


class ThemePlayer:
    """Background music player with loop support.

    Runs an internal thread that loops the theme WAV. Volume is
    controllable independently of the main SoundManager.
    """

    def __init__(self, sounds_dir: Path) -> None:
        """Initialize a theme player that reads WAV files from ``sounds_dir``."""
        self.sounds_dir = sounds_dir
        self._current_theme: str | None = None
        self._process: object | None = None  # subprocess.Popen
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._volume: float = 0.5  # Themes at 50% of master by default

    @property
    def current_theme(self) -> str | None:
        """Get the currently playing theme name, or None."""
        return self._current_theme

    @property
    def is_playing(self) -> bool:
        """True if a theme is currently playing."""
        return self._current_theme is not None

    def play(self, theme_name: str, config: SoundConfig) -> bool:
        """Start playing a theme.

        Stops any currently playing theme first.

        Args:
            theme_name: Name of the theme (e.g. "matrix_rain").
            config: SoundConfig (used to check theme_enabled).

        Returns:
            True if the theme started playing.
        """
        if not config.is_category_enabled(SoundCategory.THEME):
            return False
        if config.muted:
            return False

        if theme_name not in THEMES:
            return False

        self.stop()

        filename = THEMES[theme_name]
        path = self.sounds_dir / filename
        if not path.exists():
            # Theme file doesn't exist — fall back to a regular sound
            # (single-play, not looped). This is the placeholder
            # behavior until real theme files are available.
            return self._play_one_shot_fallback(theme_name, path, config)

        self._current_theme = theme_name
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop_theme,
            args=(path, config.master_volume * self._volume),
            daemon=True,
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        """Stop the currently playing theme."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        self._current_theme = None
        if self._process is not None:
            try:
                self._process.terminate()  # type: ignore[attr-defined]
            except Exception as e:
                _log_warning(
                    "Failed to terminate theme subprocess",
                    f"{type(e).__name__}: {e}",
                )
            self._process = None

    def set_volume(self, volume: float) -> None:
        """Set theme volume (0.0-1.0)."""
        self._volume = max(0.0, min(1.0, volume))

    def _play_one_shot_fallback(self, theme_name: str, path: Path, config: SoundConfig) -> bool:
        """Play a single-shot sound as a theme fallback.

        Used when the theme WAV file doesn't exist. Plays the
        associated sound effect once (no loop).
        """
        # Find the closest matching effect
        effect_name = f"theme/{theme_name}"
        if effect_name not in DEFAULT_SOUNDS:
            return False
        sm = get_sound_manager()
        return sm.play_with_config(effect_name, config)

    def _loop_theme(self, path: Path, volume: float) -> None:
        """Internal thread that loops the theme."""
        import subprocess

        while not self._stop_event.is_set():
            try:
                # Use afplay on macOS with --volume
                if sys.platform == "darwin":
                    self._process = subprocess.Popen(
                        ["afplay", "-v", str(int(volume * 100)), str(path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                elif sys.platform.startswith("linux"):
                    # aplay doesn't have volume control, use --volume
                    self._process = subprocess.Popen(
                        ["aplay", "-q", str(path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    # Windows: use winsound
                    try:
                        import winsound as _ws  # type: ignore[import-not-found]

                        self._process = None
                        _ws.PlaySound(
                            str(path),
                            _ws.SND_FILENAME | _ws.SND_ASYNC | _ws.SND_LOOP,
                        )
                    except Exception:
                        return

                # Wait for the process to finish (or stop signal)
                if self._process is not None:
                    self._process.wait()
                else:
                    # Windows mode: sleep then check stop event
                    while not self._stop_event.is_set():
                        time.sleep(0.1)

                if self._stop_event.is_set():
                    if self._process is not None:
                        try:
                            self._process.terminate()
                        except Exception as e:
                            _log_warning(
                                "Failed to terminate theme subprocess on stop",
                                f"{type(e).__name__}: {e}",
                            )
                    break
            except Exception as e:
                # Don't silently kill the loop — log so debug is possible.
                _log_warning(
                    "Theme loop iteration failed",
                    f"{type(e).__name__}: {e}",
                )
                break

        self._current_theme = None
        self._process = None


# Module-level singleton
_theme_player: ThemePlayer | None = None


def get_theme_player() -> ThemePlayer:
    """Get the global ThemePlayer singleton."""
    global _theme_player
    if _theme_player is None:
        sm = get_sound_manager()
        _theme_player = ThemePlayer(sm.sounds_dir)
    return _theme_player


def play_theme(theme_name: str, config: SoundConfig) -> bool:
    """Play a theme. Convenience function."""
    return get_theme_player().play(theme_name, config)


def stop_theme() -> None:
    """Stop the current theme. Convenience function."""
    if _theme_player is not None:
        _theme_player.stop()
