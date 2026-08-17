"""Tests for the faction reputation system.

Covers:
- FactionReputation.adjust() with clamping + history capping
- reputation_tier() tier mapping
- ReputationState lazy creation + serialization roundtrip
- Edge cases: unknown factions in serialized data, max history
"""

from __future__ import annotations

import pytest

from wet_run.matrix.node import Faction
from wet_run.run.reputation import (
    DEFAULT_REPUTATION,
    MAX_DELTA_PER_EVENT,
    FactionReputation,
    ReputationState,
    clamp_delta,
    reputation_tier,
)

# ============================================================================
# Pure helpers
# ============================================================================


class TestClampDelta:
    def test_under_max_unchanged(self) -> None:
        assert clamp_delta(10) == 10
        assert clamp_delta(-10) == -10
        assert clamp_delta(0) == 0

    def test_positive_clamped_to_max(self) -> None:
        assert clamp_delta(MAX_DELTA_PER_EVENT) == MAX_DELTA_PER_EVENT
        assert clamp_delta(MAX_DELTA_PER_EVENT + 100) == MAX_DELTA_PER_EVENT

    def test_negative_clamped_to_min(self) -> None:
        assert clamp_delta(-MAX_DELTA_PER_EVENT) == -MAX_DELTA_PER_EVENT
        assert clamp_delta(-MAX_DELTA_PER_EVENT - 100) == -MAX_DELTA_PER_EVENT


class TestReputationTier:
    @pytest.mark.parametrize(
        ("score", "expected"),
        [
            (100, "ALLIED"),
            (80, "ALLIED"),
            (79, "FRIENDLY"),
            (50, "FRIENDLY"),
            (49, "TRUSTED"),
            (20, "TRUSTED"),
            (19, "NEUTRAL"),
            (-19, "NEUTRAL"),
            (-20, "HOSTILE"),
            (-49, "HOSTILE"),
            (-50, "ENEMY"),
            (-79, "ENEMY"),
            (-80, "OUTCAST"),
            (-100, "OUTCAST"),
        ],
    )
    def test_tier_mapping(self, score: int, expected: str) -> None:
        assert reputation_tier(score) == expected


# ============================================================================
# FactionReputation
# ============================================================================


class TestFactionReputation:
    def test_default_score_is_zero(self) -> None:
        rep = FactionReputation(faction=Faction.HOSAKA)
        assert rep.score == DEFAULT_REPUTATION
        assert rep.history == []

    def test_default_tier_is_neutral(self) -> None:
        assert FactionReputation(faction=Faction.HOSAKA).tier() == "NEUTRAL"

    def test_adjust_increases_score(self) -> None:
        rep = FactionReputation(faction=Faction.HOSAKA)
        rep.adjust(20, source="mission:ta_heist")
        assert rep.score == 20
        assert rep.tier() == "TRUSTED"

    def test_adjust_records_history(self) -> None:
        rep = FactionReputation(faction=Faction.HOSAKA)
        rep.adjust(10, source="mission:a")
        rep.adjust(-5, source="combat:death")
        assert rep.history[0] == (-5, "combat:death")  # newest first
        assert rep.history[1] == (10, "mission:a")

    def test_adjust_clamps_overflow(self) -> None:
        rep = FactionReputation(faction=Faction.HOSAKA)
        rep.adjust(100, source="big")
        assert rep.score == MAX_DELTA_PER_EVENT  # clamped, not 100

    def test_history_capped(self) -> None:
        rep = FactionReputation(faction=Faction.HOSAKA)
        for i in range(FactionReputation.HISTORY_MAX + 10):
            rep.adjust(1, source=f"e{i}")
        assert len(rep.history) == FactionReputation.HISTORY_MAX
        # Newest at index 0
        assert rep.history[0][1] == f"e{FactionReputation.HISTORY_MAX + 9}"

    def test_negative_score_works(self) -> None:
        rep = FactionReputation(faction=Faction.MAAS)
        rep.adjust(-25, source="combat:black_ice")
        assert rep.score == -25
        assert rep.tier() == "HOSTILE"


