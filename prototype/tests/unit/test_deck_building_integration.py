"""Tests for Deck Building integration (ADR-0178, Round 4)."""

from __future__ import annotations

from roguelike_sprawl.combat.deck_building import (
    get_deck_size,
    get_deck_size_names,
    get_default_deck_size,
    is_valid_deck_size,
)
from roguelike_sprawl.engine.state import AppState


class TestDeckSizeIntegration:
    """AppState deck_size integrates with deck_building module."""

    def test_default_deck_size_is_standard(self) -> None:
        state = AppState()
        assert state.deck_size == "standard"
        assert is_valid_deck_size(state.deck_size)

    def test_deck_size_validates_against_module(self) -> None:
        for name in get_deck_size_names():
            state = AppState(deck_size=name)
            assert is_valid_deck_size(state.deck_size)

    def test_deck_size_invalid_accepted_at_construction(self) -> None:
        # Dataclasses don't validate string types at construction.
        # Validation happens at module level via is_valid_deck_size().
        state = AppState(deck_size="unknown")
        assert state.deck_size == "unknown"
        assert not is_valid_deck_size(state.deck_size)

    def test_deck_size_passed_to_module(self) -> None:
        state = AppState(deck_size="light")
        ds = get_deck_size(state.deck_size)
        assert ds is not None
        assert ds.name == "LIGHT"
        assert ds.slots == 6

    def test_deck_size_heavy(self) -> None:
        state = AppState(deck_size="heavy")
        ds = get_deck_size(state.deck_size)
        assert ds is not None
        assert ds.name == "HEAVY"
        assert ds.slots == 10

    def test_deck_size_standard(self) -> None:
        state = AppState(deck_size="standard")
        ds = get_deck_size(state.deck_size)
        assert ds is not None
        assert ds.name == "STANDARD"
        assert ds.slots == 8

    def test_default_deck_size_matches_module(self) -> None:
        state = AppState()
        assert state.deck_size == get_default_deck_size()


class TestDeckSizeStats:
    """Verify deck size stats for game tuning."""

    def test_light_ap_regen_bonus(self) -> None:
        ds = get_deck_size("light")
        assert ds.ap_regen_bonus == 0.5

    def test_heavy_cooldown_modifier(self) -> None:
        ds = get_deck_size("heavy")
        assert ds.cooldown_modifier == 0.15

    def test_standard_balanced(self) -> None:
        ds = get_deck_size("standard")
        assert ds.ap_regen_bonus == 0.0
        assert ds.cooldown_modifier == 0.0


class TestDeckSizePersistence:
    """Test that deck_size persists across operations."""

    def test_deck_size_change_preserves_other_state(self) -> None:
        state = AppState(credits=500, player_grade=3)
        state.deck_size = "heavy"
        assert state.credits == 500
        assert state.player_grade == 3
        assert state.deck_size == "heavy"

    def test_deck_size_after_default_loadout(self) -> None:
        state = AppState()
        original_loadout = state.player_loadout
        state.deck_size = "light"
        assert state.player_loadout == original_loadout
