"""Unit tests for the settings UI (volume, mute)."""

from __future__ import annotations


class TestSettingsUI:
    """Tests for settings_ui module functions."""

    def test_get_volume_returns_float(self) -> None:
        """get_volume() returns a float in 0.0-1.0 range."""
        from wet_run.engine.settings_ui import get_volume

        vol = get_volume()
        assert isinstance(vol, float)
        assert 0.0 <= vol <= 1.0

    def test_set_volume_updates_value(self) -> None:
        """set_volume() persists to the global sound manager."""
        from wet_run.engine.settings_ui import get_volume, set_volume

        set_volume(0.7)
        assert get_volume() == 0.7
        set_volume(0.3)
        assert get_volume() == 0.3
        # Reset to default
        set_volume(0.5)

    def test_adjust_volume_increments(self) -> None:
        """adjust_volume(+0.1) increases by 0.1."""
        from wet_run.engine.settings_ui import adjust_volume, set_volume

        set_volume(0.5)
        new_vol = adjust_volume(+0.1)
        assert new_vol == pytest_approx(0.6)
        # Reset
        set_volume(0.5)

    def test_adjust_volume_decrements(self) -> None:
        """adjust_volume(-0.1) decreases by 0.1."""
        from wet_run.engine.settings_ui import adjust_volume, set_volume

        set_volume(0.5)
        new_vol = adjust_volume(-0.1)
        assert new_vol == pytest_approx(0.4)
        # Reset
        set_volume(0.5)

    def test_adjust_volume_clamps_high(self) -> None:
        """adjust_volume cannot exceed 1.0."""
        from wet_run.engine.settings_ui import adjust_volume, set_volume

        set_volume(0.95)
        new_vol = adjust_volume(+0.5)
        assert new_vol == 1.0
        # Reset
        set_volume(0.5)

    def test_adjust_volume_clamps_low(self) -> None:
        """adjust_volume cannot go below 0.0."""
        from wet_run.engine.settings_ui import adjust_volume, set_volume

        set_volume(0.05)
        new_vol = adjust_volume(-0.5)
        assert new_vol == 0.0
        # Reset
        set_volume(0.5)

    def test_is_muted_returns_bool(self) -> None:
        """is_muted() returns a bool."""
        from wet_run.engine.settings_ui import is_muted, set_volume

        set_volume(0.5)  # Reset to default
        result = is_muted()
        assert isinstance(result, bool)

    def test_toggle_mute_flips(self) -> None:
        """toggle_mute() flips state and returns new value."""
        from wet_run.engine.settings_ui import is_muted, toggle_mute

        initial = is_muted()
        new_state = toggle_mute()
        assert new_state != initial
        assert is_muted() == new_state
        # Restore
        toggle_mute()


def pytest_approx(value: float) -> object:
    """Helper for approximate float comparison."""
    import pytest

    return pytest.approx(value)
