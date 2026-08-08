"""Tests for Status Effects v2 (ADR-0179)."""

from __future__ import annotations

import dataclasses

import pytest

from roguelike_sprawl.combat.status_effects_v2 import (
    StatusEffectV2,
    apply_bleed,
    apply_confused,
    apply_fatigue,
    apply_terrified,
    get_status_v2,
    get_status_v2_by_type,
    get_status_v2_count,
    list_status_v2,
    make_status_v2,
)


def test_registry_has_4_effects() -> None:
    assert get_status_v2_count() == 4


def test_get_status_v2_existing() -> None:
    eff = get_status_v2("bleed")
    assert eff is not None
    assert eff.name == "BLEED"


def test_get_status_v2_nonexistent() -> None:
    assert get_status_v2("nonexistent") is None


def test_list_status_v2() -> None:
    effects = list_status_v2()
    assert len(effects) == 4
    assert all(isinstance(e, StatusEffectV2) for e in effects)


def test_get_status_v2_by_type() -> None:
    bleeds = get_status_v2_by_type("bleed")
    assert len(bleeds) == 1
    assert bleeds[0].name == "BLEED"


def test_apply_bleed() -> None:
    eff = apply_bleed()
    assert eff.effect_type == "bleed"
    assert eff.duration_ms == 5000


def test_apply_fatigue() -> None:
    eff = apply_fatigue()
    assert eff.effect_type == "fatigue"
    assert eff.value == -0.5


def test_apply_confused() -> None:
    eff = apply_confused()
    assert eff.effect_type == "confused"
    assert eff.value == 0.25


def test_apply_terrified() -> None:
    eff = apply_terrified()
    assert eff.effect_type == "terrified"
    assert eff.duration_ms == 4000


def test_apply_with_custom_duration() -> None:
    eff = apply_bleed(duration_ms=10000)
    assert eff.duration_ms == 10000


def test_make_status_v2_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown"):
        make_status_v2("nonexistent")


def test_status_v2_immutable() -> None:
    eff = get_status_v2("bleed")
    assert eff is not None
    try:
        eff.name = "Modified"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_all_effects_have_durations() -> None:
    for eff in list_status_v2():
        assert eff.duration_ms > 0


def test_fatigue_has_negative_ap_regen() -> None:
    fatigue = get_status_v2("fatigue")
    assert fatigue is not None
    assert fatigue.value < 0


def test_terrified_increases_damage_taken() -> None:
    terrified = get_status_v2("terrified")
    assert terrified is not None
    assert terrified.value > 0


def test_confused_has_miss_chance() -> None:
    confused = get_status_v2("confused")
    assert confused is not None
    assert 0.0 < confused.value < 1.0


def test_bleed_does_damage() -> None:
    bleed = get_status_v2("bleed")
    assert bleed is not None
    assert bleed.value > 0


def test_all_effects_have_unique_ids() -> None:
    ids = [e.id for e in list_status_v2()]
    assert len(ids) == len(set(ids))


def test_registry_has_all_four_types() -> None:
    types = {e.effect_type for e in list_status_v2()}
    assert "bleed" in types
    assert "fatigue" in types
    assert "confused" in types
    assert "terrified" in types


def test_all_effects_have_names() -> None:
    for eff in list_status_v2():
        assert eff.name != ""
