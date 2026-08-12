"""Tests for Meta-Progression (ADR-0174)."""

from __future__ import annotations

import dataclasses

import pytest

from roguelike_sprawl.combat.meta_progression import (
    META_UNLOCKS,
    MetaUnlock,
    check_unlock_condition,
    get_locked_ids,
    get_meta_progress,
    get_meta_unlocks,
    get_unlock_progress_ratio,
    get_unlocked_ids,
    get_unlocks_by_category,
    record_meta_progress,
)


def test_registry_has_unlocks() -> None:
    assert len(META_UNLOCKS) >= 10


def test_get_meta_unlocks() -> None:
    unlocks = get_meta_unlocks()
    assert len(unlocks) >= 10
    assert all(isinstance(u, MetaUnlock) for u in unlocks)


def test_get_meta_progress_existing() -> None:
    unlock = get_meta_progress("ghost_deck")
    assert unlock is not None
    assert unlock.id == "ghost_deck"


def test_get_meta_progress_nonexistent() -> None:
    assert get_meta_progress("nonexistent") is None


def test_record_meta_progress() -> None:
    unlock = get_meta_progress("ghost_deck")
    assert unlock is not None
    original = unlock.progress
    record_meta_progress("ghost_deck", 1)
    updated = get_meta_progress("ghost_deck")
    assert updated is not None
    assert updated.progress == original + 1


def test_record_meta_progress_nonexistent() -> None:
    with pytest.raises(ValueError, match="Unknown unlock"):
        record_meta_progress("nonexistent")


def test_get_unlocks_by_category() -> None:
    decks = get_unlocks_by_category("deck")
    assert len(decks) >= 3
    assert all(u.category == "deck" for u in decks)


def test_unlocked_and_locked_partition() -> None:
    unlocked = get_unlocked_ids()
    locked = get_locked_ids()
    assert unlocked.isdisjoint(locked)
    assert len(unlocked) + len(locked) == len(META_UNLOCKS)


def test_check_unlock_condition_present() -> None:
    assert check_unlock_condition("win_5_stealth_runs", {"win_5_stealth_runs": 1})


def test_check_unlock_condition_absent() -> None:
    assert not check_unlock_condition("win_5_stealth_runs", {})


def test_get_progress_ratio_complete() -> None:
    unlock = get_meta_progress("ghost_deck")
    assert unlock is not None
    record_meta_progress("ghost_deck", 100)
    ratio = get_unlock_progress_ratio("ghost_deck")
    assert ratio == 1.0


def test_get_progress_ratio_partial() -> None:
    unlock = get_meta_progress("ta_skin")
    assert unlock is not None
    ratio = get_unlock_progress_ratio("ta_skin")
    assert 0.0 <= ratio <= 1.0


def test_get_progress_ratio_nonexistent() -> None:
    assert get_unlock_progress_ratio("nonexistent") == 0.0


def test_unlocks_immutable() -> None:
    unlock = get_meta_progress("neuromancer_unlock")
    assert unlock is not None
    try:
        unlock.name = "Modified"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_all_categories_present() -> None:
    categories = {u.category for u in META_UNLOCKS.values()}
    assert "program" in categories
    assert "augment" in categories
    assert "deck" in categories
    assert "cosmetic" in categories


def test_record_progress_then_check() -> None:
    # ghost_deck requires 5 stealth wins
    record_meta_progress("ghost_deck", 3)
    assert not check_unlock_condition("win_5_stealth_runs", {"win_5_stealth_runs": 0})
    # After 5 wins, unlock triggers
    assert check_unlock_condition("win_5_stealth_runs", {"win_5_stealth_runs": 5})
