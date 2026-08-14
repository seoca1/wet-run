"""Sound manager for Roguelike Sprawl.

Plays sound effects via subprocess + system tools:
- macOS: afplay (built-in)
- Linux: aplay (alsa-utils)
- Windows: winsound (built-in)

Generates placeholder WAV files on first use if missing.
Zero external Python dependencies (uses only standard library).
"""

from __future__ import annotations

import math
import random
import shutil
import subprocess
import sys
import threading
import wave
from pathlib import Path

from .config import SoundConfig

# --- Constants ---

SFX = "sfx"
AMBIENT = "ambient"
VOICE = "voice"
MUSIC = "music"

# --- Default sounds by category ---

# Category -> (filename, frequency_hz, duration_ms, kind)
# kind: 'sine' (pure tone), 'square' (8-bit), 'noise' (white noise burst)
DEFAULT_SOUNDS: dict[str, tuple[str, int, int, str]] = {
    # UI
    "ui/menu_select": ("ui_menu_select.wav", 600, 60, "sine"),
    "ui/menu_confirm": ("ui_menu_confirm.wav", 800, 80, "sine"),
    "ui/menu_cancel": ("ui_menu_cancel.wav", 300, 100, "sine"),
    "ui/error": ("ui_error.wav", 200, 200, "square"),
    "ui/notification": ("ui_notification.wav", 1000, 120, "sine"),
    # Story
    "story/text_typing": ("story_text_typing.wav", 1200, 30, "sine"),
    "story/dialogue_advance": ("story_dialogue_advance.wav", 500, 100, "sine"),
    "story/event_trigger": ("story_event_trigger.wav", 700, 250, "sine"),
    # Theme (graphic novel ambient) — ADR-0032
    "theme/matrix_rain": ("theme_matrix_rain.wav", 220, 4000, "sine"),
    "theme/cyberspace": ("theme_cyberspace.wav", 180, 4000, "sine"),
    "theme/chiba": ("theme_chiba.wav", 150, 4000, "noise"),
    "theme/sense_net": ("theme_sense_net.wav", 110, 4000, "sine"),
    "theme/finn_office": ("theme_finn_office.wav", 100, 4000, "sine"),
    "theme/loa_drum": ("theme_loa_drum.wav", 60, 1500, "square"),
    "theme/loa_drum_fade": ("theme_loa_drum_fade.wav", 80, 2000, "sine"),
    "theme/loa_channel": ("theme_loa_channel.wav", 90, 4000, "sine"),
    "theme/manarase_drone": ("theme_manarase_drone.wav", 130, 4000, "sine"),
    "theme/industrial": ("theme_industrial.wav", 70, 4000, "square"),
    "theme/broadcast": ("theme_broadcast.wav", 250, 3000, "noise"),
    "theme/hammer_alert": ("theme_hammer_alert.wav", 300, 2000, "square"),
    # Jack-in / Jack-out (movement)
    "movement/jack_in_zap": ("movement_jack_in_zap.wav", 800, 400, "noise"),
    "movement/jack_out_buzz": ("movement_jack_out_buzz.wav", 400, 400, "noise"),
    "movement/data_extract": ("movement_data_extract.wav", 1500, 250, "sine"),
    "movement/black_ice_roar": ("movement_black_ice_roar.wav", 80, 600, "square"),
    "movement/broadcast_static": ("movement_broadcast_static.wav", 200, 500, "noise"),
    "movement/broadcast_out": ("movement_broadcast_out.wav", 600, 800, "sine"),
    "movement/neon_hum": ("movement_neon_hum.wav", 250, 3000, "sine"),
    # Combat
    "combat/hit_normal": ("combat_hit_normal.wav", 150, 80, "noise"),
    "combat/hit_crit": ("combat_hit_crit.wav", 100, 200, "noise"),
    "combat/hit_miss": ("combat_hit_miss.wav", 400, 50, "sine"),
    "combat/skill_physical": ("combat_skill_physical.wav", 220, 200, "square"),
    "combat/skill_magic": ("combat_skill_magic.wav", 900, 300, "sine"),
    "combat/skill_heal": ("combat_skill_heal.wav", 1300, 400, "sine"),
    "combat/skill_buff": ("combat_skill_buff.wav", 1100, 200, "sine"),
    "combat/skill_debuff": ("combat_skill_debuff.wav", 250, 300, "square"),
    "combat/block": ("combat_block.wav", 350, 100, "noise"),
    "combat/stun": ("combat_stun.wav", 800, 250, "square"),
    "combat/victory": ("combat_victory.wav", 600, 600, "sine"),
    "combat/defeat": ("combat_defeat.wav", 200, 800, "sine"),
    # Movement
    "movement/nav_step": ("movement_nav_step.wav", 400, 40, "sine"),
    "movement/jack_in": ("movement_jack_in.wav", 300, 500, "sine"),
    "movement/jack_out": ("movement_jack_out.wav", 500, 500, "sine"),
    "movement/nav_block": ("movement_nav_block.wav", 150, 80, "square"),
    # Items
    "items/equip": ("items_equip.wav", 1000, 100, "sine"),
    "items/pickup": ("items_pickup.wav", 800, 80, "sine"),
    "items/cant": ("items_cant.wav", 250, 200, "square"),
}


