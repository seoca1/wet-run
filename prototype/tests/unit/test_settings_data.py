"""Tests for wet_run.settings (data module) — GameSettings dataclass + helpers.

Coverage target for src/wet_run/settings.py.
Note: tests/unit/test_settings.py is for engine.settings_view UI module — different module.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wet_run.settings import (
    GAME_AUTHOR,
    GAME_NAME,
    GAME_VERSION,
    ColorTheme,
    Difficulty,
    GameSettings,
    GlyphStyle,
    Language,
    SubtitleMode,
    apply_audio_settings,
    apply_combo_settings,
    apply_difficulty_settings,
    apply_fixes,
    clone_settings,
    get_about_info,
    get_default_settings,
    get_settings_summary,
    load_settings_from_file,
    reset_settings,
    save_settings_to_file,
    settings_from_dict,
    settings_to_dict,
    validate_settings,
)

# ----------------------------------------------------------------------------
# Enums
# ----------------------------------------------------------------------------


class TestEnums:
    def test_color_theme_values(self):
        assert ColorTheme.MATRIX.value == "matrix"
        assert ColorTheme.CYBERPUNK.value == "cyberpunk"
        assert ColorTheme.MONO.value == "mono"

    def test_glyph_style_values(self):
        assert GlyphStyle.ASCII.value == "ascii"
        assert GlyphStyle.UNICODE.value == "unicode"

    def test_language_values(self):
        assert Language.KOREAN.value == "ko"
        assert Language.ENGLISH.value == "en"
        assert Language.JAPANESE.value == "ja"
        assert Language.CHINESE.value == "zh"
        assert Language.BOTH.value == "both"

    def test_subtitle_mode_values(self):
        assert SubtitleMode.OFF.value == "off"
        assert SubtitleMode.SUBTITLE.value == "subtitle"
        assert SubtitleMode.REPLACE.value == "replace"

    def test_difficulty_values(self):
        assert Difficulty.EASY.value == "easy"
        assert Difficulty.NORMAL.value == "normal"
        assert Difficulty.HARD.value == "hard"
        assert Difficulty.NIGHTMARE.value == "nightmare"


# ----------------------------------------------------------------------------
# Defaults
# ----------------------------------------------------------------------------


class TestDefaults:
    def test_audio_defaults(self):
        s = GameSettings()
        assert s.master_volume == 0.2
        assert s.music_volume == 0.2
        assert s.sfx_volume == 0.5
        assert s.voice_volume == 0.5
        assert s.muted is False

    def test_sound_categories_defaults(self):
        s = GameSettings()
        # keys=False per user request
        assert s.sound_categories["keys"] is False
        assert s.sound_categories["themes"] is True
        assert s.sound_categories["combat"] is True

    def test_display_defaults(self):
        s = GameSettings()
        assert s.animation_speed == 1.0
        assert s.color_theme == ColorTheme.MATRIX.value
        assert s.vignette_intensity == 1.0
        assert s.show_fps is False
        assert s.glyph_style == GlyphStyle.UNICODE.value

    def test_input_defaults(self):
        s = GameSettings()
        assert s.key_bindings["confirm"] == "Return"
        assert s.key_bindings["cancel"] == "Escape"
        assert s.key_bindings["up"] == "Up"
        assert s.key_bindings["skill_1"] == "1"
        # All skill_1-9 default to digit keys
        for i in range(1, 10):
            assert s.key_bindings[f"skill_{i}"] == str(i)

    def test_language_defaults(self):
        s = GameSettings()
        assert s.language == Language.BOTH.value
        assert s.subtitle_mode == SubtitleMode.SUBTITLE.value

    def test_gameplay_defaults(self):
        s = GameSettings()
        assert s.difficulty == Difficulty.NORMAL.value
        assert s.damage_taken_multiplier == 1.0
        assert s.combo_window_ms == 3500
        assert s.auto_save is True

    def test_meta_defaults(self):
        s = GameSettings()
        assert s.schema_version == 1
        assert s.last_modified_ms == 0


# ----------------------------------------------------------------------------
# validate_settings
# ----------------------------------------------------------------------------


class TestValidateSettings:
    def test_valid_defaults(self):
        assert validate_settings(GameSettings()) == []

    def test_master_volume_out_of_range(self):
        s = GameSettings(master_volume=1.5)
        errors = validate_settings(s)
        assert any("master_volume" in e for e in errors)

    def test_music_volume_negative(self):
        s = GameSettings(music_volume=-0.1)
        errors = validate_settings(s)
        assert any("music_volume" in e for e in errors)

    def test_all_volumes(self):
        for attr in ("master_volume", "music_volume", "sfx_volume", "voice_volume"):
            s = GameSettings(**{attr: 2.0})
            assert any(attr in e for e in validate_settings(s))

    def test_animation_speed_out_of_range(self):
        s = GameSettings(animation_speed=10.0)
        assert any("animation_speed" in e for e in validate_settings(s))

    def test_vignette_out_of_range(self):
        s = GameSettings(vignette_intensity=1.5)
        assert any("vignette_intensity" in e for e in validate_settings(s))

    def test_invalid_color_theme(self):
        s = GameSettings(color_theme="invalid")
        assert any("color_theme" in e for e in validate_settings(s))

    def test_invalid_glyph_style(self):
        s = GameSettings(glyph_style="invalid")
        assert any("glyph_style" in e for e in validate_settings(s))

    def test_invalid_language(self):
        s = GameSettings(language="klingon")
        assert any("language" in e for e in validate_settings(s))

    def test_invalid_subtitle_mode(self):
        s = GameSettings(subtitle_mode="double-subtitle")
        assert any("subtitle_mode" in e for e in validate_settings(s))

    def test_invalid_difficulty(self):
        s = GameSettings(difficulty="super-hard")
        assert any("difficulty" in e for e in validate_settings(s))

    def test_damage_modifier_out_of_range(self):
        s = GameSettings(damage_taken_multiplier=10.0)
        assert any("damage_taken_multiplier" in e for e in validate_settings(s))

    def test_combo_window_too_high(self):
        s = GameSettings(combo_window_ms=60000)
        assert any("combo_window_ms" in e for e in validate_settings(s))

    def test_combo_window_too_low(self):
        s = GameSettings(combo_window_ms=500)
        assert any("combo_window_ms" in e for e in validate_settings(s))

    def test_multiple_errors(self):
        s = GameSettings(master_volume=2.0, animation_speed=10.0, color_theme="bad")
        errors = validate_settings(s)
        assert len(errors) >= 3


# ----------------------------------------------------------------------------
# apply_fixes
# ----------------------------------------------------------------------------


class TestApplyFixes:
    def test_returns_same_instance(self):
        s = GameSettings()
        assert apply_fixes(s) is s

    def test_clamps_volumes_high(self):
        s = GameSettings(master_volume=2.0, music_volume=3.0)
        apply_fixes(s)
        assert s.master_volume == 1.0
        assert s.music_volume == 1.0

    def test_clamps_volumes_low(self):
        s = GameSettings(master_volume=-0.5)
        apply_fixes(s)
        assert s.master_volume == 0.0

    def test_clamps_animation_speed(self):
        s = GameSettings(animation_speed=10.0)
        apply_fixes(s)
        assert s.animation_speed == 5.0

    def test_clamps_animation_speed_low(self):
        s = GameSettings(animation_speed=0.05)
        apply_fixes(s)
        assert s.animation_speed == 0.1

    def test_clamps_vignette(self):
        s = GameSettings(vignette_intensity=1.5)
        apply_fixes(s)
        assert s.vignette_intensity == 1.0

    def test_resets_invalid_color_theme(self):
        s = GameSettings(color_theme="invalid")
        apply_fixes(s)
        assert s.color_theme == ColorTheme.MATRIX.value

    def test_resets_invalid_glyph_style(self):
        s = GameSettings(glyph_style="invalid")
        apply_fixes(s)
        assert s.glyph_style == GlyphStyle.UNICODE.value

    def test_resets_invalid_language(self):
        s = GameSettings(language="klingon")
        apply_fixes(s)
        assert s.language == Language.BOTH.value

    def test_resets_invalid_subtitle_mode(self):
        s = GameSettings(subtitle_mode="invalid")
        apply_fixes(s)
        assert s.subtitle_mode == SubtitleMode.SUBTITLE.value

    def test_resets_invalid_difficulty(self):
        s = GameSettings(difficulty="super-hard")
        apply_fixes(s)
        assert s.difficulty == Difficulty.NORMAL.value

    def test_clamps_damage_modifier(self):
        s = GameSettings(damage_taken_multiplier=10.0)
        apply_fixes(s)
        assert s.damage_taken_multiplier == 5.0

    def test_clamps_combo_window_low(self):
        s = GameSettings(combo_window_ms=500)
        apply_fixes(s)
        assert s.combo_window_ms == 1000

    def test_clamps_combo_window_high(self):
        s = GameSettings(combo_window_ms=20000)
        apply_fixes(s)
        assert s.combo_window_ms == 10000

    def test_no_change_for_valid(self):
        s = GameSettings()
        snapshot = settings_to_dict(s)
        apply_fixes(s)
        assert settings_to_dict(s) == snapshot


# ----------------------------------------------------------------------------
# get_default_settings / reset_settings / clone_settings
# ----------------------------------------------------------------------------


class TestGetDefaultSettings:
    def test_fresh_instance(self):
        s = get_default_settings()
        assert isinstance(s, GameSettings)
        assert s.combo_window_ms == 3500

    def test_each_call_new(self):
        a = get_default_settings()
        b = get_default_settings()
        assert a is not b


class TestResetSettings:
    def test_resets_modified(self):
        s = GameSettings(master_volume=0.99, color_theme="cyberpunk")
        reset_settings(s)
        assert s.master_volume == 0.2
        assert s.color_theme == "matrix"

    def test_returns_same_instance(self):
        s = GameSettings()
        assert reset_settings(s) is s


class TestCloneSettings:
    def test_independent_copy(self):
        original = GameSettings(master_volume=0.5)
        copy_obj = clone_settings(original)
        assert copy_obj is not original
        assert copy_obj.master_volume == 0.5
        copy_obj.master_volume = 0.1
        assert original.master_volume == 0.5

    def test_deep_copies_dicts(self):
        original = GameSettings()
        original.sound_categories["keys"] = True
        copy_obj = clone_settings(original)
        copy_obj.sound_categories["keys"] = False
        assert original.sound_categories["keys"] is True

    def test_deep_copies_key_bindings(self):
        original = GameSettings()
        copy_obj = clone_settings(original)
        copy_obj.key_bindings["confirm"] = "Space"
        assert original.key_bindings["confirm"] == "Return"


# ----------------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------------


class TestSettingsSerialization:
    def test_to_dict_has_sections(self):
        d = settings_to_dict(GameSettings())
        for key in ("schema_version", "audio", "display", "input", "language", "gameplay"):
            assert key in d

    def test_roundtrip(self):
        s = GameSettings(master_volume=0.7, difficulty="hard", language="en")
        s2 = settings_from_dict(settings_to_dict(s))
        assert s2.master_volume == 0.7
        assert s2.difficulty == "hard"
        assert s2.language == "en"

    def test_roundtrip_sound_categories(self):
        s = GameSettings()
        s.sound_categories["themes"] = False
        s2 = settings_from_dict(settings_to_dict(s))
        assert s2.sound_categories["themes"] is False

    def test_from_dict_missing_audio(self):
        s = settings_from_dict({"display": {"animation_speed": 2.0}})
        assert s.animation_speed == 2.0
        assert s.master_volume == 0.2  # default

    def test_from_dict_empty(self):
        s = settings_from_dict({})
        assert s.combo_window_ms == 3500

    def test_from_dict_invalid_clamped(self):
        s = settings_from_dict({"audio": {"master_volume": 10.0}})
        assert s.master_volume == 1.0

    def test_from_dict_skips_non_dict_sound_categories(self):
        # Non-dict value passed for sound_categories is silently ignored
        s = settings_from_dict({"audio": {"sound_categories": "bad"}})
        assert s.sound_categories["themes"] is True


class TestFileIO:
    def test_roundtrip_via_file(self, tmp_path: Path):
        path = tmp_path / "settings.json"
        s = GameSettings(master_volume=0.42, color_theme="cyberpunk")
        assert save_settings_to_file(s, path, current_ms=1000) is True
        assert path.exists()
        assert s.last_modified_ms == 1000

        loaded = load_settings_from_file(path)
        assert loaded.master_volume == 0.42
        assert loaded.color_theme == "cyberpunk"

    def test_load_missing_returns_defaults(self, tmp_path: Path):
        loaded = load_settings_from_file(tmp_path / "missing.json")
        assert loaded.combo_window_ms == 3500

    def test_load_corrupt_json_returns_defaults(self, tmp_path: Path):
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        loaded = load_settings_from_file(path)
        assert loaded.combo_window_ms == 3500

    def test_load_non_dict_returns_defaults(self, tmp_path: Path):
        path = tmp_path / "list.json"
        path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        loaded = load_settings_from_file(path)
        assert loaded.combo_window_ms == 3500

    def test_save_creates_parent_dir(self, tmp_path: Path):
        path = tmp_path / "nested" / "deeper" / "settings.json"
        assert save_settings_to_file(GameSettings(), path) is True
        assert path.exists()

    def test_load_invalid_values_clamped(self, tmp_path: Path):
        path = tmp_path / "bad_values.json"
        path.write_text(
            json.dumps({"audio": {"master_volume": 5.0}, "display": {"color_theme": "junk"}}),
            encoding="utf-8",
        )
        loaded = load_settings_from_file(path)
        assert loaded.master_volume == 1.0
        assert loaded.color_theme == "matrix"


# ----------------------------------------------------------------------------
# apply_*_settings helpers
# ----------------------------------------------------------------------------


class TestApplyAudioSettings:
    def test_no_mute(self):
        s = GameSettings(master_volume=0.5, music_volume=0.4)
        result = apply_audio_settings(s)
        assert result["master_volume"] == 0.5
        assert result["music_volume"] == pytest.approx(0.4)
        assert result["muted"] is False

    def test_muted_zeros_volume(self):
        s = GameSettings(muted=True, master_volume=0.5)
        result = apply_audio_settings(s)
        assert result["master_volume"] == 0.0
        assert result["muted"] is True

    def test_master_zero_no_crash(self):
        s = GameSettings(master_volume=0.0, music_volume=0.5)
        # max(0, 0.01) prevents division by zero
        result = apply_audio_settings(s)
        assert result["master_volume"] == 0.0
        assert result["music_volume"] == 0.0

    def test_categories_in_result(self):
        s = GameSettings()
        result = apply_audio_settings(s)
        assert "categories" in result
        assert result["categories"]["themes"] is True
        assert result["categories"]["keys"] is False


class TestApplyComboSettings:
    def test_returns_value(self):
        s = GameSettings(combo_window_ms=5000)
        assert apply_combo_settings(s) == 5000


class TestApplyDifficultySettings:
    def test_easy(self):
        s = GameSettings(difficulty="easy")
        m = apply_difficulty_settings(s)
        assert m["damage_taken"] == 0.5
        assert m["damage_dealt"] == 1.5

    def test_normal(self):
        s = GameSettings(difficulty="normal")
        m = apply_difficulty_settings(s)
        assert m["damage_taken"] == 1.0
        assert m["damage_dealt"] == 1.0

    def test_hard(self):
        s = GameSettings(difficulty="hard")
        m = apply_difficulty_settings(s)
        assert m["damage_taken"] == 1.5
        assert m["damage_dealt"] == 0.8

    def test_nightmare(self):
        s = GameSettings(difficulty="nightmare")
        m = apply_difficulty_settings(s)
        assert m["damage_taken"] == 2.0
        assert m["damage_dealt"] == 0.6

    def test_unknown_falls_back_to_normal(self):
        s = GameSettings(difficulty="invalid")
        m = apply_difficulty_settings(s)
        assert m["damage_taken"] == 1.0


# ----------------------------------------------------------------------------
# get_settings_summary
# ----------------------------------------------------------------------------


class TestGetSettingsSummary:
    def test_has_all_sections(self):
        summary = get_settings_summary(GameSettings())
        for key in ("audio", "display", "input", "language", "gameplay"):
            assert key in summary

    def test_audio_percentages(self):
        s = GameSettings(master_volume=0.5, music_volume=0.4)
        summary = get_settings_summary(s)
        assert summary["audio"]["master"] == "50%"
        assert summary["audio"]["music"] == "40%"

    def test_categories_count(self):
        # Default: 5 of 6 categories on (keys off)
        summary = get_settings_summary(GameSettings())
        assert summary["audio"]["categories_on"] == 5
        assert summary["audio"]["categories_total"] == 6

    def test_vignette_percentage(self):
        s = GameSettings(vignette_intensity=0.5)
        summary = get_settings_summary(s)
        assert summary["display"]["vignette"] == "50%"

    def test_damage_format(self):
        s = GameSettings(damage_taken_multiplier=1.5)
        summary = get_settings_summary(s)
        assert summary["gameplay"]["damage_taken"] == "1.5x"

    def test_combo_window_format(self):
        s = GameSettings(combo_window_ms=2500)
        summary = get_settings_summary(s)
        assert summary["gameplay"]["combo_window"] == "2500ms"


# ----------------------------------------------------------------------------
# Version / get_about_info
# ----------------------------------------------------------------------------


class TestVersionInfo:
    def test_constants(self):
        assert GAME_NAME == "Roguelike Sprawl"
        assert GAME_AUTHOR == "emilio"
        assert isinstance(GAME_VERSION, str)
        assert len(GAME_VERSION) > 0

    def test_get_about_info_keys(self):
        info = get_about_info()
        assert info["name"] == GAME_NAME
        assert info["version"] == GAME_VERSION
        assert info["author"] == GAME_AUTHOR
        assert info["schema_version"] == "1"
        assert "settings_count" in info
        assert "achievements_count" in info
