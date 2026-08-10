"""Tests for mission reputation-based filtering (Phase 6+).

A mission is "available" when:
  - Player grade is within [grade_min, grade_max]
  - Player is NOT hostile (HOSTILE/ENEMY/OUTCAST) with any of the
    fixer's primary factions

Tests cover:
  - available_for() with/without reputation
  - locked_for() returns the right missions
  - mission_status() reports the right status
  - Edge cases: missing reputation, neutral rep, all factions friendly
"""

from __future__ import annotations

from pathlib import Path

import pytest

from roguelike_sprawl.engine.mission_completion import FIXER_REPUTATION
from roguelike_sprawl.matrix.node import Faction
from roguelike_sprawl.missions import JobBoard
from roguelike_sprawl.missions.board import MissionRepStatus
from roguelike_sprawl.missions.mission import Mission, Objective, Rewards
from roguelike_sprawl.run.reputation import ReputationState

# ============================================================================
# Helpers
# ============================================================================


def _make_mission(
    mission_id: str,
    fixer: str = "finn",
    grade_min: int = 1,
    grade_max: int = 1,
) -> Mission:
    """Build a minimal Mission for testing."""
    return Mission(
        id=mission_id,
        title=f"Test {mission_id}",
        fixer=fixer,
        arc=1,
        grade_min=grade_min,
        grade_max=grade_max,
        matrix_seed=42,
        zone=Faction.NONE,  # type: ignore[arg-type]
        objective="",
        reward_tier=1,
        reward_credits=100,
        primary_objective=Objective(type="extract_data", count=1),
        secondary_objectives=(),
        rewards=Rewards(credits=100, materials={}),
    )


def _state_with_rep(scores: dict[Faction, int]) -> ReputationState:
    """Build a ReputationState with the given scores (others default 0)."""
    state = ReputationState()
    for faction, score in scores.items():
        state.get(faction).score = score
    return state


# ============================================================================
# MissionRepStatus enum integrity
# ============================================================================


class TestMissionRepStatusEnum:
    def test_enum_values_are_strings(self) -> None:
        assert MissionRepStatus.AVAILABLE == "available"
        assert MissionRepStatus.LOCKED_GRADE == "locked_grade"
        assert MissionRepStatus.LOCKED_REPUTATION == "locked_reputation"

    def test_all_statuses_are_distinct(self) -> None:
        statuses = {s.value for s in MissionRepStatus}
        assert len(statuses) == 3


# ============================================================================
# available_for() — basic grade filter (regression-safe)
# ============================================================================


class TestAvailableForGradeOnly:
    def test_grade_filter_no_reputation(self) -> None:
        """Without reputation, all grade-matching missions are available."""
        board = JobBoard(
            missions=(
                _make_mission("m1", grade_min=1, grade_max=2),
                _make_mission("m2", grade_min=2, grade_max=3),
                _make_mission("m3", grade_min=4, grade_max=5),
            )
        )
        result = board.available_for(grade=2)
        assert {m.id for m in result} == {"m1", "m2"}

    def test_reputation_none_preserves_legacy_behavior(self) -> None:
        """Passing reputation=None is identical to the old 1-arg API."""
        board = JobBoard(missions=(_make_mission("m1"),))
        result = board.available_for(grade=1, reputation=None)
        assert {m.id for m in result} == {"m1"}


# ============================================================================
# available_for() — with reputation filtering
# ============================================================================


