"""Unit tests for BGM Manager (Cycle 3 polish).

Covers:
- Screen-to-theme registration (register / register_defaults)
- Theme playback (play_for_screen / play_theme)
- Volume control (set_volume, clamped 0.0-1.0)
- Mute control (mute / unmute / toggle_mute)
- Stop / fade_out (simulated crossfade)
- Singleton pattern (get_bgm_manager / reset_bgm_manager)
- Pillar 4 compliance (ephemeral state, no cross-run inheritance)
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from wet_run.audio.bgm_manager import (
    DEFAULT_BGM_VOLUME,
    BgmManager,
    get_bgm_manager,
    reset_bgm_manager,
)


@pytest.fixture(autouse=True)
def _reset_singleton() -> None:
    """Reset the BGM singleton between tests."""
    reset_bgm_manager()
    yield
    reset_bgm_manager()


class TestScreenRegistration:
    """register / register_defaults / validation."""

    def test_register_known_theme(self) -> None:
        bgm = BgmManager()
        bgm.register("MENU", "finn_office")
        assert "MENU" in bgm.registered_screens
        assert bgm.play_for_screen("MENU") is True

    def test_register_unknown_theme_raises(self) -> None:
        bgm = BgmManager()
        with pytest.raises(ValueError, match="Unknown theme"):
            bgm.register("MENU", "fake_theme_xyz")

    def test_register_defaults_covers_all_screens(self) -> None:
        bgm = BgmManager()
        bgm.register_defaults()
        assert bgm.registered_screens == sorted(
            [
                "MENU",
                "HUB",
                "MATRIX",
                "MATRIX_DEEP",
                "COMBAT",
                "COMBAT_BOSS",
                "NPC",
                "SENSE_NET",
                "LOA",
                "CINEMATIC",
                "SALVATION",
            ]
        )

    def test_register_overwrites(self) -> None:
        bgm = BgmManager()
        bgm.register("HUB", "finn_office")
        bgm.register("HUB", "chiba")
        assert bgm.play_for_screen("HUB") is True
        assert bgm.current_theme == "chiba"


class TestThemePlayback:
    """play_for_screen / play_theme / stop / fade_out."""

    def test_play_for_screen_unknown_returns_false(self) -> None:
        bgm = BgmManager()
        with patch("wet_run.audio.bgm_manager.play_theme") as mock_play:
            assert bgm.play_for_screen("UNKNOWN_SCREEN") is False
            mock_play.assert_not_called()

    def test_play_theme_success(self) -> None:
        bgm = BgmManager()
        with patch("wet_run.audio.bgm_manager.play_theme", return_value=True) as mock_play:
            assert bgm.play_theme("matrix_rain") is True
            assert bgm.current_theme == "matrix_rain"
            mock_play.assert_called_once()

    def test_play_theme_unknown_returns_false(self) -> None:
        bgm = BgmManager()
        with patch("wet_run.audio.bgm_manager.play_theme") as mock_play:
            assert bgm.play_theme("nonexistent") is False
            mock_play.assert_not_called()

    def test_play_theme_while_muted_records_but_skips_audio(self) -> None:
        bgm = BgmManager()
        bgm.mute()
        with patch("wet_run.audio.bgm_manager.play_theme") as mock_play:
            assert bgm.play_theme("matrix_rain") is True
            assert bgm.current_theme == "matrix_rain"
            mock_play.assert_not_called()

    def test_stop_calls_audio_stop(self) -> None:
        bgm = BgmManager()
        with patch("wet_run.audio.bgm_manager.stop_theme") as mock_stop:
            bgm.stop()
            assert bgm.current_theme is None
            mock_stop.assert_called_once()

    def test_fade_out_calls_stop(self) -> None:
        bgm = BgmManager()
        with patch("wet_run.audio.bgm_manager.stop_theme") as mock_stop:
            bgm.fade_out(duration_ms=500)
            assert bgm.current_theme is None
            mock_stop.assert_called_once()


class TestVolumeControl:
    """set_volume clamped 0.0-1.0."""

    def test_default_volume(self) -> None:
        bgm = BgmManager()
        assert bgm.volume == DEFAULT_BGM_VOLUME

    def test_set_volume_within_range(self) -> None:
        bgm = BgmManager()
        bgm.set_volume(0.7)
        assert bgm.volume == 0.7

    def test_set_volume_clamps_to_zero(self) -> None:
        bgm = BgmManager()
        bgm.set_volume(-0.5)
        assert bgm.volume == 0.0

    def test_set_volume_clamps_to_one(self) -> None:
        bgm = BgmManager()
        bgm.set_volume(1.5)
        assert bgm.volume == 1.0

    def test_set_volume_with_current_theme_restarts(self) -> None:
        bgm = BgmManager()
        with patch("wet_run.audio.bgm_manager.play_theme", return_value=True) as mock_play:
            bgm.play_theme("matrix_rain")
            mock_play.reset_mock()
            bgm.set_volume(0.5)
            mock_play.assert_called_once()


class TestMuteControl:
    """mute / unmute / toggle_mute."""

    def test_default_not_muted(self) -> None:
        bgm = BgmManager()
        assert bgm.is_muted is False

    def test_mute_stops_playback(self) -> None:
        bgm = BgmManager()
        with patch("wet_run.audio.bgm_manager.play_theme", return_value=True):
            bgm.play_theme("matrix_rain")
        with patch("wet_run.audio.bgm_manager.stop_theme") as mock_stop:
            bgm.mute()
            assert bgm.is_muted is True
            mock_stop.assert_called_once()

    def test_mute_idempotent(self) -> None:
        bgm = BgmManager()
        with patch("wet_run.audio.bgm_manager.stop_theme") as mock_stop:
            bgm.mute()
            mock_stop.reset_mock()
            bgm.mute()
            mock_stop.assert_not_called()

    def test_unmute_does_not_auto_resume(self) -> None:
        bgm = BgmManager()
        with patch("wet_run.audio.bgm_manager.play_theme", return_value=True):
            bgm.play_theme("matrix_rain")
        with patch("wet_run.audio.bgm_manager.play_theme") as mock_play:
            bgm.unmute()
            assert bgm.is_muted is False
            mock_play.assert_not_called()

    def test_toggle_mute(self) -> None:
        bgm = BgmManager()
        assert bgm.toggle_mute() is True
        assert bgm.is_muted is True
        assert bgm.toggle_mute() is False
        assert bgm.is_muted is False


class TestSingleton:
    """get_bgm_manager / reset_bgm_manager."""

    def test_singleton_returns_same_instance(self) -> None:
        a = get_bgm_manager()
        b = get_bgm_manager()
        assert a is b

    def test_reset_creates_new_instance(self) -> None:
        a = get_bgm_manager()
        reset_bgm_manager()
        b = get_bgm_manager()
        assert a is not b


class TestPillar4Compliance:
    """Pillar 4: ephemeral session preference, no meta-progression."""

    def test_no_meta_state_field(self) -> None:
        """BgmManager does not touch run.meta_state (ADR-0131)."""
        bgm = BgmManager()
        with patch("wet_run.audio.bgm_manager.play_theme", return_value=True):
            bgm.play_theme("matrix_rain")
        assert not hasattr(bgm, "meta_state")

    def test_volume_does_not_persist_across_resets(self) -> None:
        """Reset creates fresh BgmManager with default volume (ephemeral)."""
        a = get_bgm_manager()
        a.set_volume(0.9)
        assert a.volume == 0.9
        reset_bgm_manager()
        b = get_bgm_manager()
        assert b.volume == DEFAULT_BGM_VOLUME


__all__ = [
    "TestScreenRegistration",
    "TestThemePlayback",
    "TestVolumeControl",
    "TestMuteControl",
    "TestSingleton",
    "TestPillar4Compliance",
]
