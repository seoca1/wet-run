"""Tests for ASCII Battle Portrait Evolution (ADR-0171)."""

from __future__ import annotations

import dataclasses

import pytest

from wet_run.combat.battle_portraits import (
    BOSS_PHASE_COLORS,
    HP_THRESHOLDS,
    ICE_COLORS,
    get_color_for_threshold,
    get_glyph_for_threshold,
    get_hp_threshold,
    get_known_ice_types,
    get_phase_count,
    get_portrait,
    get_status_overlay,
    is_known_ice_type,
)


def test_hp_threshold_full() -> None:
    assert get_hp_threshold(1.0) == "full"
    assert get_hp_threshold(0.95) == "full"


def test_hp_threshold_healthy() -> None:
    assert get_hp_threshold(0.7) == "healthy"
    assert get_hp_threshold(0.85) == "healthy"


def test_hp_threshold_wounded() -> None:
    assert get_hp_threshold(0.4) == "wounded"
    assert get_hp_threshold(0.5) == "wounded"


def test_hp_threshold_critical() -> None:
    assert get_hp_threshold(0.2) == "critical"
    assert get_hp_threshold(0.3) == "critical"


def test_hp_threshold_dying() -> None:
    assert get_hp_threshold(0.1) == "dying"
    assert get_hp_threshold(0.0) == "dying"


def test_hp_threshold_boundaries() -> None:
    assert get_hp_threshold(HP_THRESHOLDS["full"]) == "full"
    assert get_hp_threshold(HP_THRESHOLDS["healthy"]) == "healthy"
    assert get_hp_threshold(HP_THRESHOLDS["wounded"]) == "wounded"
    assert get_hp_threshold(HP_THRESHOLDS["critical"]) == "critical"


def test_get_color_for_threshold_darkens() -> None:
    base = ICE_COLORS["watchdog"]
    full = get_color_for_threshold("watchdog", "full")
    healthy = get_color_for_threshold("watchdog", "healthy")
    wounded = get_color_for_threshold("watchdog", "wounded")
    critical = get_color_for_threshold("watchdog", "critical")
    dying = get_color_for_threshold("watchdog", "dying")
    assert full == base
    assert healthy[0] < full[0]
    assert wounded[0] < healthy[0]
    assert critical[0] < wounded[0]
    assert dying == (255, 0, 0)


def test_get_color_for_threshold_unknown_ice() -> None:
    color = get_color_for_threshold("nonexistent", "full")
    assert color == (200, 200, 200)


def test_get_status_overlay_burn() -> None:
    assert get_status_overlay(("burn",)) == "^"


def test_get_status_overlay_stun() -> None:
    assert get_status_overlay(("stun",)) == "~"


def test_get_status_overlay_slow() -> None:
    assert get_status_overlay(("slow",)) == "..."


def test_get_status_overlay_silence() -> None:
    assert get_status_overlay(("silence",)) == "X"


def test_get_status_overlay_vulnerable() -> None:
    assert get_status_overlay(("vulnerable",)) == "!"


def test_get_status_overlay_multiple() -> None:
    overlay = get_status_overlay(("burn", "stun"))
    assert "^" in overlay
    assert "~" in overlay


def test_get_status_overlay_none() -> None:
    assert get_status_overlay(()) == ""


def test_get_glyph_for_threshold_baseline() -> None:
    assert get_glyph_for_threshold("watchdog", "full") == "W"


def test_get_glyph_for_threshold_dying() -> None:
    assert get_glyph_for_threshold("watchdog", "dying") == "w"


def test_get_glyph_for_threshold_critical() -> None:
    assert get_glyph_for_threshold("watchdog", "critical") == "W*"


def test_get_glyph_for_threshold_unknown_ice() -> None:
    assert get_glyph_for_threshold("nonexistent", "full") == "?"


def test_get_portrait_basic() -> None:
    portrait = get_portrait("watchdog", hp_ratio=1.0)
    assert portrait.base_glyph == "W"
    assert portrait.color == ICE_COLORS["watchdog"]


def test_get_portrait_with_status_effects() -> None:
    portrait = get_portrait("watchdog", hp_ratio=1.0, status_effect_ids=("burn", "stun"))
    assert portrait.effect_overlay != ""


def test_get_portrait_boss_phase_4_color() -> None:
    portrait = get_portrait("wintermute", hp_ratio=1.0, phase=4)
    assert portrait.color == BOSS_PHASE_COLORS["wintermute"][4]


def test_get_portrait_boss_phase_max() -> None:
    portrait = get_portrait("wintermute", hp_ratio=1.0, phase=99)
    assert portrait.color == BOSS_PHASE_COLORS["wintermute"][4]


def test_get_portrait_dying_glyph_lowercase() -> None:
    portrait = get_portrait("watchdog", hp_ratio=0.05)
    assert portrait.base_glyph == "w"


def test_get_portrait_suffix_with_overlay() -> None:
    portrait = get_portrait("watchdog", hp_ratio=1.0, status_effect_ids=("burn",))
    assert portrait.suffix.startswith(" [")
    assert portrait.suffix.endswith("]")


def test_get_known_ice_types() -> None:
    types = get_known_ice_types()
    assert "watchdog" in types
    assert "goliath" in types
    assert "wintermute" in types
    assert "ta_construct_prime" in types


def test_is_known_ice_type() -> None:
    assert is_known_ice_type("watchdog")
    assert is_known_ice_type("wintermute")
    assert not is_known_ice_type("nonexistent")


def test_get_phase_count_boss() -> None:
    assert get_phase_count("wintermute") == 4
    assert get_phase_count("ta_construct_prime") == 4


def test_get_phase_count_non_boss() -> None:
    assert get_phase_count("watchdog") == 0
    assert get_phase_count("goliath") == 0


def test_portrait_immutable() -> None:
    portrait = get_portrait("watchdog", hp_ratio=1.0)
    try:
        portrait.base_glyph = "X"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass
