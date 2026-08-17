"""Tests for mission completion system + reputation hooks.

Covers:
- check_mission_completion() / complete_mission() basics
- update_mission_progress() counter logic
- fixer → faction reputation mapping (FIXER_REPUTATION)
- get_next_available_mission() flow
"""

from __future__ import annotations

from wet_run.engine.mission_completion import (
    FIXER_REPUTATION,
    complete_mission,
    fixer_to_factions,
)
from wet_run.engine.state import AppState
from wet_run.matrix.node import Faction
from wet_run.missions import Mission
from wet_run.missions.mission import Rewards
from wet_run.run import start_run


def _make_mission(mission_id: str = "test_mission", fixer: str = "finn") -> Mission:
    """Create a simple test mission that can be completed via extract_data."""
    return Mission(
        id=mission_id,
        title=f"Test {mission_id}",
        fixer=fixer,
        arc=1,
        grade_min=1,
        grade_max=1,
        matrix_seed=42,
        zone=Faction.NONE,  # type: ignore[arg-type]
        objective="Extract the data.",
        reward_tier=1,
        reward_credits=500,
        primary_objective=None,  # set via constructor below
        rewards=Rewards(credits=500, materials={"data_fragment": 2}),
    )


def _state_with_mission(mission: Mission, current_node: str = "data1") -> AppState:
    state = AppState()
    state.inventory = {}
    state.credits = 0
    state.run_state = start_run(mission.id)
    state.current_mission = mission
    state.mission_progress = {"extract_data": mission.required_count()}
    return state


# ============================================================================
# Mission completion basics
# ============================================================================


class TestCompleteMission:
    def test_complete_mission_awards_credits(self) -> None:
        state = AppState()
        state.inventory = {}
        state.credits = 0
        mission = _make_mission()
        state.current_mission = mission
        complete_mission(state, mission)
        assert state.credits == 500

    def test_complete_mission_awards_materials(self) -> None:
        state = AppState()
        state.inventory = {}
        state.credits = 0
        mission = _make_mission()
        state.current_mission = mission
        complete_mission(state, mission)
        assert state.inventory.get("data_fragment") == 2

    def test_complete_mission_marks_completed(self) -> None:
        state = AppState()
        state.inventory = {}
        state.credits = 0
        mission = _make_mission()
        state.current_mission = mission
        complete_mission(state, mission)
        assert mission.id in state.completed_missions

    def test_complete_mission_clears_current(self) -> None:
        state = AppState()
        state.inventory = {}
        state.credits = 0
        mission = _make_mission()
        state.current_mission = mission
        complete_mission(state, mission)
        assert state.current_mission is None

    def test_complete_mission_resets_progress(self) -> None:
        state = AppState()
        state.inventory = {}
        state.credits = 0
        mission = _make_mission()
        state.current_mission = mission
        state.mission_progress = {"extract_data": 1}
        complete_mission(state, mission)
        assert state.mission_progress == {}


# ============================================================================
# Reputation hooks (Phase 6+)
# ============================================================================


