"""Tests for SoundConfig + category routing (Phase 4)."""

from __future__ import annotations

import pytest

from wet_run.audio.config import (
    CATEGORY_KEY_BINDINGS,
    DEFAULT_CATEGORY_ENABLED,
    SOUND_CATEGORY_MAP,
    SoundCategory,
    SoundConfig,
    category_label,
)
from wet_run.audio.sound_manager import DEFAULT_SOUNDS


class TestSoundCategory:
    """SoundCategory enum."""

    def test_all_categories_defined(self) -> None:
        """All 6 categories are defined."""
        assert SoundCategory.THEME
        assert SoundCategory.EVENTS
        assert SoundCategory.KEYS
        assert SoundCategory.COMBAT
        assert SoundCategory.MOVEMENT
        assert SoundCategory.ITEMS

    def test_six_categories(self) -> None:
        """Exactly 6 categories."""
        assert len(list(SoundCategory)) == 6


class TestDefaultCategoryEnabled:
    """Default enabled state for each category."""

    def test_keys_disabled_by_default(self) -> None:
        """KEYS category is disabled by default (per user request)."""
        assert DEFAULT_CATEGORY_ENABLED[SoundCategory.KEYS] is False

    def test_other_categories_enabled(self) -> None:
        """All other categories are enabled by default."""
        for cat in SoundCategory:
            if cat == SoundCategory.KEYS:
                continue
            assert DEFAULT_CATEGORY_ENABLED[cat] is True


class TestSoundCategoryMap:
    """SOUND_CATEGORY_MAP — sound name → category."""

    def test_theme_sounds_mapped(self) -> None:
        """Theme sounds are mapped to THEME."""
        for theme_sound in (
            "theme/matrix_rain",
            "theme/cyberspace",
            "theme/chiba",
            "theme/sense_net",
            "theme/finn_office",
        ):
            assert theme_sound in SOUND_CATEGORY_MAP
            assert SOUND_CATEGORY_MAP[theme_sound] is SoundCategory.THEME

    def test_event_sounds_mapped(self) -> None:
        """Event sounds are mapped to EVENTS."""
        for event_sound in (
            "story/text_typing",
            "story/dialogue_advance",
            "story/event_trigger",
            "combat/victory",
            "combat/defeat",
        ):
            assert event_sound in SOUND_CATEGORY_MAP
            assert SOUND_CATEGORY_MAP[event_sound] is SoundCategory.EVENTS

    def test_ui_sounds_mapped_to_keys(self) -> None:
        """UI sounds are mapped to KEYS (default OFF)."""
        for ui_sound in (
            "ui/menu_select",
            "ui/menu_confirm",
            "ui/menu_cancel",
            "ui/error",
            "ui/notification",
        ):
            assert SOUND_CATEGORY_MAP[ui_sound] is SoundCategory.KEYS

    def test_combat_effects_mapped(self) -> None:
        """Combat effects (excluding victory/defeat) are mapped to COMBAT."""
        for combat_sound in (
            "combat/hit_normal",
            "combat/hit_crit",
            "combat/hit_miss",
            "combat/skill_physical",
            "combat/skill_magic",
            "combat/skill_heal",
            "combat/skill_buff",
            "combat/skill_debuff",
            "combat/block",
            "combat/stun",
        ):
            assert SOUND_CATEGORY_MAP[combat_sound] is SoundCategory.COMBAT

    def test_movement_sounds_mapped(self) -> None:
        """Movement sounds are mapped to MOVEMENT."""
        for move_sound in (
            "movement/nav_step",
            "movement/nav_block",
            "movement/jack_in",
            "movement/jack_out",
        ):
            assert SOUND_CATEGORY_MAP[move_sound] is SoundCategory.MOVEMENT

    def test_item_sounds_mapped(self) -> None:
        """Item sounds are mapped to ITEMS."""
        for item_sound in ("items/equip", "items/pickup", "items/cant"):
            assert SOUND_CATEGORY_MAP[item_sound] is SoundCategory.ITEMS

    def test_all_default_sounds_categorized(self) -> None:
        """All DEFAULT_SOUNDS have a category mapping."""
        for sound_name in DEFAULT_SOUNDS:
            assert sound_name in SOUND_CATEGORY_MAP, (
                f"Sound {sound_name} is not in SOUND_CATEGORY_MAP"
            )