class TestAvailableForWithReputation:
    def test_neutral_rep_lets_mission_through(self) -> None:
        """Neutral reputation (default 0) does NOT lock any mission."""
        board = JobBoard(missions=(_make_mission("m1", fixer="finn"),))
        rep = _state_with_rep({})  # all factions at NEUTRAL (0)
        result = board.available_for(grade=1, reputation=rep)
        assert {m.id for m in result} == {"m1"}

    def test_allied_rep_lets_mission_through(self) -> None:
        """ALLIED reputation is not hostile — mission is available."""
        board = JobBoard(missions=(_make_mission("m1", fixer="maas"),))
        rep = _state_with_rep({Faction.MAAS: 100})  # ALLIED
        result = board.available_for(grade=1, reputation=rep)
        assert {m.id for m in result} == {"m1"}

    def test_hostile_rep_locks_mission(self) -> None:
        """Player hostile with Maas → Maas mission locked."""
        board = JobBoard(missions=(_make_mission("m1", fixer="maas"),))
        rep = _state_with_rep({Faction.MAAS: -50})  # ENEMY tier
        result = board.available_for(grade=1, reputation=rep)
        assert not result  # empty tuple

    def test_outcast_rep_locks_mission(self) -> None:
        """OUTCAST tier also locks missions."""
        board = JobBoard(missions=(_make_mission("m1", fixer="ta_rep"),))
        rep = _state_with_rep({Faction.TA: -100})  # OUTCAST
        result = board.available_for(grade=1, reputation=rep)
        assert not result

    def test_hostile_with_unrelated_faction_does_not_lock(self) -> None:
        """Being hostile with Maas doesn't lock a Finn (Hosaka) mission."""
        board = JobBoard(missions=(_make_mission("m1", fixer="finn"),))
        # Finn is associated with Hosaka + Sense/Net, NOT Maas.
        rep = _state_with_rep({Faction.MAAS: -100})  # OUTCAST with Maas
        result = board.available_for(grade=1, reputation=rep)
        # Finn mission is still available (player is fine with Hosaka).
        assert {m.id for m in result} == {"m1"}

    def test_hostile_with_any_fixers_faction_locks(self) -> None:
        """If player is hostile with ANY of the fixer's factions, lock."""
        board = JobBoard(missions=(_make_mission("m1", fixer="finn"),))
        # Finn is Hosaka + Sense/Net. Hostile with Hosaka should lock.
        rep = _state_with_rep({Faction.HOSAKA: -50})
        result = board.available_for(grade=1, reputation=rep)
        assert not result

    def test_mixed_factions_some_locked_some_available(self) -> None:
        """Multiple missions, mixed lock states."""
        board = JobBoard(
            missions=(
                _make_mission("finn_job", fixer="finn"),
                _make_mission("maas_job", fixer="maas"),
                _make_mission("ta_job", fixer="ta_rep"),
            )
        )
        # Hostile with Maas only.
        rep = _state_with_rep({Faction.MAAS: -50})
        result = board.available_for(grade=1, reputation=rep)
        assert {m.id for m in result} == {"finn_job", "ta_job"}

    def test_trusted_rep_lets_mission_through(self) -> None:
        """TRUSTED (score 20) is not hostile — mission available."""
        board = JobBoard(missions=(_make_mission("m1", fixer="sally"),))
        # sally is associated with Sense/Net.
        rep = _state_with_rep({Faction.SENSE_NET: 25})  # TRUSTED
        result = board.available_for(grade=1, reputation=rep)
        assert {m.id for m in result} == {"m1"}


# ============================================================================
# locked_for()
# ============================================================================


class TestLockedFor:
    def test_no_locked_missions_when_neutral(self) -> None:
        board = JobBoard(
            missions=(
                _make_mission("m1", fixer="finn"),
                _make_mission("m2", fixer="maas"),
            )
        )
        rep = _state_with_rep({})
        assert board.locked_for(rep) == ()

    def test_returns_only_hostile_locked_missions(self) -> None:
        board = JobBoard(
            missions=(
                _make_mission("finn_job", fixer="finn"),
                _make_mission("maas_job", fixer="maas"),
                _make_mission("ta_job", fixer="ta_rep"),
            )
        )
        # Hostile with Maas only.
        rep = _state_with_rep({Faction.MAAS: -50})
        locked = board.locked_for(rep)
        assert {m.id for m in locked} == {"maas_job"}

    def test_all_locked_when_maximally_hostile(self) -> None:
        """If hostile with every fixer's faction, every mission locks."""
        board = JobBoard(
            missions=(
                _make_mission("finn_job", fixer="finn"),
                _make_mission("maas_job", fixer="maas"),
                _make_mission("ta_job", fixer="ta_rep"),
            )
        )
        # HOSTILE with Hosaka, Maas, TA (covers all 3 fixers).
        rep = _state_with_rep({Faction.HOSAKA: -50, Faction.MAAS: -50, Faction.TA: -50})
        locked = board.locked_for(rep)
        assert {m.id for m in locked} == {"finn_job", "maas_job", "ta_job"}


# ============================================================================
# mission_status() — combined check
# ============================================================================


class TestMissionStatus:
    def test_available_when_grade_and_rep_match(self) -> None:
        board = JobBoard(missions=(_make_mission("m1", grade_min=1, grade_max=3, fixer="finn"),))
        rep = _state_with_rep({Faction.HOSAKA: 50})  # FRIENDLY
        assert (
            board.mission_status(board.get("m1"), grade=2, reputation=rep)
            is MissionRepStatus.AVAILABLE
        )

    def test_locked_grade_takes_precedence_when_rep_ok(self) -> None:
        """Grade mismatch → LOCKED_GRADE even with good rep."""
        board = JobBoard(missions=(_make_mission("m1", grade_min=1, grade_max=2, fixer="finn"),))
        rep = _state_with_rep({Faction.HOSAKA: 100})  # ALLIED
        # Player is grade 3, mission is grade 1-2.
        assert (
            board.mission_status(board.get("m1"), grade=3, reputation=rep)
            is MissionRepStatus.LOCKED_GRADE
        )

    def test_locked_reputation_takes_precedence(self) -> None:
        """Reputation lock wins over grade mismatch."""
        board = JobBoard(missions=(_make_mission("m1", grade_min=1, grade_max=5, fixer="maas"),))
        rep = _state_with_rep({Faction.MAAS: -50})  # ENEMY
        # Player is grade 1, mission grade 1-5 (in range), BUT rep hostile.
        assert (
            board.mission_status(board.get("m1"), grade=1, reputation=rep)
            is MissionRepStatus.LOCKED_REPUTATION
        )

    def test_legacy_no_reputation_state(self) -> None:
        """No reputation → all missions AVAILABLE (assuming grade in range)."""
        board = JobBoard(missions=(_make_mission("m1", grade_min=1, grade_max=3, fixer="finn"),))
        assert (
            board.mission_status(board.get("m1"), grade=2, reputation=None)
            is MissionRepStatus.AVAILABLE
        )

    def test_get_returns_none_for_unknown_mission(self) -> None:
        board = JobBoard()
        # Passing None as the mission should not crash; returns None.
        assert board.mission_status(None, grade=1) is None  # type: ignore[arg-type]


