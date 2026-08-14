"""Unit tests for the sound manager."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestSoundManager:
    """Tests for SoundManager class."""

    def test_manager_creates_sounds_dir(self, tmp_path: Path) -> None:
        """SoundManager creates its sounds directory if missing."""
        from roguelike_sprawl.audio.sound_manager import SoundManager

        sounds_dir = tmp_path / "new_sounds"
        SoundManager(sounds_dir=sounds_dir)
        assert sounds_dir.exists()

    def test_manager_auto_generates_wavs(self, tmp_path: Path) -> None:
        """SoundManager auto-generates WAVs for all default sounds."""
        from roguelike_sprawl.audio.sound_manager import DEFAULT_SOUNDS, SoundManager

        sounds_dir = tmp_path / "sounds"
        SoundManager(sounds_dir=sounds_dir)
        # All 27 default sounds should have a WAV file
        for sound_name, (filename, *_args) in DEFAULT_SOUNDS.items():
            path = sounds_dir / filename
            assert path.exists(), f"Missing WAV for {sound_name}: {path}"

    def test_is_available_returns_bool(self) -> None:
        """is_available() returns True on systems with afplay/aplay."""
        from roguelike_sprawl.audio.sound_manager import SoundManager

        sm = SoundManager(sounds_dir=Path("data/sounds_test"))
        result = sm.is_available()
        assert isinstance(result, bool)

    def test_set_volume_clamps(self) -> None:
        """set_volume clamps to 0.0-1.0 range."""
        from roguelike_sprawl.audio.sound_manager import SoundManager

        sm = SoundManager(sounds_dir=Path("data/sounds_test"))
        sm.set_volume(2.0)
        assert sm.volume == 1.0
        sm.set_volume(-1.0)
        assert sm.volume == 0.0
        sm.set_volume(0.5)
        assert sm.volume == 0.5

    def test_mute_toggle(self) -> None:
        """toggle_mute flips muted state and returns new value."""
        from roguelike_sprawl.audio.sound_manager import SoundManager

        sm = SoundManager(sounds_dir=Path("data/sounds_test"))
        assert sm.muted is False
        new_state = sm.toggle_mute()
        assert new_state is True
        assert sm.muted is True
        new_state = sm.toggle_mute()
        assert new_state is False

    def test_play_unknown_sound_returns_false(self) -> None:
        """play() with unknown sound name returns False without raising."""
        from roguelike_sprawl.audio.sound_manager import SoundManager

        sm = SoundManager(sounds_dir=Path("data/sounds_test"))
        result = sm.play("nonexistent/sound_name")
        assert result is False

    def test_play_returns_bool_for_known_sound(self) -> None:
        """play() returns bool for known sounds (True if audio backend works)."""
        from roguelike_sprawl.audio.sound_manager import SoundManager

        sm = SoundManager(sounds_dir=Path("data/sounds_test"))
        # Mute first to avoid actual playback
        sm.set_mute(True)
        result = sm.play("ui/menu_select")
        assert result is False  # Muted returns False
        # Unmute and try
        sm.set_mute(False)
        result = sm.play("ui/menu_select")
        # Should be True on macOS/Linux with afplay/aplay
        assert isinstance(result, bool)

    def test_list_sounds_includes_all_categories(self) -> None:
        """list_sounds() returns all default sound names."""
        from roguelike_sprawl.audio.sound_manager import SoundManager

        sm = SoundManager(sounds_dir=Path("data/sounds_test"))
        sounds = sm.list_sounds()
        assert "ui/menu_select" in sounds
        assert "combat/hit_normal" in sounds
        assert "story/dialogue_advance" in sounds
        assert "movement/nav_step" in sounds
        assert "items/equip" in sounds

    def test_stop_all_does_not_raise(self) -> None:
        """stop_all() is safe to call when nothing is playing."""
        from roguelike_sprawl.audio.sound_manager import SoundManager

        sm = SoundManager(sounds_dir=Path("data/sounds_test"))
        sm.stop_all()  # Should not raise
        sm.stop_all()  # Multiple calls safe


class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_get_sound_manager_returns_singleton(self) -> None:
        """get_sound_manager() returns the same instance on repeated calls."""
        from roguelike_sprawl.audio import sound_manager

        sm1 = sound_manager.get_sound_manager()
        sm2 = sound_manager.get_sound_manager()
        assert sm1 is sm2

    def test_safe_play_swallows_errors(self) -> None:
        """safe_play() returns False for unknown sounds, never raises."""
        from roguelike_sprawl.audio import sound_manager

        result = sound_manager.safe_play("nonexistent/sound")
        assert result is False


class TestSoundCategories:
    """Tests for sound category constants."""

    def test_categories_defined(self) -> None:
        """Sound category constants are exposed via audio module."""
        from roguelike_sprawl.audio import sound_manager

        assert sound_manager.SFX == "sfx"
        assert sound_manager.AMBIENT == "ambient"
        assert sound_manager.VOICE == "voice"
        assert sound_manager.MUSIC == "music"


class TestPhase31WAVGeneration:
    """Phase 31 — _generate_wav raises ValueError for unknown waveform kind."""

    def test_generate_wav_valid_kinds(self, tmp_path: Path) -> None:
        """_generate_wav accepts all three waveform kinds."""
        from roguelike_sprawl.audio.sound_manager import _generate_wav

        for kind in ("sine", "square", "noise"):
            path = tmp_path / f"test_{kind}.wav"
            _generate_wav(path, freq=440, duration_ms=50, kind=kind)
            assert path.exists()
            assert path.stat().st_size > 0

    def test_generate_wav_rejects_unknown_kind(self, tmp_path: Path) -> None:
        """_generate_wav raises ValueError with a clear message for unknown kind."""
        from roguelike_sprawl.audio.sound_manager import _generate_wav

        path = tmp_path / "bad.wav"
        with pytest.raises(ValueError, match="Unknown WAV kind"):
            _generate_wav(path, freq=440, duration_ms=50, kind="sawtooth")
        assert not path.exists()