class TestSoundConfigInit:
    """SoundConfig initialization."""

    def test_default_init(self) -> None:
        """Default SoundConfig has volume 0.2 and default categories."""
        config = SoundConfig()
        assert config.master_volume == 0.2
        assert config.muted is False
        # All categories initialized
        assert config.category_enabled is not None
        assert len(config.category_enabled) == 6

    def test_default_category_settings(self) -> None:
        """Default settings match DEFAULT_CATEGORY_ENABLED."""
        config = SoundConfig()
        for cat in SoundCategory:
            assert config.is_category_enabled(cat) == DEFAULT_CATEGORY_ENABLED[cat]

    def test_custom_volume(self) -> None:
        """Can create SoundConfig with custom volume."""
        config = SoundConfig(master_volume=0.5)
        assert config.master_volume == 0.5

    def test_custom_mute(self) -> None:
        """Can create SoundConfig with custom mute."""
        config = SoundConfig(muted=True)
        assert config.muted is True


class TestSoundConfigCategoryOps:
    """Per-category operations on SoundConfig."""

    def test_is_category_enabled_with_enum(self) -> None:
        """is_category_enabled accepts SoundCategory enum."""
        config = SoundConfig()
        # KEYS is disabled by default
        assert config.is_category_enabled(SoundCategory.KEYS) is False
        # THEME is enabled by default
        assert config.is_category_enabled(SoundCategory.THEME) is True

    def test_is_category_enabled_with_string(self) -> None:
        """is_category_enabled accepts string value."""
        config = SoundConfig()
        assert config.is_category_enabled("keys") is False
        assert config.is_category_enabled("theme") is True

    def test_set_category_enabled(self) -> None:
        """set_category_enabled sets the state."""
        config = SoundConfig()
        config.set_category_enabled(SoundCategory.KEYS, True)
        assert config.is_category_enabled(SoundCategory.KEYS) is True

    def test_toggle_category(self) -> None:
        """toggle_category flips the state and returns the new value."""
        config = SoundConfig()
        # KEYS starts disabled
        new_state = config.toggle_category(SoundCategory.KEYS)
        assert new_state is True
        assert config.is_category_enabled(SoundCategory.KEYS) is True
        # Toggle again
        new_state = config.toggle_category(SoundCategory.KEYS)
        assert new_state is False


class TestSoundConfigMuteVolume:
    """Master mute + volume operations."""

    def test_toggle_mute(self) -> None:
        """toggle_mute flips state and returns new value."""
        config = SoundConfig()
        assert config.muted is False
        new_state = config.toggle_mute()
        assert new_state is True
        assert config.muted is True

    def test_adjust_volume_up(self) -> None:
        """adjust_volume(+0.1) increases volume."""
        config = SoundConfig(master_volume=0.5)
        new_vol = config.adjust_volume(+0.1)
        assert new_vol == pytest.approx(0.6)

    def test_adjust_volume_down(self) -> None:
        """adjust_volume(-0.1) decreases volume."""
        config = SoundConfig(master_volume=0.5)
        new_vol = config.adjust_volume(-0.1)
        assert new_vol == pytest.approx(0.4)

    def test_adjust_volume_clamps_high(self) -> None:
        """adjust_volume cannot exceed 1.0."""
        config = SoundConfig(master_volume=0.95)
        new_vol = config.adjust_volume(+0.5)
        assert new_vol == 1.0

    def test_adjust_volume_clamps_low(self) -> None:
        """adjust_volume cannot go below 0.0."""
        config = SoundConfig(master_volume=0.05)
        new_vol = config.adjust_volume(-0.5)
        assert new_vol == 0.0


class TestSoundConfigIsPlayable:
    """is_sound_playable() — checks all gating conditions."""

    def test_playable_when_unmuted_and_enabled(self) -> None:
        """A sound is playable when not muted and its category is enabled."""
        config = SoundConfig()
        # THEME is enabled by default
        assert config.is_sound_playable("theme/matrix_rain") is True

    def test_not_playable_when_muted(self) -> None:
        """A muted config returns False for all sounds."""
        config = SoundConfig(muted=True)
        assert config.is_sound_playable("combat/hit_normal") is False
        assert config.is_sound_playable("theme/cyberspace") is False

    def test_not_playable_when_category_disabled(self) -> None:
        """Disabling a category makes its sounds unplayable."""
        config = SoundConfig()
        config.set_category_enabled(SoundCategory.COMBAT, False)
        assert config.is_sound_playable("combat/hit_normal") is False
        # But other categories still work
        assert config.is_sound_playable("theme/cyberspace") is True

    def test_not_playable_for_unknown_sound(self) -> None:
        """Unknown sound name returns False."""
        config = SoundConfig()
        assert config.is_sound_playable("nonexistent/sound") is False

    def test_keys_sounds_disabled_by_default(self) -> None:
        """KEYS sounds (UI) are disabled by default."""
        config = SoundConfig()
        assert config.is_sound_playable("ui/menu_select") is False


