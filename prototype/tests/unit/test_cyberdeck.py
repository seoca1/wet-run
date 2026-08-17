"""Tests for Cyberdeck Customization (ADR-0172)."""

from __future__ import annotations

import dataclasses

import pytest

from wet_run.combat.cyberdeck import (
    DEFAULT_DECK_SLOTS,
    MAX_DECK_NAME_LENGTH,
    Cyberdeck,
    add_program_to_deck,
    create_deck,
    get_deck_program_count,
    get_deck_slots_remaining,
    has_program,
    remove_program_from_deck,
    validate_deck,
)


def test_create_deck_empty() -> None:
    deck = create_deck("My Deck")
    assert deck.name == "My Deck"
    assert deck.program_ids == ()
    assert deck.passive_bonus == {}


def test_create_deck_with_programs() -> None:
    deck = create_deck("Stealth", ["probe", "detect", "shield"])
    assert deck.program_ids == ("probe", "detect", "shield")


def test_create_deck_name_too_long() -> None:
    with pytest.raises(ValueError, match="too long"):
        create_deck("x" * (MAX_DECK_NAME_LENGTH + 1))


def test_validate_deck_empty() -> None:
    deck = create_deck("Empty")
    assert validate_deck(deck)


def test_validate_deck_full() -> None:
    deck = create_deck("Full", [f"prog_{i}" for i in range(8)])
    assert validate_deck(deck, max_slots=8)


def test_validate_deck_too_many() -> None:
    deck = create_deck("Overfull", [f"prog_{i}" for i in range(9)])
    assert not validate_deck(deck, max_slots=8)


def test_validate_deck_duplicates() -> None:
    deck = Cyberdeck(name="Dupes", program_ids=("probe", "probe"))
    assert not validate_deck(deck)


def test_add_program_to_deck() -> None:
    deck = create_deck("Build")
    deck = add_program_to_deck(deck, "probe")
    deck = add_program_to_deck(deck, "shield")
    assert deck.program_ids == ("probe", "shield")
    assert get_deck_program_count(deck) == 2


def test_add_program_full_deck() -> None:
    deck = create_deck("Full", [f"prog_{i}" for i in range(8)])
    with pytest.raises(ValueError, match="full"):
        add_program_to_deck(deck, "extra")


def test_add_program_duplicate() -> None:
    deck = create_deck("Dup", ["probe"])
    with pytest.raises(ValueError, match="already in deck"):
        add_program_to_deck(deck, "probe")


def test_remove_program_from_deck() -> None:
    deck = create_deck("Build", ["probe", "shield", "detect"])
    deck = remove_program_from_deck(deck, "shield")
    assert deck.program_ids == ("probe", "detect")


def test_remove_program_not_in_deck() -> None:
    deck = create_deck("Build", ["probe"])
    with pytest.raises(ValueError, match="not in deck"):
        remove_program_from_deck(deck, "missing")


def test_get_deck_program_count() -> None:
    deck = create_deck("5", ["a", "b", "c", "d", "e"])
    assert get_deck_program_count(deck) == 5


def test_get_deck_slots_remaining() -> None:
    deck = create_deck("3", ["a", "b", "c"])
    assert get_deck_slots_remaining(deck) == 5
    assert get_deck_slots_remaining(deck, max_slots=4) == 1


def test_has_program() -> None:
    deck = create_deck("Has", ["probe", "shield"])
    assert has_program(deck, "probe")
    assert has_program(deck, "shield")
    assert not has_program(deck, "missing")


def test_deck_is_immutable() -> None:
    deck = create_deck("Deck", ["probe"])
    try:
        deck.name = "New Name"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_add_remove_preserves_other_fields() -> None:
    deck = Cyberdeck(
        name="Test",
        program_ids=("probe",),
        passive_bonus={"crit": 5},
    )
    deck = add_program_to_deck(deck, "shield")
    assert deck.passive_bonus == {"crit": 5}
    deck = remove_program_from_deck(deck, "probe")
    assert deck.passive_bonus == {"crit": 5}
    assert deck.program_ids == ("shield",)


def test_default_deck_slots_constant() -> None:
    assert DEFAULT_DECK_SLOTS == 8
