"""Tests for Deck Building (ADR-0178)."""

from __future__ import annotations

import dataclasses

import pytest

from roguelike_sprawl.combat.deck_building import (
    DECK_SIZES,
    get_ap_regen_bonus,
    get_cooldown_modifier,
    get_deck_size,
    get_deck_size_names,
    get_deck_sizes,
    get_default_deck_size,
    get_slot_limit,
    is_valid_deck_size,
)


def test_registry_has_3_sizes() -> None:
    assert len(DECK_SIZES) == 3


def test_get_deck_size_existing() -> None:
    deck = get_deck_size("light")
    assert deck is not None
    assert deck.name == "LIGHT"
    assert deck.slots == 6


def test_get_deck_size_case_insensitive() -> None:
    deck = get_deck_size("LIGHT")
    assert deck is not None
    assert deck.slots == 6


def test_get_deck_size_nonexistent() -> None:
    assert get_deck_size("nonexistent") is None


def test_get_deck_sizes() -> None:
    sizes = get_deck_sizes()
    assert len(sizes) == 3
    assert sizes[0].name == "LIGHT"
    assert sizes[1].name == "STANDARD"
    assert sizes[2].name == "HEAVY"


def test_slot_limits() -> None:
    assert get_slot_limit("light") == 6
    assert get_slot_limit("standard") == 8
    assert get_slot_limit("heavy") == 10


def test_slot_limit_invalid_returns_default() -> None:
    assert get_slot_limit("nonexistent") == 8


def test_ap_regen_bonuses() -> None:
    assert get_ap_regen_bonus("light") == 0.5
    assert get_ap_regen_bonus("standard") == 0.0
    assert get_ap_regen_bonus("heavy") == -0.3


def test_cooldown_modifiers() -> None:
    assert get_cooldown_modifier("light") == -0.10
    assert get_cooldown_modifier("standard") == 0.0
    assert get_cooldown_modifier("heavy") == 0.15


def test_relationship_slots_to_ap_regen() -> None:
    """More slots = less AP regen (trade-off)."""
    sizes = get_deck_sizes()
    for i in range(len(sizes) - 1):
        assert sizes[i].slots < sizes[i + 1].slots
        assert sizes[i].ap_regen_bonus > sizes[i + 1].ap_regen_bonus


def test_get_deck_size_names() -> None:
    names = get_deck_size_names()
    assert "light" in names
    assert "standard" in names
    assert "heavy" in names


def test_is_valid_deck_size() -> None:
    assert is_valid_deck_size("light")
    assert is_valid_deck_size("HEAVY")
    assert not is_valid_deck_size("invalid")


def test_get_default_deck_size() -> None:
    assert get_default_deck_size() == "standard"


def test_deck_size_immutable() -> None:
    deck = get_deck_size("light")
    assert deck is not None
    try:
        deck.slots = 99  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_all_sizes_have_negative_cooldown() -> None:
    """Light has shorter cooldowns, heavy has longer."""
    light = get_deck_size("light")
    heavy = get_deck_size("heavy")
    assert light is not None
    assert heavy is not None
    assert light.cooldown_modifier < heavy.cooldown_modifier