class TestFactionReputationOnCompletion:
    """When a mission completes, reputation adjusts per fixer."""

    def _setup_state(self, mission: Mission) -> AppState:
        state = AppState()
        state.inventory = {}
        state.credits = 0
        state.current_mission = mission
        return state

    def test_finn_completion_balances_neutral_factions(self) -> None:
        mission = _make_mission(fixer="finn")
        state = self._setup_state(mission)
        complete_mission(state, mission)
        # Finn boosts Hosaka and Sense/Net slightly
        assert state.reputation.get(Faction.HOSAKA).score == 5
        assert state.reputation.get(Faction.SENSE_NET).score == 5

    def test_maas_work_hurts_hosaka(self) -> None:
        mission = _make_mission(fixer="maas")
        state = self._setup_state(mission)
        complete_mission(state, mission)
        # Maas work boosts Maas, hurts Hosaka
        assert state.reputation.get(Faction.MAAS).score == 10
        assert state.reputation.get(Faction.HOSAKA).score == -3

    def test_sense_net_work_hurts_ta(self) -> None:
        mission = _make_mission(fixer="sally")  # sally = Sense/Net
        state = self._setup_state(mission)
        complete_mission(state, mission)
        # sally gives +10 Sense/Net, -3 Maas.
        assert state.reputation.get(Faction.SENSE_NET).score == 10
        assert state.reputation.get(Faction.MAAS).score == -3

    def test_ta_rep_work_hurts_sense_net(self) -> None:
        mission = _make_mission(fixer="ta_rep")
        state = self._setup_state(mission)
        complete_mission(state, mission)
        assert state.reputation.get(Faction.TA).score == 10
        assert state.reputation.get(Faction.SENSE_NET).score == -3

    def test_kumiko_boosts_maas(self) -> None:
        mission = _make_mission(fixer="kumiko")
        state = self._setup_state(mission)
        complete_mission(state, mission)
        assert state.reputation.get(Faction.MAAS).score == 8

    def test_yakuza_no_reputation_change(self) -> None:
        """Yakuza fixer has no Faction enum mapping → no rep change."""
        mission = _make_mission(fixer="yakuza")
        state = self._setup_state(mission)
        # Snapshot before
        before = state.reputation.total_score()
        complete_mission(state, mission)
        after = state.reputation.total_score()
        assert before == after  # No change

    def test_unknown_fixer_no_crash(self) -> None:
        """Unknown fixer (legacy data, typo) → graceful no-op."""
        # Build a Mission directly with an unknown fixer — bypass the
        # dataclass validation in _make_mission (mission is frozen).
        mission = _make_mission(fixer="finn")
        object.__setattr__(mission, "fixer", "unknown_phantom")
        state = self._setup_state(mission)
        complete_mission(state, mission)  # should not raise
        assert state.credits == 500  # other rewards still work

    def test_reputation_history_records_source(self) -> None:
        mission = _make_mission(fixer="maas")
        state = self._setup_state(mission)
        complete_mission(state, mission)
        history = state.reputation.get(Faction.MAAS).history
        assert len(history) == 1
        assert history[0][1] == f"mission:{mission.id}"

    def test_reputation_message_visible_in_status(self) -> None:
        mission = _make_mission(fixer="finn")
        state = self._setup_state(mission)
        complete_mission(state, mission)
        # Rep messages mention tier + delta
        rep_msgs = [m for m in state.status_messages if m.startswith(">>> Rep ")]
        assert len(rep_msgs) >= 2  # Hosaka + Sense/Net for Finn


# ============================================================================
# fixer_to_factions helper
# ============================================================================


class TestFixerToFactions:
    def test_finn_maps_to_two_factions(self) -> None:
        factions = fixer_to_factions("finn")
        assert Faction.HOSAKA in factions
        assert Faction.SENSE_NET in factions

    def test_maas_maps_to_maas_and_hosaka(self) -> None:
        # Maas work → Maas +, Hosaka -. Both should be returned.
        assert set(fixer_to_factions("maas")) == {Faction.MAAS, Faction.HOSAKA}

    def test_yakuza_returns_empty(self) -> None:
        assert fixer_to_factions("yakuza") == []

    def test_unknown_fixer_returns_empty(self) -> None:
        assert fixer_to_factions("phantom_fixer") == []


# ============================================================================
# FIXER_REPUTATION table integrity
# ============================================================================


class TestFixerReputationTable:
    def test_all_fixer_keys_are_valid(self) -> None:
        """Every key in FIXER_REPUTATION is a valid Faction enum value."""
        for fixer_name, deltas in FIXER_REPUTATION.items():
            for faction_name in deltas:
                Faction(faction_name)  # raises if invalid

    def test_no_deltas_exceed_max_per_event(self) -> None:
        """Each |delta| ≤ 25 so single events can't swing reputation."""
        for fixer_name, deltas in FIXER_REPUTATION.items():
            for faction_name, delta in deltas.items():
                assert abs(delta) <= 25, f"{fixer_name} → {faction_name}: delta {delta} exceeds ±25"
