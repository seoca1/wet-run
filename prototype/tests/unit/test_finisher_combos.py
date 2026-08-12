"""Tests for Finisher Combos (ADR-0181)."""

from __future__ import annotations

import dataclasses

import pytest

from roguelike_sprawl.combat.finisher_combos import (
    FINISHER_REGISTRY,
    FinisherCombo,
    can_trigger_finisher,
    get_finisher,
    get_finisher_count,
    get_finisher_ids,
    get_finisher_remaining_cooldown,
    get_highest_combo_finisher,
    has_finisher,
    list_available_finishers,
    list_finishers,
)


def test_registry_has_4_finishers() -> None:
    assert get_finisher_count() == 4


def test_get_finisher_existing() -> None:
    finisher = get_finisher("burst")
    assert finisher is not None
    assert finisher.name == "BURST"


def test_get_finisher_nonexistent() -> None:
    assert get_finisher("nonexistent") is None


def test_list_finishers() -> None:
    finishers = list_finishers()
    assert len(finishers) == 4
    assert all(isinstance(f, FinisherCombo) for f in finishers)


def test_get_highest_combo_finisher_low() -> None:
    assert get_highest_combo_finisher(0) is None
    assert get_highest_combo_finisher(4) is None


def test_get_highest_combo_finisher_burst() -> None:
    finisher = get_highest_combo_finisher(5)
    assert finisher is not None
    assert finisher.id == "burst"


def test_get_highest_combo_finisher_pierce() -> None:
    finisher = get_highest_combo_finisher(8)
    assert finisher is not None
    assert finisher.id == "pierce"


def test_get_highest_combo_finisher_burn() -> None:
    finisher = get_highest_combo_finisher(15)
    assert finisher is not None
    assert finisher.id == "burn"


def test_list_available_finishers() -> None:
    at_5 = list_available_finishers(5)
    assert len(at_5) == 1
    assert at_5[0].id == "burst"
    at_12 = list_available_finishers(12)
    assert len(at_12) == 3


def test_can_trigger_finisher_ok() -> None:
    assert can_trigger_finisher(5, "burst", 0, 4000)


def test_can_trigger_finisher_low_combo() -> None:
    assert not can_trigger_finisher(3, "burst", 0, 1000)


def test_can_trigger_finisher_on_cooldown() -> None:
    assert not can_trigger_finisher(5, "burst", 0, 100)
    assert can_trigger_finisher(5, "burst", 0, 4000)


def test_can_trigger_finisher_unknown() -> None:
    assert not can_trigger_finisher(5, "nonexistent", 0, 1000)


def test_get_finisher_remaining_cooldown() -> None:
    assert get_finisher_remaining_cooldown("burst", 0, 0) == 3000
    assert get_finisher_remaining_cooldown("burst", 0, 3000) == 0
    assert get_finisher_remaining_cooldown("burst", 0, 5000) == 0


def test_get_finisher_remaining_cooldown_unknown() -> None:
    assert get_finisher_remaining_cooldown("nonexistent", 0, 0) == 0


def test_get_finisher_ids() -> None:
    ids = get_finisher_ids()
    assert "burst" in ids
    assert "pierce" in ids
    assert "silence" in ids
    assert "burn" in ids


def test_has_finisher() -> None:
    assert has_finisher("burst")
    assert not has_finisher("nonexistent")


def test_threshold_progression() -> None:
    thresholds = [
        f.combo_threshold
        for f in sorted(FINISHER_REGISTRY.values(), key=lambda f: f.combo_threshold)
    ]
    assert thresholds == [5, 8, 12, 15]


def test_finisher_immutable() -> None:
    finisher = get_finisher("burst")
    assert finisher is not None
    try:
        finisher.name = "Modified"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_each_finisher_has_effect_type() -> None:
    for finisher in list_finishers():
        assert finisher.effect_type != ""


def test_cooldown_positive() -> None:
    for finisher in list_finishers():
        assert finisher.cooldown_ms > 0


def test_damage_multiplier_positive() -> None:
    for finisher in list_finishers():
        assert finisher.damage_multiplier > 0


def test_all_finisher_ids_unique() -> None:
    ids = [f.id for f in list_finishers()]
    assert len(ids) == len(set(ids))
