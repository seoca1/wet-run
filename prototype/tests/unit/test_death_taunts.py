"""Tests for Death Taunts Library (ADR-0168)."""

from __future__ import annotations

import random

from wet_run.combat.death_taunts import (
    DEATH_TAUNTS,
    DeathTaunt,
    add_taunt,
    all_taunt_ice_ids,
    get_taunt,
    get_taunt_texts,
    has_taunt,
    register_taunts,
    taunt_count,
)


def test_registry_has_core_ice_types() -> None:
    core_types = {"watchdog", "goliath", "black", "construct", "standard", "patrol", "hunter"}
    for ice_type in core_types:
        assert has_taunt(ice_type), f"Missing taunts for {ice_type}"


def test_registry_has_boss_taunts() -> None:
    boss_types = {"wintermute", "ta_construct_prime", "neuromancer"}
    for boss in boss_types:
        assert has_taunt(boss), f"Missing taunts for boss {boss}"


def test_get_taunt_returns_text() -> None:
    rng = random.Random(42)
    taunt = get_taunt("watchdog", rng)
    assert taunt is not None
    assert isinstance(taunt, str)
    assert len(taunt) > 0


def test_get_taunt_for_boss() -> None:
    rng = random.Random(42)
    taunt = get_taunt("wintermute", rng)
    assert taunt is not None


def test_get_taunt_nonexistent_returns_none() -> None:
    rng = random.Random(42)
    taunt = get_taunt("nonexistent_ice", rng)
    assert taunt is None


def test_taunt_count() -> None:
    assert taunt_count("watchdog") == 3
    assert taunt_count("goliath") == 3
    assert taunt_count("black") == 3
    assert taunt_count("construct") == 2
    assert taunt_count("neuromancer") == 1
    assert taunt_count("nonexistent") == 0


def test_all_taunt_ice_ids_returns_all() -> None:
    ids = all_taunt_ice_ids()
    assert "watchdog" in ids
    assert "wintermute" in ids
    assert "ta_construct_prime" in ids
    assert len(ids) >= 10


def test_get_taunt_texts_returns_all() -> None:
    texts = get_taunt_texts("watchdog")
    assert len(texts) == 3
    assert all(isinstance(t, str) for t in texts)


def test_add_taunt_appends() -> None:
    initial = taunt_count("watchdog")
    add_taunt("watchdog", DeathTaunt("watchdog", "Watchdog", "Custom line.", 1.0))
    assert taunt_count("watchdog") == initial + 1


def test_register_taunts_replaces() -> None:
    new_taunts = (DeathTaunt("watchdog", "Watchdog", "Only one.", 1.0),)
    register_taunts("watchdog", new_taunts)
    assert taunt_count("watchdog") == 1
    assert get_taunt_texts("watchdog") == ("Only one.",)


def test_taunt_rarity_field_is_valid() -> None:
    for ice_type in all_taunt_ice_ids():
        for taunt in DEATH_TAUNTS[ice_type]:
            assert 0.0 <= taunt.rarity <= 1.0
