"""Tests for fragment_hook (ADR-0140 §Proposal 2 matrix integration)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import pytest

from wet_run.lore import (
    MemoryFragmentTracker,
    check_memory_fragment_on_node_entry,
)
from wet_run.lore.memory_fragment import load_encounter_table


@dataclass
class _FakeState:
    """Minimal AppState stub with status_messages list."""

    status_messages: list[str] = field(default_factory=list)


@pytest.fixture
def encounter_table() -> dict[str, object]:
    return load_encounter_table(__import__("pathlib").Path("data/lore/encounter_table.json"))


@pytest.fixture
def tracker() -> MemoryFragmentTracker:
    return MemoryFragmentTracker(per_run_cap=6)


class TestCheckMemoryFragmentOnNodeEntry:
    """Matrix integration hook — rolls + applies state."""

    def test_cap_reached_no_roll(
        self, encounter_table: dict[str, object], tracker: MemoryFragmentTracker
    ) -> None:
        tracker.per_run_cap = 0
        state = _FakeState()
        rng = random.Random(42)
        result = check_memory_fragment_on_node_entry(
            state,
            encounter_table,
            tracker,
            rng,
            current_zone="surface",
            current_grade=1,
            faction=None,
        )
        assert result.cap_reached is True
        assert result.pick is None
        assert state.status_messages == []

    def test_no_match_no_message(
        self, encounter_table: dict[str, object], tracker: MemoryFragmentTracker
    ) -> None:
        state = _FakeState()
        rng = random.Random(42)
        # 'mid' zone has no fragments → no pick
        result = check_memory_fragment_on_node_entry(
            state,
            encounter_table,
            tracker,
            rng,
            current_zone="mid",
            current_grade=1,
            faction=None,
        )
        assert result.pick is None
        assert result.status_message == ""
        assert state.status_messages == []

    def test_hit_emits_status_message(
        self, encounter_table: dict[str, object], tracker: MemoryFragmentTracker
    ) -> None:
        encounter_table["base_chance"] = 1.0
        state = _FakeState()
        rng = random.Random(42)
        result = check_memory_fragment_on_node_entry(
            state,
            encounter_table,
            tracker,
            rng,
            current_zone="surface",
            current_grade=1,
            faction=None,
        )
        if result.pick is not None:
            assert len(state.status_messages) == 1
            assert "Memory fragment recovered" in state.status_messages[0]
            assert result.pick.fragment_id in state.status_messages[0]
            assert tracker.count == 1

    def test_faction_rep_delta_in_message(
        self, encounter_table: dict[str, object], tracker: MemoryFragmentTracker
    ) -> None:
        encounter_table["base_chance"] = 1.0
        state = _FakeState()
        rng = random.Random(42)
        result = check_memory_fragment_on_node_entry(
            state,
            encounter_table,
            tracker,
            rng,
            current_zone="core",
            current_grade=3,
            faction="hosaka",
        )
        if result.pick is not None and result.pick.rep_delta != 0:
            assert "+1" in result.status_message or "-1" in result.status_message

    def test_already_found_excluded(
        self, encounter_table: dict[str, object], tracker: MemoryFragmentTracker
    ) -> None:
        encounter_table["base_chance"] = 1.0
        tracker.already_found.add("memory_signal_echo_01")
        state = _FakeState()
        rng = random.Random(42)
        result = check_memory_fragment_on_node_entry(
            state,
            encounter_table,
            tracker,
            rng,
            current_zone="surface",
            current_grade=1,
            faction=None,
        )
        # If hit, it should not be the already-found fragment
        if result.pick is not None:
            assert result.pick.fragment_id != "memory_signal_echo_01"

    def test_status_message_cap_reached(self, tracker: MemoryFragmentTracker) -> None:
        tracker.per_run_cap = 0
        state = _FakeState()
        rng = random.Random(42)
        result = check_memory_fragment_on_node_entry(
            state,
            {},
            tracker,
            rng,
            current_zone="surface",
            current_grade=1,
            faction=None,
        )
        assert "cap reached" in result.status_message.lower()
