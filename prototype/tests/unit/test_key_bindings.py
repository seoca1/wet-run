"""Integration tests for sound config key bindings (Phase 5-2).

Verifies that the app.py and death.py handlers correctly process
key events for M (mute) and T/E/K/B/V/I (per-category toggle).

Note: These tests use the singleton SoundConfig from audio module
because the toggle helpers operate on it.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from wet_run.audio.config import SoundCategory
from wet_run.audio.sound_manager import get_sound_config


def _make_keydown(sym: object) -> MagicMock:
    """Create a mock KeyDown event with a given sym."""
    event = MagicMock()
    event.sym = sym
    return event


class TestKeyBindingLogic:
    """Verify the key binding logic from settings_ui."""

    def setup_method(self) -> None:
        """Reset SoundConfig to defaults before each test."""
        # Force the singleton to be created with default settings
        import wet_run.audio

        wet_run.audio._manager = None  # type: ignore[attr-defined]
        cfg = get_sound_config()
        cfg.muted = False
        cfg.master_volume = 0.2
        from wet_run.audio.config import DEFAULT_CATEGORY_ENABLED

        for cat, enabled in DEFAULT_CATEGORY_ENABLED.items():
            cfg.set_category_enabled(cat, enabled)

    def teardown_method(self) -> None:
        """Reset volume after each test (for next test isolation)."""
        cfg = get_sound_config()
        cfg.master_volume = 0.2

    def test_toggle_category_via_helper(self) -> None:
        """toggle_category() helper actually toggles the singleton config."""
        from wet_run.engine.settings_ui import toggle_category

        config = get_sound_config()
        # THEME is ON by default
        assert config.is_category_enabled(SoundCategory.THEME) is True
        new_state = toggle_category(SoundCategory.THEME)
        assert new_state is False
        assert config.is_category_enabled(SoundCategory.THEME) is False

    def test_toggle_k_from_off(self) -> None:
        """K key toggles KEYS from default OFF to ON."""
        from wet_run.engine.settings_ui import toggle_category

        config = get_sound_config()
        # KEYS is OFF by default
        assert config.is_category_enabled(SoundCategory.KEYS) is False
        new_state = toggle_category(SoundCategory.KEYS)
        assert new_state is True
        assert config.is_category_enabled(SoundCategory.KEYS) is True

    def test_master_mute_toggle(self) -> None:
        """Master mute toggle works via SoundConfig."""
        config = get_sound_config()
        assert config.muted is False
        new_state = config.toggle_mute()
        assert new_state is True
        assert config.muted is True

    def test_volume_up(self) -> None:
        """Volume up via adjust_volume(+0.1)."""
        from wet_run.audio import sound_manager
        from wet_run.engine.settings_ui import adjust_volume

        sm = sound_manager.get_sound_manager()
        sm.set_volume(0.5)
        new_vol = adjust_volume(+0.1)
        assert abs(new_vol - 0.6) < 0.001

    def test_volume_down(self) -> None:
        """Volume down via adjust_volume(-0.1)."""
        from wet_run.audio import sound_manager
        from wet_run.engine.settings_ui import adjust_volume

        sm = sound_manager.get_sound_manager()
        sm.set_volume(0.5)
        new_vol = adjust_volume(-0.1)
        assert abs(new_vol - 0.4) < 0.001

    def test_all_six_categories_toggleable(self) -> None:
        """All 6 categories can be toggled via helper."""
        from wet_run.engine.settings_ui import toggle_category

        config = get_sound_config()
        for cat in SoundCategory:
            before = config.is_category_enabled(cat)
            new_state = toggle_category(cat)
            assert new_state != before
            assert config.is_category_enabled(cat) != before


class TestCategoryKeyBindings:
    """CATEGORY_KEY_BINDINGS map keys to categories."""

    def test_all_keys_unique(self) -> None:
        """All 6 category keys are unique."""
        from wet_run.audio.config import CATEGORY_KEY_BINDINGS

        keys = list(CATEGORY_KEY_BINDINGS.values())
        assert len(keys) == len(set(keys))

    def test_keys_are_single_chars(self) -> None:
        """All keys are single characters."""
        from wet_run.audio.config import CATEGORY_KEY_BINDINGS

        for key in CATEGORY_KEY_BINDINGS.values():
            assert len(key) == 1
            assert key.isalpha()

    def test_t_maps_to_theme(self) -> None:
        """Pressing T maps to THEME category."""
        from wet_run.audio.config import CATEGORY_KEY_BINDINGS

        for cat, key in CATEGORY_KEY_BINDINGS.items():
            if key == "T":
                assert cat is SoundCategory.THEME
                break
        else:
            pytest.fail("T key not found")

    def test_e_maps_to_events(self) -> None:
        """Pressing E maps to EVENTS category."""
        from wet_run.audio.config import CATEGORY_KEY_BINDINGS

        for cat, key in CATEGORY_KEY_BINDINGS.items():
            if key == "E":
                assert cat is SoundCategory.EVENTS
                break
        else:
            pytest.fail("E key not found")

    def test_k_maps_to_keys(self) -> None:
        """Pressing K maps to KEYS category."""
        from wet_run.audio.config import CATEGORY_KEY_BINDINGS

        for cat, key in CATEGORY_KEY_BINDINGS.items():
            if key == "K":
                assert cat is SoundCategory.KEYS
                break
        else:
            pytest.fail("K key not found")

    def test_b_maps_to_combat(self) -> None:
        """Pressing B maps to COMBAT category."""
        from wet_run.audio.config import CATEGORY_KEY_BINDINGS

        for cat, key in CATEGORY_KEY_BINDINGS.items():
            if key == "B":
                assert cat is SoundCategory.COMBAT
                break
        else:
            pytest.fail("B key not found")

    def test_v_maps_to_movement(self) -> None:
        """Pressing V maps to MOVEMENT category."""
        from wet_run.audio.config import CATEGORY_KEY_BINDINGS

        for cat, key in CATEGORY_KEY_BINDINGS.items():
            if key == "V":
                assert cat is SoundCategory.MOVEMENT
                break
        else:
            pytest.fail("V key not found")

    def test_i_maps_to_items(self) -> None:
        """Pressing I maps to ITEMS category."""
        from wet_run.audio.config import CATEGORY_KEY_BINDINGS

        for cat, key in CATEGORY_KEY_BINDINGS.items():
            if key == "I":
                assert cat is SoundCategory.ITEMS
                break
        else:
            pytest.fail("I key not found")


class TestVolumePropagation:
    """Volume changes propagate to SoundManager."""

    def test_adjust_volume_changes_manager(self) -> None:
        """adjust_volume() updates both config and SoundManager."""
        from wet_run.audio import sound_manager
        from wet_run.engine.settings_ui import adjust_volume

        sm = sound_manager.get_sound_manager()
        sm.set_volume(0.3)

        new_vol = adjust_volume(+0.1)
        assert abs(new_vol - 0.4) < 0.001
        assert abs(sm.volume - 0.4) < 0.001

    def test_volume_clamped_high(self) -> None:
        """Volume cannot exceed 1.0."""
        from wet_run.audio import sound_manager
        from wet_run.engine.settings_ui import adjust_volume

        sm = sound_manager.get_sound_manager()
        sm.set_volume(0.95)
        new_vol = adjust_volume(+0.5)
        assert new_vol == 1.0

    def test_volume_clamped_low(self) -> None:
        """Volume cannot go below 0.0."""
        from wet_run.audio import sound_manager
        from wet_run.engine.settings_ui import adjust_volume

        sm = sound_manager.get_sound_manager()
        sm.set_volume(0.05)
        new_vol = adjust_volume(-0.5)
        assert new_vol == 0.0