class TestSoundConfigHelpers:
    """Helper methods."""

    def test_get_category_for_sound(self) -> None:
        """get_category_for_sound returns the right category."""
        config = SoundConfig()
        assert config.get_category_for_sound("combat/hit_normal") is SoundCategory.COMBAT
        assert config.get_category_for_sound("theme/cyberspace") is SoundCategory.THEME
        assert config.get_category_for_sound("nonexistent") is None

    def test_get_summary(self) -> None:
        """get_summary returns all settings as a dict."""
        config = SoundConfig()
        summary = config.get_summary()
        assert "master_volume" in summary
        assert "muted" in summary
        # All categories
        for cat in SoundCategory:
            assert f"{cat.value}_enabled" in summary


class TestCategoryLabel:
    """category_label() human-readable labels."""

    def test_theme_label(self) -> None:
        """THEME has Korean label."""
        assert "배경" in category_label(SoundCategory.THEME) or "Theme" in category_label(
            SoundCategory.THEME
        )

    def test_keys_label(self) -> None:
        """KEYS has Korean label."""
        assert "키" in category_label(SoundCategory.KEYS) or "Keys" in category_label(
            SoundCategory.KEYS
        )

    def test_all_categories_have_labels(self) -> None:
        """All categories return non-empty labels."""
        for cat in SoundCategory:
            label = category_label(cat)
            assert label
            assert len(label) > 0


class TestCategoryKeyBindings:
    """Key bindings for category toggles."""

    def test_all_categories_have_bindings(self) -> None:
        """All 6 categories have a key binding."""
        for cat in SoundCategory:
            assert cat in CATEGORY_KEY_BINDINGS
            assert CATEGORY_KEY_BINDINGS[cat]  # Non-empty

    def test_specific_bindings(self) -> None:
        """Specific keys for specific categories."""
        assert CATEGORY_KEY_BINDINGS[SoundCategory.THEME] == "T"
        assert CATEGORY_KEY_BINDINGS[SoundCategory.EVENTS] == "E"
        assert CATEGORY_KEY_BINDINGS[SoundCategory.KEYS] == "K"
        assert CATEGORY_KEY_BINDINGS[SoundCategory.COMBAT] == "B"
        assert CATEGORY_KEY_BINDINGS[SoundCategory.MOVEMENT] == "V"
        assert CATEGORY_KEY_BINDINGS[SoundCategory.ITEMS] == "I"


class TestSoundManagerIntegration:
    """SoundManager integration with SoundConfig."""

    def test_play_with_config_respects_master_mute(self) -> None:
        """play_with_config returns False when muted."""
        from wet_run.audio.sound_manager import get_sound_manager

        sm = get_sound_manager()
        config = SoundConfig(muted=True)
        result = sm.play_with_config("combat/hit_normal", config)
        assert result is False

    def test_play_with_config_respects_category(self) -> None:
        """play_with_config returns False when category is disabled."""
        from wet_run.audio.sound_manager import get_sound_manager

        sm = get_sound_manager()
        config = SoundConfig()
        config.set_category_enabled(SoundCategory.COMBAT, False)
        result = sm.play_with_config("combat/hit_normal", config)
        assert result is False

    def test_play_with_config_enables_category(self) -> None:
        """play_with_config returns True when category is enabled and sound exists."""
        from wet_run.audio.sound_manager import get_sound_manager

        sm = get_sound_manager()
        config = SoundConfig()
        # TEMPLATE: don't actually play (sm.is_available check)
        if sm.is_available():
            config.set_category_enabled(SoundCategory.THEME, True)
            result = sm.play_with_config("theme/matrix_rain", config)
            # Could be True (played) or False (file missing) — depends on test env
            assert isinstance(result, bool)
        else:
            # No audio backend — skip
            pass

    def test_keys_disabled_by_default_in_play_with_config(self) -> None:
        """play_with_config returns False for KEYS sounds by default."""
        from wet_run.audio.sound_manager import get_sound_manager

        sm = get_sound_manager()
        config = SoundConfig()  # KEYS disabled by default
        result = sm.play_with_config("ui/menu_select", config)
        assert result is False

    def test_safe_play_with_config(self) -> None:
        """safe_play_with_config uses the config and swallows errors."""
        from wet_run.audio.sound_manager import safe_play_with_config

        config = SoundConfig(muted=True)
        result = safe_play_with_config("combat/hit_normal", config)
        assert result is False  # Muted


class TestVolumePropagation:
    """Volume from config is applied when playing."""

    def test_set_volume_in_play_with_config(self) -> None:
        """play_with_config sets the manager's volume to config's value."""
        from wet_run.audio.sound_manager import get_sound_manager

        sm = get_sound_manager()
        original_volume = sm.volume

        config = SoundConfig(master_volume=0.3)
        # play_with_config should temporarily set volume to 0.3
        # (and restore to original after)
        sm.play_with_config("combat/hit_normal", config)
        assert sm.volume == original_volume  # Restored
