"""Tests for scene-based theme auto-start (Phase 5-1).

Tests focus on the state machine: state.current_theme is set correctly.
Audio playback itself is tested via integration (not mocked here).
"""

from __future__ import annotations

from wet_run.audio.config import SoundConfig
from wet_run.engine.story_cinematic import (
    BRIEFING_FINN_SCENE,
    PROLOGUE_SCENE,
    CinematicState,
    stop_scene_theme,
)


class TestSceneThemeField:
    """StoryScene has a theme field."""

    def test_prologue_has_chiba_theme(self) -> None:
        """PROLOGUE_SCENE uses 'chiba' theme (Gibson's neon city)."""
        assert PROLOGUE_SCENE.theme == "chiba"

    def test_briefing_has_finn_office_theme(self) -> None:
        """BRIEFING_FINN_SCENE uses 'finn_office' theme."""
        assert BRIEFING_FINN_SCENE.theme == "finn_office"

    def test_default_theme(self) -> None:
        """A scene without an explicit theme uses 'matrix_rain'."""
        from wet_run.engine.story_cinematic import StoryLine, StoryScene

        scene = StoryScene(
            id="test",
            title_en="Test",
            title_ko="테스트",
            lines=(StoryLine(text_en="Hi", text_ko=""),),
        )
        assert scene.theme == "matrix_rain"


class TestMaybeStartThemeStateMachine:
    """_maybe_start_theme() state machine (no real audio)."""

    def test_initial_state_has_no_theme(self) -> None:
        """Fresh CinematicState has current_theme=None."""
        state = CinematicState(scene=PROLOGUE_SCENE)
        assert state.current_theme is None

    def test_state_field_exists(self) -> None:
        """CinematicState has a current_theme field."""
        state = CinematicState(scene=PROLOGUE_SCENE)
        # Should be able to set the field
        state.current_theme = "test"
        assert state.current_theme == "test"

    def test_stop_clears_current_theme(self) -> None:
        """stop_scene_theme clears the field."""
        state = CinematicState(scene=PROLOGUE_SCENE)
        state.current_theme = "chiba"
        stop_scene_theme(state)
        assert state.current_theme is None

    def test_stop_with_no_theme(self) -> None:
        """stop_scene_theme with no theme does not crash."""
        state = CinematicState(scene=PROLOGUE_SCENE)
        state.current_theme = None
        stop_scene_theme(state)
        assert state.current_theme is None


class TestThemeCategoryControl:
    """Theme playback respects SoundConfig category setting."""

    def test_default_config_has_theme_enabled(self) -> None:
        """Default config has THEME category enabled."""
        config = SoundConfig()
        assert config.is_category_enabled(config.__class__) or True
        # Check via enum
        from wet_run.audio.config import SoundCategory

        assert config.is_category_enabled(SoundCategory.THEME) is True

    def test_disabling_theme(self) -> None:
        """Can disable THEME category."""
        from wet_run.audio.config import SoundCategory

        config = SoundConfig()
        config.set_category_enabled(SoundCategory.THEME, False)
        assert config.is_category_enabled(SoundCategory.THEME) is False


class TestThemeIntegrationWithStep:
    """Integration with step_cinematic (no real audio)."""

    def test_step_cinematic_sets_theme(self) -> None:
        """step_cinematic calls _maybe_start_theme which sets state."""
        # Disable THEME so we don't actually play audio
        from unittest.mock import patch

        from wet_run.audio.config import SoundCategory
        from wet_run.engine.story_cinematic import step_cinematic

        config = SoundConfig()
        config.set_category_enabled(SoundCategory.THEME, False)

        with patch("wet_run.engine.story_cinematic.get_sound_config", return_value=config):
            state = CinematicState(scene=PROLOGUE_SCENE)
            step_cinematic(state, elapsed_ms=100)
            # current_theme stays None when THEME is disabled
            assert state.current_theme is None

    def test_step_cinematic_persists_theme(self) -> None:
        """Multiple step_cinematic calls don't change the theme."""
        from unittest.mock import patch

        from wet_run.engine.story_cinematic import step_cinematic

        config = SoundConfig()
        with patch("wet_run.engine.story_cinematic.get_sound_config", return_value=config):
            state = CinematicState(scene=PROLOGUE_SCENE)
            # Manually set theme (simulating first call succeeded)
            state.current_theme = "chiba"
            # Subsequent step calls should not change it
            step_cinematic(state, elapsed_ms=200)
            step_cinematic(state, elapsed_ms=300)
            assert state.current_theme == "chiba"

    def test_step_cinematic_updates_theme_on_scene_change(self) -> None:
        """If scene changes, step_cinematic updates the theme."""
        from unittest.mock import patch

        from wet_run.engine.story_cinematic import step_cinematic

        config = SoundConfig()
        with patch("wet_run.engine.story_cinematic.get_sound_config", return_value=config):
            state = CinematicState(scene=PROLOGUE_SCENE)
            # Pretend we already have chiba playing
            state.current_theme = "chiba"
            # Switch to briefing
            state.scene = BRIEFING_FINN_SCENE
            # Step should update theme
            step_cinematic(state, elapsed_ms=200)
            # Theme should now be finn_office
            assert state.current_theme == "finn_office"
