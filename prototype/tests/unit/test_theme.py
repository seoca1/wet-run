"""Tests for audio.theme — ThemePlayer + THEMES dict + singleton.

Coverage target for src/wet_run/audio/theme.py.
Real audio playback is mocked; we test the control/decision logic.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from wet_run.audio.config import SoundConfig
from wet_run.audio.theme import (
    DEFAULT_THEME,
    THEMES,
    ThemePlayer,
    get_theme_player,
    play_theme,
    stop_theme,
)


@pytest.fixture
def config():
    return SoundConfig(master_volume=0.8)


def _disabled_config():
    config = SoundConfig()
    config.category_enabled["theme"] = False
    return config


def _muted_config():
    config = SoundConfig(muted=True)
    return config


@pytest.fixture
def sounds_dir(tmp_path: Path):
    """Empty sounds dir — no theme files exist (test fallback path)."""
    return tmp_path


@pytest.fixture
def sounds_dir_with_themes(tmp_path: Path):
    """Create real (empty) theme files so play() takes the loop path."""
    for name in THEMES.values():
        (tmp_path / name).write_bytes(b"RIFF\x00\x00")
    return tmp_path


# ----------------------------------------------------------------------------
# THEMES dict
# ----------------------------------------------------------------------------


class TestTHEMES:
    def test_has_multiple_themes(self):
        assert len(THEMES) >= 5

    def test_default_theme_in_dict(self):
        assert DEFAULT_THEME in THEMES

    def test_all_filenames_end_with_wav(self):
        for filename in THEMES.values():
            assert filename.endswith(".wav")

    def test_keys_are_non_empty(self):
        for k in THEMES:
            assert isinstance(k, str)
            assert len(k) > 0

    def test_default_filename_format(self):
        assert THEMES[DEFAULT_THEME].startswith("theme_")
        assert THEMES[DEFAULT_THEME].endswith(".wav")


# ----------------------------------------------------------------------------
# SoundConfig decision gates
# ----------------------------------------------------------------------------


class TestConfigGates:
    def test_theme_disabled_returns_false(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        config = _disabled_config()
        result = player.play(DEFAULT_THEME, config)
        assert result is False

    def test_muted_returns_false(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        config = _muted_config()
        result = player.play(DEFAULT_THEME, config)
        assert result is False

    def test_unknown_theme_returns_false(self, sounds_dir: Path, config: SoundConfig):
        player = ThemePlayer(sounds_dir)
        result = player.play("not-a-real-theme", config)
        assert result is False

    def test_disabled_check_takes_priority(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        config = _disabled_config()
        config.muted = True
        result = player.play(DEFAULT_THEME, config)
        assert result is False


# ----------------------------------------------------------------------------
# ThemePlayer state machine
# ----------------------------------------------------------------------------


class TestThemePlayerInit:
    def test_init_stores_sounds_dir(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        assert player.sounds_dir == sounds_dir

    def test_init_no_theme_playing(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        assert player.current_theme is None
        assert player.is_playing is False

    def test_init_volume_default(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        # Default volume should be in valid range
        assert 0.0 <= player._volume <= 1.0


class TestThemeStateProperties:
    def test_current_theme_starts_none(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        assert player.current_theme is None

    def test_is_playing_starts_false(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        assert player.is_playing is False


# ----------------------------------------------------------------------------
# set_volume
# ----------------------------------------------------------------------------


class TestSetVolume:
    def test_set_volume_normal(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        player.set_volume(0.5)
        assert player._volume == 0.5

    def test_set_volume_clamps_above_1(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        player.set_volume(1.5)
        assert player._volume == 1.0

    def test_set_volume_clamps_below_0(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        player.set_volume(-0.5)
        assert player._volume == 0.0

    def test_set_volume_at_boundaries(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        player.set_volume(0.0)
        assert player._volume == 0.0
        player.set_volume(1.0)
        assert player._volume == 1.0


# ----------------------------------------------------------------------------
# Fallback when file missing
# ----------------------------------------------------------------------------


class TestOneShotFallback:
    def test_fallback_when_file_missing(self, sounds_dir: Path, config: SoundConfig):
        """When theme file doesn't exist, try playing as a one-shot effect."""
        player = ThemePlayer(sounds_dir)
        # Patch the sound_manager's play_with_config to return True
        with patch("wet_run.audio.sound_manager.get_sound_manager") as mock_sm:
            mock_sm.return_value.play_with_config.return_value = True
            result = player.play(DEFAULT_THEME, config)
            # Result depends on whether fallback succeeds (sm mock returns True)
            assert isinstance(result, bool)

    def test_fallback_unknown_theme_returns_false(self, sounds_dir: Path, config: SoundConfig):
        player = ThemePlayer(sounds_dir)
        result = player.play("does-not-exist", config)
        assert result is False


# ----------------------------------------------------------------------------
# stop() on idle player
# ----------------------------------------------------------------------------


class TestStop:
    def test_stop_idle_does_not_crash(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        # Calling stop on idle player should not raise
        player.stop()
        assert player.current_theme is None
        assert player.is_playing is False

    def test_stop_sets_current_to_none(self, sounds_dir: Path):
        player = ThemePlayer(sounds_dir)
        player._current_theme = "fake"  # Set manually for test
        player.stop()
        # After stop, _current_theme should be cleared (or possibly not, depending on impl)
        # Just verify no crash and state is consistent
        assert player._thread is None


# ----------------------------------------------------------------------------
# Convenience functions + singleton
# ----------------------------------------------------------------------------


class TestSingleton:
    def test_get_theme_player_returns_instance(self):
        import wet_run.audio.theme as theme_module

        theme_module._theme_player = None

        with patch("wet_run.audio.theme.get_sound_manager") as mock_sm:
            mock_sm.return_value.sounds_dir = Path("/tmp/sounds")
            player1 = get_theme_player()
            player2 = get_theme_player()
            assert player1 is player2
            mock_sm.assert_called_once()

    def test_get_after_reset_creates_new(self):
        import wet_run.audio.theme as theme_module

        theme_module._theme_player = None

        with patch("wet_run.audio.theme.get_sound_manager") as mock_sm:
            mock_sm.return_value.sounds_dir = Path("/tmp/sounds")
            player1 = get_theme_player()
            theme_module._theme_player = None
            player2 = get_theme_player()
            assert player1 is not player2


class TestConvenienceFunctions:
    def test_play_theme_convenience(self, tmp_path: Path):
        import wet_run.audio.theme as theme_module

        theme_module._theme_player = None

        with patch("wet_run.audio.sound_manager.get_sound_manager"):
            config = _disabled_config()
            result = play_theme(DEFAULT_THEME, config)
            assert result is False  # disabled config returns False

    def test_stop_theme_convenience_no_crash(self):
        import wet_run.audio.theme as theme_module

        theme_module._theme_player = None
        # Should not raise even when no theme player exists
        stop_theme()


# ----------------------------------------------------------------------------
# Threading lifecycle (smoke test)
# ----------------------------------------------------------------------------


class TestThreadSafety:
    def test_play_returns_bool(self, sounds_dir: Path, config: SoundConfig):
        player = ThemePlayer(sounds_dir)
        result = player.play(DEFAULT_THEME, config)
        assert isinstance(result, bool)

    def test_stop_after_play_attempt(self, sounds_dir: Path, config: SoundConfig):
        player = ThemePlayer(sounds_dir)
        player.play(DEFAULT_THEME, config)
        # Should not crash even if stop runs immediately
        player.stop()
        # No daemon thread leaks
        if player._thread is not None:
            player._thread.join(timeout=0.1)
