"""Tests for construct_whisper_hook (ADR-0140 §Proposal 1 combat integration)."""

from __future__ import annotations

from dataclasses import dataclass, field

from wet_run.lore import (
    ConstructWhisper,
    check_construct_whisper_on_combat_start,
)
from wet_run.matrix.node import Faction
from wet_run.run.reputation import ReputationState


@dataclass
class _FakeState:
    """Minimal AppState stub with required lore integration fields."""

    reputation: ReputationState = field(default_factory=ReputationState)
    construct_whisper_tracker: ConstructWhisper = field(default_factory=ConstructWhisper)
    status_messages: list[str] = field(default_factory=list)


class TestCheckConstructWhisperOnCombatStart:
    """Combat hook integration — faction-tier-gated whispers."""

    def test_no_eligible_no_messages(self) -> None:
        state = _FakeState()
        delivered = check_construct_whisper_on_combat_start(state)
        assert delivered == []
        assert state.status_messages == []

    def test_trusted_triggers_one_whisper(self) -> None:
        state = _FakeState()
        state.reputation.adjust(Faction.HOSAKA, 25, source="test")
        delivered = check_construct_whisper_on_combat_start(state)
        assert len(delivered) == 1
        assert "HOSAKA" in delivered[0].upper()
        assert state.construct_whisper_tracker.has_whispered(Faction.HOSAKA)
        assert len(state.status_messages) == 1

    def test_friendly_triggers_whisper(self) -> None:
        state = _FakeState()
        state.reputation.adjust(Faction.MAAS, 55, source="test")
        delivered = check_construct_whisper_on_combat_start(state)
        assert len(delivered) == 1
        assert "MAAS" in delivered[0].upper()

    def test_multiple_factions_trigger_multiple(self) -> None:
        state = _FakeState()
        state.reputation.adjust(Faction.HOSAKA, 25, source="t1")
        state.reputation.adjust(Faction.MAAS, 25, source="t2")
        state.reputation.adjust(Faction.TA, 25, source="t3")
        delivered = check_construct_whisper_on_combat_start(state)
        assert len(delivered) == 3
        assert state.construct_whisper_tracker.count == 3

    def test_already_whispered_not_re_delivered(self) -> None:
        state = _FakeState()
        state.reputation.adjust(Faction.HOSAKA, 25, source="t")
        first = check_construct_whisper_on_combat_start(state)
        second = check_construct_whisper_on_combat_start(state)
        assert len(first) == 1
        assert second == []
        assert len(state.status_messages) == 1

    def test_hostile_faction_excluded(self) -> None:
        state = _FakeState()
        state.reputation.adjust(Faction.HOSAKA, -25, source="t")
        delivered = check_construct_whisper_on_combat_start(state)
        assert delivered == []

    def test_missing_state_attributes_returns_empty(self) -> None:
        """Defensive: state without reputation/tracker doesn't crash."""
        state = _FakeState.__new__(_FakeState)
        # Skip __init__ so attributes aren't set
        state.reputation = None  # type: ignore[assignment]
        state.construct_whisper_tracker = None  # type: ignore[assignment]
        state.status_messages = []
        delivered = check_construct_whisper_on_combat_start(state)
        assert delivered == []

    def test_cap_enforced_across_factions(self) -> None:
        state = _FakeState()
        state.construct_whisper_tracker.max_total = 2
        state.reputation.adjust(Faction.HOSAKA, 25, source="t1")
        state.reputation.adjust(Faction.MAAS, 25, source="t2")
        state.reputation.adjust(Faction.TA, 25, source="t3")
        delivered = check_construct_whisper_on_combat_start(state)
        assert len(delivered) == 2
        assert state.construct_whisper_tracker.count == 2