# ============================================================================
# ReputationState
# ============================================================================


class TestReputationState:
    def test_empty_state(self) -> None:
        state = ReputationState()
        assert state.all_factions() == []
        assert state.total_score() == 0

    def test_lazy_creation_on_get(self) -> None:
        state = ReputationState()
        rep = state.get(Faction.TA)
        assert rep.faction is Faction.TA
        assert state.all_factions() == [Faction.TA]

    def test_get_returns_same_instance(self) -> None:
        state = ReputationState()
        a = state.get(Faction.SENSE_NET)
        b = state.get(Faction.SENSE_NET)
        assert a is b

    def test_adjust_shorthand(self) -> None:
        state = ReputationState()
        state.adjust(Faction.HOSAKA, 10, source="mission")
        assert state.get(Faction.HOSAKA).score == 10

    def test_total_score_sums(self) -> None:
        state = ReputationState()
        state.adjust(Faction.HOSAKA, 10)
        state.adjust(Faction.MAAS, -5)
        state.adjust(Faction.SENSE_NET, 20)
        assert state.total_score() == 25

    def test_adjust_clamps(self) -> None:
        state = ReputationState()
        state.adjust(Faction.HOSAKA, 999)  # way over MAX
        assert state.get(Faction.HOSAKA).score == MAX_DELTA_PER_EVENT


# ============================================================================
# Serialization
# ============================================================================


class TestSerialization:
    def test_to_dict_empty(self) -> None:
        state = ReputationState()
        d = state.to_dict()
        assert d == {"reputations": {}}

    def test_roundtrip(self) -> None:
        original = ReputationState()
        original.adjust(Faction.HOSAKA, 25, source="mission:ta_heist")
        original.adjust(Faction.TA, -10, source="combat:black_ice")

        d = original.to_dict()
        restored = ReputationState.from_dict(d)

        assert restored.get(Faction.HOSAKA).score == 25
        assert restored.get(Faction.HOSAKA).history[0] == (25, "mission:ta_heist")
        assert restored.get(Faction.TA).score == -10

    def test_unknown_faction_skipped(self) -> None:
        """Legacy save with an unrecognized faction value should not crash."""
        d = {
            "reputations": {
                "hosaka": {"score": 10, "history": []},
                "unknown_corp": {"score": 99, "history": []},
            }
        }
        restored = ReputationState.from_dict(d)
        assert restored.get(Faction.HOSAKA).score == 10
        # The unknown faction was silently skipped.
        assert len(restored.all_factions()) == 1

    def test_invalid_score_falls_back_to_zero(self) -> None:
        d = {
            "reputations": {
                "hosaka": {"score": "not_a_number", "history": []},
            }
        }
        restored = ReputationState.from_dict(d)
        assert restored.get(Faction.HOSAKA).score == 0

    def test_missing_reputations_key(self) -> None:
        """Empty save / legacy save → empty ReputationState."""
        restored = ReputationState.from_dict({})
        assert restored.all_factions() == []

    def test_malformed_history_entries_skipped(self) -> None:
        """Bad history entries (wrong shape, unparseable) are dropped."""
        d = {
            "reputations": {
                "hosaka": {
                    "score": 10,
                    "history": [
                        (5, "good"),
                        "not_a_tuple",
                        (3,),  # wrong length
                        ("x", "bad_delta"),  # non-int delta
                        (-2, "good_negative"),
                    ],
                }
            }
        }
        restored = ReputationState.from_dict(d)
        history = restored.get(Faction.HOSAKA).history
        # Only the two well-formed entries survive.
        assert (5, "good") in history
        assert (-2, "good_negative") in history
        assert len(history) == 2

    def test_non_dict_payload_ignored(self) -> None:
        """Top-level non-dict → empty state (no crash)."""
        restored = ReputationState.from_dict("not a dict")  # type: ignore[arg-type]
        assert restored.all_factions() == []