class SoundManager:
    """Manages sound playback with auto-generation of placeholder WAVs.

    Thread-safe, non-blocking playback.
    Falls back to silent no-op if no system audio tool is available.
    """

    def __init__(self, sounds_dir: Path | None = None, volume: float = 0.2):
        """Initialize SoundManager with optional sounds directory and master volume.

        Args:
            sounds_dir: Directory containing WAV files. Defaults to data/sounds_test.
            volume: Master volume in 0.0-1.0 range, clamped.
        """
        self.sounds_dir = sounds_dir or Path("data/sounds_test")
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        self.volume = max(0.0, min(1.0, volume))
        self.muted = False
        self._lock = threading.Lock()
        self._process: subprocess.Popen[bytes] | None = None
        self._tool = self._detect_tool()
        self._ensure_sounds()

    def _detect_tool(self) -> str | None:
        """Detect which system audio tool is available."""
        if sys.platform == "darwin" and shutil.which("afplay"):
            return "afplay"
        if sys.platform.startswith("linux") and shutil.which("aplay"):
            return "aplay"
        if sys.platform.startswith("win"):
            return "winsound"
        return None

    def _ensure_sounds(self) -> None:
        """Generate placeholder WAV files for any missing sounds."""
        for _name, (filename, freq, dur_ms, kind) in DEFAULT_SOUNDS.items():
            path = self.sounds_dir / filename
            if not path.exists():
                _generate_wav(path, freq, dur_ms, kind)

    def is_available(self) -> bool:
        """Return True if a working audio backend is available."""
        return self._tool is not None

    def set_volume(self, volume: float) -> None:
        """Set master volume, clamped to [0.0, 1.0]."""
        self.volume = max(0.0, min(1.0, volume))

    def set_mute(self, muted: bool) -> None:
        """Set the global mute flag."""
        self.muted = muted

    def toggle_mute(self) -> bool:
        """Flip the mute state; returns the new value."""
        self.muted = not self.muted
        return self.muted

    def play(self, sound_name: str, pitch: float | None = None) -> bool:
        """Play a sound by name. Returns True if playback started.

        Args:
            sound_name: Name from DEFAULT_SOUNDS.
            pitch: Optional pitch multiplier (0.5 = half speed, 2.0 = double).
                   Currently informational only - placeholder WAVs are fixed.
                   Reserved for future sound bank with multiple pitches.
        """
        if self.muted:
            return False
        if sound_name not in DEFAULT_SOUNDS:
            return False
        filename, _freq, _dur, _kind = DEFAULT_SOUNDS[sound_name]
        path = self.sounds_dir / filename
        if not path.exists():
            return False
        return self._play_file(path)

    def play_with_config(
        self, sound_name: str, config: SoundConfig, pitch: float | None = None
    ) -> bool:
        """Play a sound respecting a SoundConfig (master + category).

        Returns False if:
        - Master muted
        - The sound's category is disabled in config
        - The sound name is unknown
        - The sound file doesn't exist
        """
        if not config.is_sound_playable(sound_name):
            return False
        # Use the master volume from config
        original_volume = self.volume
        self.set_volume(config.master_volume)
        try:
            return self.play(sound_name, pitch=pitch)
        finally:
            # Restore original volume (in case it differs)
            self.set_volume(original_volume)

    def play_category(self, category: str, sound_name: str, pitch: float | None = None) -> bool:
        """Play a sound from a specific category, ignoring config.

        Useful for tests or explicit overrides.
        """
        return self.play(sound_name, pitch=pitch)

    def _play_file(self, path: Path) -> bool:
        """Dispatch playback to the platform-specific backend; False if no tool."""
        if self._tool == "afplay":
            return self._play_afplay(path)
        if self._tool == "aplay":
            return self._play_aplay(path)
        if self._tool == "winsound":
            return self._play_winsound(path)
        return False

    def _play_afplay(self, path: Path) -> bool:
        """macOS afplay backend; True if playback started."""
        try:
            with self._lock:
                if self._process is not None and self._process.poll() is None:
                    self._process.terminate()
                vol_int = int(self.volume * 100)
                self._process = subprocess.Popen(
                    ["afplay", "-v", str(vol_int), str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return True
        except (OSError, FileNotFoundError):
            return False

    def _play_aplay(self, path: Path) -> bool:
        """Linux aplay backend; True if playback started."""
        try:
            with self._lock:
                if self._process is not None and self._process.poll() is None:
                    self._process.terminate()
                self._process = subprocess.Popen(
                    ["aplay", "-q", str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return True
        except (OSError, FileNotFoundError):
            return False

    def _play_winsound(self, path: Path) -> bool:
        """Windows winsound backend (background thread); True if dispatched."""
        if not sys.platform.startswith("win"):
            return False
        try:
            import winsound as _ws

            threading.Thread(
                target=lambda p: _ws.PlaySound(p, _ws.SND_FILENAME | _ws.SND_ASYNC),
                args=(str(path),),
                daemon=True,
            ).start()
            return True
        except (ImportError, RuntimeError):
            return False

    def stop_all(self) -> None:
        """Stop currently playing sound."""
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                self._process.terminate()
                self._process = None

    def list_sounds(self) -> list[str]:
        """List all available sound names."""
        return list(DEFAULT_SOUNDS.keys())


# --- Module-level singleton ---

_manager: SoundManager | None = None
_manager_lock = threading.Lock()


def get_sound_manager() -> SoundManager:
    """Get the global SoundManager singleton."""
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = SoundManager()
        return _manager


def get_sound_config() -> SoundConfig:
    """Get the global SoundConfig (creates default if missing).

    The SoundConfig is stored on the SoundManager for persistence.
    """
    sm = get_sound_manager()
    cfg: SoundConfig | None = getattr(sm, "_sound_config", None)
    if cfg is None:
        cfg = SoundConfig()
        sm._sound_config = cfg  # type: ignore[attr-defined]
        sm.set_volume(cfg.master_volume)
        sm.muted = cfg.muted
    return cfg


def play(sound_name: str) -> bool:
    """Play a sound via the global manager."""
    return get_sound_manager().play(sound_name)


def stop_all() -> None:
    """Stop all currently playing sounds."""
    get_sound_manager().stop_all()


def set_volume(volume: float) -> None:
    """Set master volume (0.0-1.0) on the global SoundManager."""
    get_sound_manager().set_volume(volume)


def set_mute(muted: bool) -> None:
    """Mute or unmute audio globally via the SoundManager."""
    get_sound_manager().set_mute(muted)


def toggle_mute() -> bool:
    """Toggle the global mute state; returns the new muted state."""
    return get_sound_manager().toggle_mute()


def is_available() -> bool:
    """Return True if the current platform has a working audio backend."""
    return get_sound_manager().is_available()


def list_sounds() -> list[str]:
    """Return the list of sound names available for playback."""
    return get_sound_manager().list_sounds()


# --- WAV generation ---

# Default SoundConfig (no config = play all)
_DEFAULT_CONFIG = SoundConfig()


def safe_play(sound_name: str) -> bool:
    """Play a sound, swallowing all errors. Returns True on success.

    Use this in engine modules where audio failure must not break gameplay.

    Respects a default SoundConfig (all categories on). For per-user
    control, use safe_play_with_config() instead.
    """
    try:
        sm = get_sound_manager()
        return sm.play_with_config(sound_name, _DEFAULT_CONFIG)
    except Exception:
        return False


def safe_play_with_config(sound_name: str, config: SoundConfig) -> bool:
    """Play a sound respecting a SoundConfig, swallowing errors.

    Use this when you have access to the user's SoundConfig (e.g. from
    AppState). Returns True on success, False otherwise.
    """
    try:
        sm = get_sound_manager()
        return sm.play_with_config(sound_name, config)
    except Exception:
        return False


_VALID_WAV_KINDS = ("sine", "square", "noise")


def _generate_wav(path: Path, freq: int, duration_ms: int, kind: str) -> None:
    """Generate a placeholder WAV file with a synthesized tone.

    Args:
        path: Destination WAV file path.
        freq: Tone frequency in Hz. Only relevant for ``sine``/``square`` kinds.
        duration_ms: Duration in milliseconds.
        kind: Waveform shape — one of ``"sine"``, ``"square"``, ``"noise"``.

    Raises:
        ValueError: If ``kind`` is not one of the supported waveform shapes.
    """
    if kind not in _VALID_WAV_KINDS:
        raise ValueError(
            f"Unknown WAV kind: {kind!r} (expected one of {_VALID_WAV_KINDS})"
        )

    sample_rate = 22050
    n_samples = int(sample_rate * duration_ms / 1000)
    amplitude = int(32767 * 0.3)

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        random.seed(freq)
        for i in range(n_samples):
            t = i / sample_rate
            if kind == "sine":
                sample = amplitude * math.sin(2 * math.pi * freq * t)
            elif kind == "square":
                sample = amplitude if math.sin(2 * math.pi * freq * t) >= 0 else -amplitude
            else:  # "noise"
                sample = amplitude * (random.random() * 2 - 1)

            # Apply fade in/out
            fade = min(i, n_samples - i, sample_rate // 20)
            if fade < sample_rate // 20:
                sample *= fade / (sample_rate // 20)

            wav.writeframes(int(sample).to_bytes(2, "little", signed=True))
