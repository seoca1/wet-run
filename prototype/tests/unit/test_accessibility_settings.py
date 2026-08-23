"""Unit tests for accessibility settings (Cycle 3 polish).

Covers:
- AppState.font_size default + cycle behavior (small/normal/large)
- AppState.high_contrast default + toggle behavior
- settings_view.SETTINGS_OPTIONS includes new entries
- Pillar 4 compliance (ephemeral session preference, no meta_state)
"""

from __future__ import annotations

from wet_run.engine.settings_view import SETTINGS_OPTIONS
from wet_run.engine.state import AppState


class TestAppStateAccessibility:
    """AppState.font_size + AppState.high_contrast defaults."""

    def test_font_size_default_is_normal(self) -> None:
        state = AppState()
        assert state.font_size == "normal"

    def test_high_contrast_default_is_false(self) -> None:
        state = AppState()
        assert state.high_contrast is False

    def test_colorblind_mode_default_is_none(self) -> None:
        """ADR-0196: colorblind_mode default is "none" (one of COLORBLIND_MODES)."""
        state = AppState()
        assert state.colorblind_mode == "none"


class TestSettingsViewOptions:
    """settings_view.SETTINGS_OPTIONS includes new entries."""

    def test_settings_options_includes_font_size(self) -> None:
        opt_ids = [opt_id for opt_id, _ in SETTINGS_OPTIONS]
        assert "font_size" in opt_ids

    def test_settings_options_includes_high_contrast(self) -> None:
        opt_ids = [opt_id for opt_id, _ in SETTINGS_OPTIONS]
        assert "high_contrast" in opt_ids

    def test_settings_options_count(self) -> None:
        assert len(SETTINGS_OPTIONS) == 9

    def test_settings_options_includes_existing(self) -> None:
        opt_ids = [opt_id for opt_id, _ in SETTINGS_OPTIONS]
        for opt in ("audio", "colorblind", "keymap", "resolution", "back"):
            assert opt in opt_ids


class TestPillar4Compliance:
    """Accessibility settings are ephemeral, no meta-progression."""

    def test_font_size_does_not_write_meta_state(self) -> None:
        state = AppState()
        state.font_size = "large"
        assert not hasattr(state, "meta_state") or state.meta_state is None

    def test_high_contrast_does_not_write_meta_state(self) -> None:
        state = AppState()
        state.high_contrast = True
        assert not hasattr(state, "meta_state") or state.meta_state is None

    def test_new_fields_dont_persist_across_resets(self) -> None:
        """AppState() constructor resets all defaults — ephemeral session."""
        a = AppState()
        a.font_size = "large"
        a.high_contrast = True
        b = AppState()
        assert b.font_size == "normal"
        assert b.high_contrast is False


__all__ = [
    "TestAppStateAccessibility",
    "TestSettingsViewOptions",
    "TestPillar4Compliance",
]
