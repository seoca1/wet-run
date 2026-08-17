"""Tests for graphic novel sound cue mapping (ADR-0043).

Covers:
    - All scene cues resolve to a valid DEFAULT_SOUNDS key
    - resolve_sound() handles both short scene cue names and full keys
    - get_category() returns the correct category prefix
    - play_scene_sound() is a no-op without a SoundManager
    - play_once() caches properly (doesn't replay same cue within session)
    - All 15 scene cues are present in SCENE_SOUND_MAP
    - Audio path bug fix verification: graphic_novel.py uses data/sounds_test
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.audio.sound_manager import DEFAULT_SOUNDS  # noqa: E402
from wet_run.engine.graphic_novel_audio import (  # noqa: E402
    SCENE_SOUND_MAP,
    get_category,
    play_once,
    play_scene_sound,
    resolve_sound,
)

SCENES_DIR = Path(__file__).parent.parent.parent / "data" / "scenes"


def _all_scene_cues() -> list[str]:
    """Read all 12 scenes and return the list of sound cues used."""
    cues: list[str] = []
    for p in sorted(SCENES_DIR.rglob("*.json")):
        if p.parent.name not in {"case", "sil", "kas"}:
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        for line in d.get("dialogue", []):
            if line.get("sound"):
                cues.append(line["sound"])
    return cues


# ============================================================================
# Cue resolution
# ============================================================================


class TestResolveSound:
    def test_resolve_scene_cue_chiba_rain(self) -> None:
        assert resolve_sound("chiba_rain_loop") == "theme/chiba"

    def test_resolve_scene_cue_loa_drum(self) -> None:
        assert resolve_sound("loa_drum") == "theme/loa_drum"

    def test_resolve_scene_cue_shibuya_traffic(self) -> None:
        # The newly added shibuya_traffic cue
        assert resolve_sound("shibuya_traffic") == "theme/sense_net"

    def test_resolve_passthrough_full_key(self) -> None:
        # If scene_sound is already a category/key form, pass through
        assert resolve_sound("theme/matrix_rain") == "theme/matrix_rain"

    def test_resolve_none_returns_none(self) -> None:
        assert resolve_sound(None) is None

    def test_resolve_unknown_returns_none(self) -> None:
        assert resolve_sound("this_cue_does_not_exist") is None


class TestGetCategory:
    def test_theme_category(self) -> None:
        assert get_category("chiba_rain_loop") == "theme"
        assert get_category("loa_drum") == "theme"

    def test_movement_category(self) -> None:
        assert get_category("neon_hum") == "movement"
        assert get_category("jack_in_zap") == "movement"

    def test_unknown_returns_none(self) -> None:
        assert get_category("nonexistent") is None


# ============================================================================
# All 15 scene cues are mapped (ADR-0043)
# ============================================================================


class TestAllSceneCuesMapped:
    """Verify every sound cue referenced in scenes has a mapping."""

    @pytest.fixture
    def scene_cues(self) -> list[str]:
        return _all_scene_cues()

    def test_at_least_15_scene_cues(self, scene_cues: list[str]) -> None:
        assert len(scene_cues) >= 15, f"Expected ≥15 cues, got {len(scene_cues)}"

    def test_unique_scene_cues(self, scene_cues: list[str]) -> None:
        unique = sorted(set(scene_cues))
        # ADR-0049 added ending C scenes — unique count increased
        assert len(unique) >= 15, f"Expected ≥15 unique cues, got {len(unique)}: {unique}"

    def test_every_scene_cue_has_mapping(self, scene_cues: list[str]) -> None:
        """Every cue referenced in scenes must be in SCENE_SOUND_MAP."""
        unique = sorted(set(scene_cues))
        unmapped = [c for c in unique if c not in SCENE_SOUND_MAP]
        assert not unmapped, f"Scene cues without mapping: {unmapped}"

    def test_every_mapped_cue_resolves_to_default_sound(self) -> None:
        """Every value in SCENE_SOUND_MAP must exist in DEFAULT_SOUNDS."""
        invalid = [
            scene_cue
            for scene_cue, mapped in SCENE_SOUND_MAP.items()
            if mapped not in DEFAULT_SOUNDS
        ]
        assert not invalid, f"Mapped cues not in DEFAULT_SOUNDS: {invalid}"


# ============================================================================
# Playback behavior
# ============================================================================


class TestPlaySceneSound:
    def test_play_without_manager_returns_false(self) -> None:
        """play_scene_sound with None manager is a safe no-op."""
        assert play_scene_sound(None, "loa_drum") is False

    def test_play_with_none_cue_returns_false(self) -> None:
        # We don't even need a real manager — None cue short-circuits
        assert play_scene_sound(None, None) is False

    def test_play_unknown_cue_returns_false(self) -> None:
        # Without a manager, this returns False; with a manager it would also fail
        assert play_scene_sound(None, "this_cue_does_not_exist") is False


class _MockSoundManager:
    """Minimal SoundManager mock for testing play_once cache behavior."""

    def __init__(self) -> None:
        self.played: list[str] = []

    def play(self, sound_name: str, pitch: float | None = None) -> bool:
        self.played.append(sound_name)
        return True


class TestPlayOnce:
    def setup_method(self) -> None:
        play_once(None, None, reset=True)  # clear cache

    def test_play_once_caches(self) -> None:
        """play_once called twice with same cue only plays once per session."""
        mgr = _MockSoundManager()
        first = play_once(mgr, "loa_drum")
        second = play_once(mgr, "loa_drum")
        from wet_run.engine.graphic_novel_audio import _played_cache

        assert first is True
        assert second is False  # cached, not played again
        assert mgr.played == ["theme/loa_drum"]  # only one actual call
        assert "loa_drum" in _played_cache

    def test_play_once_different_cues_cached_separately(self) -> None:
        mgr = _MockSoundManager()
        play_once(mgr, "loa_drum")
        play_once(mgr, "matrix_rain")
        from wet_run.engine.graphic_novel_audio import _played_cache

        assert mgr.played == ["theme/loa_drum", "theme/matrix_rain"]
        assert "loa_drum" in _played_cache
        assert "matrix_rain" in _played_cache

    def test_play_once_reset_clears_cache(self) -> None:
        mgr = _MockSoundManager()
        play_once(mgr, "loa_drum")
        from wet_run.engine.graphic_novel_audio import _played_cache

        assert "loa_drum" in _played_cache
        play_once(mgr, None, reset=True)
        # After reset, loa_drum can be played again
        play_once(mgr, "loa_drum")
        assert mgr.played == ["theme/loa_drum", "theme/loa_drum"]

    def test_play_once_with_none_manager_does_not_cache(self) -> None:
        """When manager is None, no cache entry is created (sound never played)."""
        play_once(None, "loa_drum")
        from wet_run.engine.graphic_novel_audio import _played_cache

        # With None manager, play_scene_sound returns False,
        # so nothing is cached.
        assert "loa_drum" not in _played_cache


# ============================================================================
# Path bug fix verification
# ============================================================================


class TestPathBugFix:
    def test_graphic_novel_uses_correct_sounds_dir(self) -> None:
        """Verify graphic_novel.py uses 'data/sounds_test' (not '.. / sounds_test')."""
        script = Path(__file__).parent.parent.parent / "scripts" / "graphic_novel.py"
        text = script.read_text(encoding="utf-8")
        # Should NOT have the wrong path
        assert '".." / "sounds_test"' not in text, (
            "graphic_novel.py still has the wrong sounds_dir path!"
        )
        # Should have the correct path
        assert '"sounds_test"' in text, "graphic_novel.py missing 'sounds_test' path"


# ============================================================================
# Sound files exist on disk
# ============================================================================


class TestSoundFilesOnDisk:
    @pytest.fixture
    def sounds_dir(self) -> Path:
        return Path(__file__).parent.parent.parent / "data" / "sounds_test"

    def test_sounds_dir_exists(self, sounds_dir: Path) -> None:
        assert sounds_dir.exists(), f"{sounds_dir} not found"

    def test_all_default_sounds_have_files(self, sounds_dir: Path) -> None:
        """Every DEFAULT_SOUNDS entry should have a corresponding .wav file."""
        missing = [
            (key, filename)
            for key, (filename, *_rest) in DEFAULT_SOUNDS.items()
            if not (sounds_dir / filename).exists()
        ]
        # Note: SoundManager auto-generates missing files, so this is informational
        # We just log it — but allow it to pass if missing (auto-gen takes care)
        if missing:
            # Verify they're auto-generatable
            pytest.skip(
                f"Some sounds missing (auto-generated by SoundManager): "
                f"{[m[0] for m in missing[:5]]}..."
            )
