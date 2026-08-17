"""Tests for Random Rules → JobBoard integration (ADR-0188, Round 4)."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from wet_run.missions.board import JobBoard


def _make_mission(mid: str, grade_min: int = 1, grade_max: int = 6, fixer: str = "finn"):
    """Create a minimal mission dict for testing."""
    return {
        "id": mid,
        "title": f"Mission {mid}",
        "fixer": fixer,
        "arc": 1,
        "grade_min": grade_min,
        "grade_max": grade_max,
        "primary_objective": {
            "type": "extract_data",
            "data_id": "x",
            "count": 1,
        },
        "secondary_objectives": [],
        "matrix_seed": 1,
        "zone": "mid",
        "rewards": {"credits": 100, "materials": {}},
        "is_canonical_cast": True,
        "reward_credits": 100,
        "reward_tier": 1,
    }


def _make_board(mission_ids: list[str], tmp_path: Path) -> JobBoard:
    """Create a JobBoard from a list of mission IDs via temp JSON file."""
    data = {mid: _make_mission(mid) for mid in mission_ids}
    path = tmp_path / "missions.json"
    path.write_text(json.dumps(data))
    return JobBoard.load(path)


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
    reputation: dict | None = None


class TestJobBoardSelectWeighted:
    """JobBoard.select_weighted uses random_rules for selection."""

    def test_select_weighted_returns_mission(self, tmp_path: Path) -> None:
        board = _make_board(["m1", "m2", "m3"], tmp_path)
        state = DummyState()
        result = board.select_weighted(state, seed=42)
        assert result is not None
        assert result.id in ["m1", "m2", "m3"]

    def test_select_weighted_empty_returns_none(self) -> None:
        board = JobBoard()
        state = DummyState()
        result = board.select_weighted(state, seed=42)
        assert result is None

    def test_select_weighted_seed_deterministic(self, tmp_path: Path) -> None:
        board = _make_board(["m1", "m2", "m3"], tmp_path)
        state = DummyState()
        r1 = board.select_weighted(state, seed=42)
        r2 = board.select_weighted(state, seed=42)
        assert r1.id == r2.id

    def test_select_weighted_respects_grade(self, tmp_path: Path) -> None:
        board = _make_board(["m_low", "m_high"], tmp_path)
        board._missions["m_low"] = replace(
            board._missions["m_low"],
            grade_min=1,
            grade_max=2,
        )
        board._missions["m_high"] = replace(
            board._missions["m_high"],
            grade_min=5,
            grade_max=6,
        )
        state = DummyState(grade=1)
        for _ in range(10):
            result = board.select_weighted(state, seed=42)
            assert result is not None
            assert result.id == "m_low"

    def test_select_weighted_seed_42_specific(self, tmp_path: Path) -> None:
        board = _make_board(["alpha", "beta", "gamma"], tmp_path)
        state = DummyState()
        result = board.select_weighted(state, seed=42)
        assert result is not None
        assert result.id in ("alpha", "beta", "gamma")


class TestJobBoardSelectByFaction:
    """JobBoard.select_by_faction filters by fixer."""

    def test_select_by_faction_filters_correctly(self, tmp_path: Path) -> None:
        board = _make_board(["m_finn", "m_yakuza", "m_finn2"], tmp_path)
        board._missions["m_yakuza"] = replace(
            board._missions["m_yakuza"],
            fixer="yakuza",
        )
        board._missions["m_finn2"] = replace(
            board._missions["m_finn2"],
            fixer="finn",
        )
        result = board.select_by_faction("finn", 1)
        assert len(result) == 2
        for m in result:
            assert m.fixer == "finn"

    def test_select_by_faction_empty(self, tmp_path: Path) -> None:
        board = _make_board(["m1"], tmp_path)
        result = board.select_by_faction("hosaka", 1)
        assert result == ()


class TestJobBoardIntegration:
    """Integration of random rules with JobBoard filtering."""

    def test_select_weighted_with_grade_filter(self, tmp_path: Path) -> None:
        board = _make_board(["m1", "m2", "m3"], tmp_path)
        for m_id in ["m1", "m2", "m3"]:
            board._missions[m_id] = replace(
                board._missions[m_id],
                grade_min=3,
                grade_max=4,
            )
        state = DummyState(grade=3)
        result = board.select_weighted(state, seed=42)
        assert result is not None
        assert result.id in ["m1", "m2", "m3"]

    def test_select_weighted_with_pre_filtered_missions(self, tmp_path: Path) -> None:
        board = _make_board(["m1", "m2", "m3"], tmp_path)
        all_missions = tuple(board._missions.values())
        filtered = tuple(m for m in all_missions if m.id in ["m1", "m2"])
        state = DummyState()
        result = board.select_weighted(state, available=filtered, seed=42)
        assert result is not None
        assert result.id in ["m1", "m2"]
