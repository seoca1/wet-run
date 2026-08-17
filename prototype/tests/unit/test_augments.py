"""Tests for Wetware Augments (ADR-0173)."""

from __future__ import annotations

import dataclasses

import pytest

from wet_run.combat.augments import (
    AUGMENT_REGISTRY,
    DEFAULT_AUGMENT_SLOTS,
    WetwareAugment,
    apply_augment_effect,
    augment_exists,
    get_augment,
    get_augment_count,
    get_augments_by_effect,
    get_augments_by_tier,
    list_augments,
)


def test_default_augment_slots() -> None:
    assert DEFAULT_AUGMENT_SLOTS == 6


def test_registry_has_20_plus_augments() -> None:
    assert get_augment_count() >= 20


def test_get_augment_existing() -> None:
    aug = get_augment("adrenal_boost")
    assert aug is not None
    assert aug.name == "Adrenal Boost"
    assert aug.effect_type == "ap_regen"


def test_get_augment_nonexistent() -> None:
    assert get_augment("nonexistent") is None


def test_augment_exists() -> None:
    assert augment_exists("titanium_bones")
    assert not augment_exists("nonexistent")


def test_list_augments() -> None:
    augments = list_augments()
    assert len(augments) >= 20
    assert all(isinstance(a, WetwareAugment) for a in augments)


def test_get_augments_by_effect() -> None:
    crit_augments = get_augments_by_effect("crit")
    assert len(crit_augments) >= 2
    assert all(a.effect_type == "crit" for a in crit_augments)


def test_get_augments_by_tier() -> None:
    tier1 = get_augments_by_tier(1)
    assert len(tier1) >= 10


def test_augment_immutable() -> None:
    aug = get_augment("kerenzikov")
    assert aug is not None
    try:
        aug.name = "Modified"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_apply_augment_effect_matching() -> None:
    aug = get_augment("reflex_boost")
    assert aug is not None
    assert apply_augment_effect(aug, "speed") == 0.1


def test_apply_augment_effect_not_matching() -> None:
    aug = get_augment("reflex_boost")
    assert aug is not None
    assert apply_augment_effect(aug, "damage") == 0.0


def test_all_augments_have_unique_ids() -> None:
    ids = list(AUGMENT_REGISTRY.keys())
    assert len(ids) == len(set(ids))


def test_all_augments_have_descriptions() -> None:
    for aug in AUGMENT_REGISTRY.values():
        assert aug.description != ""
        assert aug.name != ""


def test_augment_count_matches_registry() -> None:
    assert len(AUGMENT_REGISTRY) == get_augment_count()
    assert len(AUGMENT_REGISTRY) == len(list_augments())


def test_stealth_augments_present() -> None:
    stealth = get_augments_by_effect("stealth")
    assert len(stealth) >= 1


def test_combat_augments_present() -> None:
    ap_regen = get_augments_by_effect("ap_regen")
    assert len(ap_regen) >= 2


def test_augment_values_are_coherent() -> None:
    """Effect values should be reasonable for their type."""
    for aug in AUGMENT_REGISTRY.values():
        if aug.effect_type in ("crit", "dodge", "stealth", "speed"):
            assert -1.0 <= aug.effect_value <= 1.0, f"{aug.id}: bad value {aug.effect_value}"
        if aug.effect_type in ("ap_regen", "max_ap", "max_hp"):
            assert aug.effect_value > 0, f"{aug.id}: bad value {aug.effect_value}"
