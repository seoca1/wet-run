"""Game settings system with persistence and validation.

Provides 6 categories of settings:
  - Audio (master/music/sfx/voice volumes, mute, per-category)
  - Display (animation speed, color theme, vignette, FPS, glyphs)
  - Input (key bindings, confirm/cancel/move/pause)
  - Language (ko/en/both, subtitle mode)
  - Gameplay (difficulty, damage modifier, combo window, auto-save)
  - About (version, reset)

All settings are stored in a single GameSettings dataclass with
sensible defaults. JSON serialization for save/load.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


# ----------------------------------------------------------------------------
# Enums
# ----------------------------------------------------------------------------


class ColorTheme(StrEnum):
    """Available color themes."""

    MATRIX = "matrix"  # Green/cyan cyberpunk
    CYBERPUNK = "cyberpunk"  # Magenta/yellow neon
    MONO = "mono"  # Grayscale retro


class GlyphStyle(StrEnum):
    """Glyph rendering style."""

    ASCII = "ascii"  # Basic ASCII only
    UNICODE = "unicode"  # Unicode block characters


class Language(StrEnum):
    """Display language."""

    KOREAN = "ko"
    ENGLISH = "en"
    JAPANESE = "ja"
    CHINESE = "zh"
    BOTH = "both"


class SubtitleMode(StrEnum):
    """How to show translated text."""

    OFF = "off"  # English only
    SUBTITLE = "subtitle"  # English + Korean
    REPLACE = "replace"  # Korean only


class Difficulty(StrEnum):
    """Game difficulty."""

    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    NIGHTMARE = "nightmare"


# ----------------------------------------------------------------------------
# Settings dataclass
# ----------------------------------------------------------------------------


@dataclass(slots=True)
class GameSettings:
    """All user-configurable game settings.

    Defaults are tuned for a quiet, accessible experience:
    - Low volume (0.2) to be unobtrusive
    - KEYS category off (per user request)
    - Korean + English subtitles
    - Normal difficulty
    - 3.5s combo window
    """

    # ---- Audio ----
    master_volume: float = 0.2
    music_volume: float = 0.2
    sfx_volume: float = 0.5
    voice_volume: float = 0.5
    muted: bool = False
    sound_categories: dict[str, bool] = field(
        default_factory=lambda: {
            "themes": True,
            "events": True,
            "keys": False,  # Per user request
            "combat": True,
            "movement": True,
            "items": True,
        }
    )

    # ---- Display ----
    animation_speed: float = 1.0  # 0.5 (slow) - 2.0 (fast)
    color_theme: str = ColorTheme.MATRIX.value
    vignette_intensity: float = 1.0  # 0.0 (off) - 1.0 (max)
    show_fps: bool = False
    glyph_style: str = GlyphStyle.UNICODE.value

    # ---- Input ----
    key_bindings: dict[str, str] = field(
        default_factory=lambda: {
            "confirm": "Return",
            "cancel": "Escape",
            "pause": "Escape",
            "up": "Up",
            "down": "Down",
            "left": "Left",
            "right": "Right",
            "skill_1": "1",
            "skill_2": "2",
            "skill_3": "3",
            "skill_4": "4",
            "skill_5": "5",
            "skill_6": "6",
            "skill_7": "7",
            "skill_8": "8",
            "skill_9": "9",
        }
    )

    # ---- Language ----
    language: str = Language.BOTH.value
    subtitle_mode: str = SubtitleMode.SUBTITLE.value

    # ---- Gameplay ----
    difficulty: str = Difficulty.NORMAL.value
    damage_taken_multiplier: float = 1.0  # 0.5 (half damage) - 2.0 (double)
    combo_window_ms: int = 3500
    auto_save: bool = True

    # ---- Meta ----
    schema_version: int = 1
    last_modified_ms: int = 0


# ----------------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------------


def validate_settings(settings: GameSettings) -> list[str]:
    """Validate settings, return list of error messages.

    Empty list means valid. Fixes can be applied via `apply_fixes`.
    """
    errors: list[str] = []

    # Volume range
    for name in ("master_volume", "music_volume", "sfx_volume", "voice_volume"):
        val = getattr(settings, name)
        if not 0.0 <= val <= 1.0:
            errors.append(f"{name} must be 0.0-1.0, got {val}")

    # Animation speed
    if not 0.1 <= settings.animation_speed <= 5.0:
        errors.append(f"animation_speed must be 0.1-5.0, got {settings.animation_speed}")

    # Vignette
    if not 0.0 <= settings.vignette_intensity <= 1.0:
        errors.append(f"vignette_intensity must be 0.0-1.0, got {settings.vignette_intensity}")

    # Color theme
    valid_themes = {t.value for t in ColorTheme}
    if settings.color_theme not in valid_themes:
        errors.append(f"color_theme must be one of {valid_themes}")

    # Glyph style
    valid_styles = {g.value for g in GlyphStyle}
    if settings.glyph_style not in valid_styles:
        errors.append(f"glyph_style must be one of {valid_styles}")

    # Language
    valid_langs = {lang.value for lang in Language}
    if settings.language not in valid_langs:
        errors.append(f"language must be one of {valid_langs}")

    # Subtitle
    valid_subs = {s.value for s in SubtitleMode}
    if settings.subtitle_mode not in valid_subs:
        errors.append(f"subtitle_mode must be one of {valid_subs}")

    # Difficulty
    valid_diff = {d.value for d in Difficulty}
    if settings.difficulty not in valid_diff:
        errors.append(f"difficulty must be one of {valid_diff}")

    # Damage modifier
    if not 0.1 <= settings.damage_taken_multiplier <= 5.0:
        errors.append("damage_taken_multiplier must be 0.1-5.0")

    # Combo window
    if not 1000 <= settings.combo_window_ms <= 10000:
        errors.append(f"combo_window_ms must be 1000-10000, got {settings.combo_window_ms}")

    return errors


def apply_fixes(settings: GameSettings) -> GameSettings:
    """Apply default fixes to invalid settings, return the same instance.

    Clamps numeric values, falls back to defaults for invalid enums.
    """
    # Clamp volumes
    for name in ("master_volume", "music_volume", "sfx_volume", "voice_volume"):
        val = getattr(settings, name)
        setattr(settings, name, max(0.0, min(1.0, val)))

    # Clamp animation speed
    settings.animation_speed = max(0.1, min(5.0, settings.animation_speed))

    # Clamp vignette
    settings.vignette_intensity = max(0.0, min(1.0, settings.vignette_intensity))

    # Validate enums
    if settings.color_theme not in {t.value for t in ColorTheme}:
        settings.color_theme = ColorTheme.MATRIX.value
    if settings.glyph_style not in {gs.value for gs in GlyphStyle}:
        settings.glyph_style = GlyphStyle.UNICODE.value
    if settings.language not in {lang.value for lang in Language}:
        settings.language = Language.BOTH.value
    if settings.subtitle_mode not in {sm.value for sm in SubtitleMode}:
        settings.subtitle_mode = SubtitleMode.SUBTITLE.value
    if settings.difficulty not in {df.value for df in Difficulty}:
        settings.difficulty = Difficulty.NORMAL.value

    # Clamp damage modifier
    settings.damage_taken_multiplier = max(0.1, min(5.0, settings.damage_taken_multiplier))

    # Clamp combo window
    settings.combo_window_ms = max(1000, min(10000, settings.combo_window_ms))

    return settings


# ----------------------------------------------------------------------------
# Reset / snapshot
# ----------------------------------------------------------------------------


def get_default_settings() -> GameSettings:
    """Return a fresh settings with all defaults."""
    return GameSettings()


def reset_settings(settings: GameSettings) -> GameSettings:
    """Reset all settings to defaults, return the same instance."""
    defaults = get_default_settings()
    for field_name in defaults.__dataclass_fields__:
        setattr(settings, field_name, getattr(defaults, field_name))
    return settings


def clone_settings(settings: GameSettings) -> GameSettings:
    """Create an independent copy of settings."""
    import copy

    return copy.deepcopy(settings)


# ----------------------------------------------------------------------------
# Persistence (JSON)
# ----------------------------------------------------------------------------


def settings_to_dict(settings: GameSettings) -> dict[str, Any]:
    """Serialize settings to a dict for JSON storage."""
    return {
        "schema_version": settings.schema_version,
        "last_modified_ms": settings.last_modified_ms,
        "audio": {
            "master_volume": settings.master_volume,
            "music_volume": settings.music_volume,
            "sfx_volume": settings.sfx_volume,
            "voice_volume": settings.voice_volume,
            "muted": settings.muted,
            "sound_categories": dict(settings.sound_categories),
        },
        "display": {
            "animation_speed": settings.animation_speed,
            "color_theme": settings.color_theme,
            "vignette_intensity": settings.vignette_intensity,
            "show_fps": settings.show_fps,
            "glyph_style": settings.glyph_style,
        },
        "input": {
            "key_bindings": dict(settings.key_bindings),
        },
        "language": {
            "language": settings.language,
            "subtitle_mode": settings.subtitle_mode,
        },
        "gameplay": {
            "difficulty": settings.difficulty,
            "damage_taken_multiplier": settings.damage_taken_multiplier,
            "combo_window_ms": settings.combo_window_ms,
            "auto_save": settings.auto_save,
        },
    }


def settings_from_dict(data: dict[str, Any]) -> GameSettings:
    """Deserialize settings from a dict (e.g. from JSON).

    Missing fields use defaults. Invalid values are fixed via
    `apply_fixes`.
    """
    settings = get_default_settings()
    audio = data.get("audio", {})
    settings.master_volume = float(audio.get("master_volume", settings.master_volume))
    settings.music_volume = float(audio.get("music_volume", settings.music_volume))
    settings.sfx_volume = float(audio.get("sfx_volume", settings.sfx_volume))
    settings.voice_volume = float(audio.get("voice_volume", settings.voice_volume))
    settings.muted = bool(audio.get("muted", settings.muted))
    cats = audio.get("sound_categories", settings.sound_categories)
    if isinstance(cats, dict):
        for key, val in cats.items():
            settings.sound_categories[key] = bool(val)

    display = data.get("display", {})
    settings.animation_speed = float(display.get("animation_speed", settings.animation_speed))
    settings.color_theme = str(display.get("color_theme", settings.color_theme))
    settings.vignette_intensity = float(
        display.get("vignette_intensity", settings.vignette_intensity)
    )
    settings.show_fps = bool(display.get("show_fps", settings.show_fps))
    settings.glyph_style = str(display.get("glyph_style", settings.glyph_style))

    input_data = data.get("input", {})
    bindings = input_data.get("key_bindings", settings.key_bindings)
    if isinstance(bindings, dict):
        for key, val in bindings.items():
            settings.key_bindings[key] = str(val)

    lang = data.get("language", {})
    settings.language = str(lang.get("language", settings.language))
    settings.subtitle_mode = str(lang.get("subtitle_mode", settings.subtitle_mode))

    gameplay = data.get("gameplay", {})
    settings.difficulty = str(gameplay.get("difficulty", settings.difficulty))
    settings.damage_taken_multiplier = float(
        gameplay.get("damage_taken_multiplier", settings.damage_taken_multiplier)
    )
    settings.combo_window_ms = int(gameplay.get("combo_window_ms", settings.combo_window_ms))
    settings.auto_save = bool(gameplay.get("auto_save", settings.auto_save))

    settings.schema_version = int(data.get("schema_version", 1))
    settings.last_modified_ms = int(data.get("last_modified_ms", 0))

    apply_fixes(settings)
    return settings


def save_settings_to_file(
    settings: GameSettings,
    path: Path,
    current_ms: int = 0,
) -> bool:
    """Save settings to a JSON file. Returns True on success."""
    try:
        settings.last_modified_ms = current_ms
        data = settings_to_dict(settings)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except (OSError, TypeError, ValueError):
        return False


def load_settings_from_file(path: Path) -> GameSettings:
    """Load settings from a JSON file. Returns defaults on error."""
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return get_default_settings()
        return settings_from_dict(data)
    except (OSError, json.JSONDecodeError):
        return get_default_settings()


# ----------------------------------------------------------------------------
# Apply settings to other systems
# ----------------------------------------------------------------------------


def apply_audio_settings(
    settings: GameSettings,
) -> dict[str, object]:
    """Compute audio values to apply to the sound manager.

    Returns a dict with master_volume, music_volume, sfx_volume,
    voice_volume, muted, and category on/off flags.
    """
    effective_volume = 0.0 if settings.muted else settings.master_volume
    return {
        "master_volume": effective_volume,
        "music_volume": effective_volume
        * settings.music_volume
        / max(settings.master_volume, 0.01),
        "sfx_volume": effective_volume * settings.sfx_volume / max(settings.master_volume, 0.01),
        "voice_volume": effective_volume
        * settings.voice_volume
        / max(settings.master_volume, 0.01),
        "muted": settings.muted,
        "categories": dict(settings.sound_categories),
    }


def apply_combo_settings(settings: GameSettings) -> int:
    """Get the combo window in ms (from settings)."""
    return settings.combo_window_ms


def apply_difficulty_settings(settings: GameSettings) -> dict[str, float]:
    """Get difficulty multipliers.

    Returns:
      damage_taken: 0.5 (easy) - 1.0 (normal) - 1.5 (hard) - 2.0 (nightmare)
      damage_dealt: similar
    """
    mults = {
        Difficulty.EASY.value: {"damage_taken": 0.5, "damage_dealt": 1.5},
        Difficulty.NORMAL.value: {"damage_taken": 1.0, "damage_dealt": 1.0},
        Difficulty.HARD.value: {"damage_taken": 1.5, "damage_dealt": 0.8},
        Difficulty.NIGHTMARE.value: {"damage_taken": 2.0, "damage_dealt": 0.6},
    }
    return mults.get(
        settings.difficulty,
        mults[Difficulty.NORMAL.value],
    )


# ----------------------------------------------------------------------------
# Settings summary
# ----------------------------------------------------------------------------


def get_settings_summary(settings: GameSettings) -> dict[str, Any]:
    """Get a summary of current settings for the dashboard."""
    return {
        "audio": {
            "master": f"{int(settings.master_volume * 100)}%",
            "music": f"{int(settings.music_volume * 100)}%",
            "sfx": f"{int(settings.sfx_volume * 100)}%",
            "muted": settings.muted,
            "categories_on": sum(1 for v in settings.sound_categories.values() if v),
            "categories_total": len(settings.sound_categories),
        },
        "display": {
            "theme": settings.color_theme,
            "animation_speed": settings.animation_speed,
            "vignette": f"{int(settings.vignette_intensity * 100)}%",
            "show_fps": settings.show_fps,
            "glyph_style": settings.glyph_style,
        },
        "input": {
            "bindings": dict(settings.key_bindings),
        },
        "language": {
            "language": settings.language,
            "subtitle_mode": settings.subtitle_mode,
        },
        "gameplay": {
            "difficulty": settings.difficulty,
            "damage_taken": f"{settings.damage_taken_multiplier:.1f}x",
            "combo_window": f"{settings.combo_window_ms}ms",
            "auto_save": settings.auto_save,
        },
    }


# ----------------------------------------------------------------------------
# Version info
# ----------------------------------------------------------------------------


GAME_VERSION = "0.5.0"
GAME_NAME = "Roguelike Sprawl"
GAME_AUTHOR = "emilio"


def get_about_info() -> dict[str, str]:
    """Get game about info."""
    counts = {
        "settings_count": "30",
        "achievements_count": "28",
        "ice_types_count": "5",
        "boss_types_count": "3",
        "skill_effects_count": "15",
        "combo_stages_count": "5",
    }
    return {
        "name": GAME_NAME,
        "version": GAME_VERSION,
        "author": GAME_AUTHOR,
        "schema_version": "1",
        **counts,
    }


__all__ = [
    "ColorTheme",
    "Difficulty",
    "GAME_AUTHOR",
    "GAME_NAME",
    "GAME_VERSION",
    "GameSettings",
    "GlyphStyle",
    "Language",
    "SubtitleMode",
    "apply_audio_settings",
    "apply_combo_settings",
    "apply_difficulty_settings",
    "apply_fixes",
    "clone_settings",
    "get_about_info",
    "get_default_settings",
    "get_settings_summary",
    "load_settings_from_file",
    "reset_settings",
    "save_settings_to_file",
    "settings_from_dict",
    "settings_to_dict",
    "validate_settings",
]
