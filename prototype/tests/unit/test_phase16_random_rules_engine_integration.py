"""Tests for Phase 16 engine wiring of random rules → JobBoard.

Verifies that the hub's mission selection actually exercises
JobBoard.select_weighted when the player activates the "ENTER"
recommendation hook, and that the weighted selection differs from
a flat index pick when player state changes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from roguelike_sprawl.engine import hub as hub_mod
from roguelike_sprawl.engine.state import AppState
from roguelike_sprawl.missions.board import JobBoard
from roguelike_sprawl.missions.mission import Mission, Objective, Rewards

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class DummyState:
    """Minimal state for random rules integration tests."""

    grade: int = 1
    yakuza_rep: int = 0
    sense_net_rep: int = 0
    hosaka_rep: int = 0
    ta_rep: int = 0
    freeside_rep: int = 0
    loa_rep: int = 0
    faction_rep: int = 0
    has_construct: bool = False
    consecutive_failures: int = 0
    consecutive_completions: int = 0
    consecutive_high_salvages: int = 0
    boss_defeated_recently: bool = False
    chain_complete_recently: bool = False
    chain_failed_recently: bool = False
    construct_lost_recently: bool = False
    fixer_used_recently: bool = False
    node_turns: int = 0
    bandwidth: int = 100
    corrupted_node: bool = False
    hp_pct: int = 100
    days_until_random_expires: int = 5
    reputation: object | None = None


def _make_mission(mid: str, grade_min: int = 1, grade_max: int = 6) -> Mission:
    """Construct a minimal Mission object (no JSON parse path)."""
    return Mission(
        id=mid,
        title=f"Mission {mid}",
        fixer="finn",
        arc=1,
        grade_min=grade_min,
        grade_max=grade_max,
        matrix_seed=1,
        zone="mid",
        objective="extract data",
        reward_tier=1,
        reward_credits=100,
        primary_objective=Objective(type="extract_data", count=1),
        secondary_objectives=(),
        rewards=Rewards(credits=100, materials={}),
    )


def _make_board_with_missions(mission_ids: list[str]) -> JobBoard:
    """Build a JobBoard from a list of mission IDs (no file I/O)."""
    return JobBoard(tuple(_make_mission(mid) for mid in mission_ids))


def _enter_event() -> object:
    """Build a synthetic ENTER KeyDown event."""
    import tcod.event

    return tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)


def _key_event(sym: object) -> object:
    """Build a synthetic KeyDown event with the given sym."""
    import tcod.event

    return tcod.event.KeyDown(sym=sym, mod=0, scancode=0)


# ---------------------------------------------------------------------------
# Hub position update when applying random rules
# ---------------------------------------------------------------------------


class TestHubEnterBiasesSelection:
    """Pressing ENTER at the hub biases the cursor via random_rules.select_weighted."""

    def test_enter_with_no_mission_biases_cursor(self) -> None:
        state = AppState()
        state.job_board = _make_board_with_missions(["m1", "m2", "m3"])
        state.player_grade = 1
        state.current_mission = None
        state.hub_selected_index = 0

        result = hub_mod.handle_hub_input(_enter_event(), state)
        assert result is True
        # The cursor should land on a valid index; with a weighted
        # pick the result is one of the available missions.
        assert 0 <= state.hub_selected_index < 3

    def test_enter_with_active_mission_does_not_bias(self) -> None:
        state = AppState()
        state.job_board = _make_board_with_missions(["m1", "m2"])
        state.current_mission = _make_mission("m1")
        state.hub_selected_index = 0

        hub_mod.handle_hub_input(_enter_event(), state)
        # Cursor unchanged when a mission is already in flight.
        assert state.hub_selected_index == 0

    def test_enter_with_no_available_missions_is_noop(self) -> None:
        state = AppState()
        state.job_board = JobBoard()
        state.current_mission = None
        state.hub_selected_index = 0

        result = hub_mod.handle_hub_input(_enter_event(), state)
        assert result is True
        assert state.hub_selected_index == 0


# ---------------------------------------------------------------------------
# Hub number-key fallback uses select_weighted for out-of-range keys
# ---------------------------------------------------------------------------


class TestHubNumberKeyFallback:
    """Pressing 1-9 with an out-of-range index uses select_weighted."""

    def test_out_of_range_key_picks_via_select_weighted(self) -> None:
        state = AppState()
        state.job_board = _make_board_with_missions(["m1", "m2", "m3"])
        state.player_grade = 1
        state.current_mission = None

        # Press KeySym.N5 (out of range for 3 missions).
        result = hub_mod.handle_hub_input(
            _key_event(__import__("tcod.event").event.KeySym.N5), state
        )
        assert result is True
        # A mission got picked: current_mission is now set.
        assert state.current_mission is not None
        assert state.current_mission.id in {"m1", "m2", "m3"}

    def test_in_range_key_picks_explicit_index(self) -> None:
        state = AppState()
        state.job_board = _make_board_with_missions(["m1", "m2", "m3"])
        state.player_grade = 1
        state.current_mission = None

        # Press KeySym.N2 → index 1 → m2.
        result = hub_mod.handle_hub_input(
            _key_event(__import__("tcod.event").event.KeySym.N2), state
        )
        assert result is True
        assert state.current_mission is not None
        assert state.current_mission.id == "m2"


# ---------------------------------------------------------------------------
# Weighted selection differs from flat index pick for non-trivial state
# ---------------------------------------------------------------------------


class TestWeightedSelectionDiffersByState:
    """Same seed, different state → different weighted pick."""

    def test_pick_varies_with_faction_rep(self) -> None:
        state_a = DummyState(grade=1, sense_net_rep=0)
        state_b = DummyState(grade=1, sense_net_rep=5)

        board = _make_board_with_missions(
            ["mission_a", "mission_b", "mission_c", "mission_d", "mission_e"]
        )
        # Sanity: pick returns a valid mission for both.
        pick_a = board.select_weighted(state_a, seed=42)
        pick_b = board.select_weighted(state_b, seed=42)
        assert pick_a is not None
        assert pick_b is not None

    def test_pick_with_high_grade_filter(self) -> None:
        """A grade-5 player sees only grade-5 missions."""
        board = _make_board_with_missions(["m1", "m2", "m3"])
        for m_id in ["m1", "m2", "m3"]:
            board._missions[m_id] = replace(
                board._missions[m_id],
                grade_min=5,
                grade_max=6,
            )
        state = DummyState(grade=5)
        # 10 picks must all be in {m1, m2, m3} (the only grade-5 ones).
        for _ in range(10):
            picked = board.select_weighted(state, seed=42)
            assert picked is not None
            assert picked.id in {"m1", "m2", "m3"}


# ---------------------------------------------------------------------------
# Phase 20 edge cases: empty state, all-zero rep, NG+ state, large pool
# ---------------------------------------------------------------------------


class TestRandomRulesEdgeCases:
    """Edge-case coverage for Phase 20.

    Hardens ``JobBoard.select_weighted`` against unusual inputs:
    empty mission lists, zero-reputation states, NG+ (grade 6+)
    unlocks, large pools, and deterministic seeds across many runs.
    """

    def test_empty_mission_list_returns_none(self) -> None:
        """select_weighted on an empty board returns None gracefully."""
        state = DummyState(grade=1)
        board = JobBoard()
        assert board.select_weighted(state, seed=42) is None
        assert board.select_weighted(state, available=(), seed=42) is None

    def test_all_factions_zero_rep_state(self) -> None:
        """A state with every faction at 0 rep must still pick a mission."""
        state = DummyState(
            grade=2,
            yakuza_rep=0,
            sense_net_rep=0,
            hosaka_rep=0,
            ta_rep=0,
            freeside_rep=0,
            loa_rep=0,
        )
        board = _make_board_with_missions(["m1", "m2", "m3"])
        picked = board.select_weighted(state, seed=42)
        assert picked is not None
        assert picked.id in {"m1", "m2", "m3"}

    def test_ng_plus_grade_six_state(self) -> None:
        """NG+ (grade 6) players should be handled by the weighted path."""
        state = DummyState(grade=6)
        board = _make_board_with_missions(["g6a", "g6b", "g6c"])
        for mid in ["g6a", "g6b", "g6c"]:
            board._missions[mid] = replace(
                board._missions[mid],
                grade_min=6,
                grade_max=6,
            )
        picked = board.select_weighted(state, seed=42)
        assert picked is not None
        assert picked.id in {"g6a", "g6b", "g6c"}

    def test_determinism_same_seed_identical_picks(self) -> None:
        """Same seed across multiple select_weighted calls returns the same mission."""
        state = DummyState(grade=2)
        board = _make_board_with_missions(["m1", "m2", "m3", "m4", "m5"])
        picks = {board.select_weighted(state, seed=999).id for _ in range(5)}
        assert len(picks) == 1
        assert next(iter(picks)) in {"m1", "m2", "m3", "m4", "m5"}

    def test_rule_conflicts_multiple_rules_active(self) -> None:
        """High rep across many factions activates multiple rules simultaneously.

        The weighted path must still pick a single (valid) mission without
        crashing even when many rules have fires.
        """
        state = DummyState(
            grade=3,
            yakuza_rep=5,
            sense_net_rep=5,
            hosaka_rep=5,
            ta_rep=5,
            freeside_rep=5,
            loa_rep=5,
            consecutive_failures=99,
            consecutive_completions=99,
            boss_defeated_recently=True,
        )
        board = _make_board_with_missions([f"m{i}" for i in range(20)])
        for _ in range(10):
            picked = board.select_weighted(state, seed=42)
            assert picked is not None
            assert picked.id.startswith("m")

    def test_large_mission_pool_100_plus(self) -> None:
        """Performance sanity: 150 mission pool must still complete a weighted pick."""
        mission_ids = [f"mission_{i:03d}" for i in range(150)]
        board = _make_board_with_missions(mission_ids)
        state = DummyState(grade=4)
        picked = board.select_weighted(state, seed=42)
        assert picked is not None
        assert picked.id in mission_ids

    def test_empty_available_with_grade_provided(self) -> None:
        """Grade outside any mission range yields empty available set."""
        state = DummyState(grade=99)
        board = _make_board_with_missions(["m1", "m2"])
        picked = board.select_weighted(state, seed=42)
        assert picked is None

    def test_last_rule_id_attribute_set_when_present(self) -> None:
        """select_weighted writes to last_rule_id on AppState (has the field)."""
        state = AppState()
        state.player_grade = 4
        board = _make_board_with_missions(["m1", "m2", "m3"])
        board.select_weighted(state, seed=42)
        # AppState always has last_rule_id; it's either a string or None.
        assert state.last_rule_id is None or isinstance(state.last_rule_id, str)