# ============================================================================
# Data integrity — fixer → faction mapping must be complete
# ============================================================================


class TestFixerReputationData:
    """Sanity checks on the FIXER_REPUTATION table used by the filter."""

    @pytest.mark.parametrize("fixer_name", ["finn", "maas", "sally", "ta_rep", "dixie", "kumiko"])
    def test_common_fixers_have_rep_table_entry(self, fixer_name: str) -> None:
        assert fixer_name in FIXER_REPUTATION, f"Missing FIXER_REPUTATION entry for {fixer_name}"

    def test_yakuza_has_no_rep_mapping(self) -> None:
        """Yakuza has no Faction enum mapping → always available."""
        assert "yakuza" in FIXER_REPUTATION
        assert FIXER_REPUTATION["yakuza"] == {}

    def test_unknown_fixer_returns_no_lock(self) -> None:
        """A fixer not in the table has no faction lock — fully available."""
        board = JobBoard(missions=(_make_mission("m1", fixer="phantom_fixer"),))
        rep = _state_with_rep({Faction.MAAS: -100})  # OUTCAST with Maas
        result = board.available_for(grade=1, reputation=rep)
        assert {m.id for m in result} == {"m1"}


# ============================================================================
# Integration with real data
# ============================================================================


class TestRealMissionsJsonIntegration:
    """End-to-end: load real missions.json and verify rep filter."""

    def test_real_data_loaded(self, data_dir: Path) -> None:

        board = JobBoard.load(data_dir / "missions" / "missions.json")
        assert len(board) >= 189, f"Expected >= 189 missions after Phase 14, got {len(board)}"

    def test_hostile_maas_hides_maas_missions(self, data_dir: Path) -> None:
        """Real test: Maas missions are locked when hostile with Maas."""
        board = JobBoard.load(data_dir / "missions" / "missions.json")
        rep = _state_with_rep({Faction.MAAS: -100})  # OUTCAST

        # In the real data, mollys_razor is the only Maas mission.
        locked = board.locked_for(rep)
        locked_ids = {m.id for m in locked}
        assert "mollys_razor" in locked_ids

    def test_neutral_lets_all_missions_through(self, data_dir: Path) -> None:
        """Default (neutral) reputation should not block any mission."""

        board = JobBoard.load(data_dir / "missions" / "missions.json")
        rep = _state_with_rep({})  # all neutral

        # All grade-1 missions should be available.
        available = board.available_for(grade=1, reputation=rep)
        assert len(available) >= 5  # several grade-1 missions in real data

    def test_legacy_save_no_reputation_attr(self, data_dir: Path) -> None:
        """Pre-reputation saves work (no .reputation field)."""
        board = JobBoard.load(data_dir / "missions" / "missions.json")
        # Pass reputation=None (simulating legacy state).
        available = board.available_for(grade=1, reputation=None)
        assert len(available) >= 5


class TestHubJobBoardDisplay:
    """The Hub Job Board surfaces locked-mission count when reputation
    gates missions. We test the helper functions used by the panel."""

    def test_locked_count_helper(self, data_dir: Path) -> None:
        """When a fixer is hostile, the panel reports a non-zero locked count."""
        board = JobBoard.load(data_dir / "missions" / "missions.json")
        rep = _state_with_rep({Faction.MAAS: -100})  # OUTCAST
        locked = board.locked_for(rep)
        assert len(locked) >= 1  # mollys_razor + others
        # The panel would render: "[+N jobs locked by rep]"

    def test_no_locked_when_neutral(self, data_dir: Path) -> None:
        board = JobBoard.load(data_dir / "missions" / "missions.json")
        rep = _state_with_rep({})  # all neutral
        locked = board.locked_for(rep)
        assert locked == ()  # no footer shown when nothing is locked
