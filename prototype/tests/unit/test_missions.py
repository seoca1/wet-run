"""Tests for missions and the job board (ADR-0010, ADR-0008)."""

from __future__ import annotations

from pathlib import Path

from wet_run.matrix.node import ZoneDepth
from wet_run.missions import JobBoard, Mission


def test_mission_creation() -> None:
    m = Mission(
        id="first_jack",
        title="First Jack",
        fixer="finn",
        arc=1,
        grade_min=1,
        grade_max=1,
        objective="Extract the demo file.",
        matrix_seed=42,
        zone=ZoneDepth.SURFACE,
        reward_tier=1,
        reward_credits=500,
    )
    assert m.id == "first_jack"
    assert m.arc == 1
    assert m.zone is ZoneDepth.SURFACE


def test_mission_invalid_grade_range() -> None:
    import pytest

    with pytest.raises(ValueError, match="grade"):
        Mission(
            id="x",
            title="X",
            fixer="finn",
            arc=1,
            grade_min=3,
            grade_max=2,
            objective="x",
            matrix_seed=1,
            zone=ZoneDepth.SURFACE,
            reward_tier=1,
            reward_credits=0,
        )


def test_job_board_empty() -> None:
    board = JobBoard()
    assert len(board) == 0
    assert board.available_for(grade=1) == ()


def test_job_board_load_missing_file(tmp_path: Path) -> None:
    board = JobBoard.load(tmp_path / "missing.json")
    assert len(board) == 0


def test_job_board_load_real_file(data_dir: Path) -> None:
    board = JobBoard.load(data_dir / "missions" / "missions.json")
    assert len(board) >= 2
    first = board.get("first_jack")
    assert first is not None
    assert first.fixer == "finn"
    assert first.zone is ZoneDepth.SURFACE


def test_job_board_loads_all_29_missions(data_dir: Path) -> None:
    """Regression: every mission in missions.json must load successfully.

    Pre-fix: 13/29 missions silently failed to load because ZoneDepth
    enum didn't include DEEP / FREESIDE tiers. This test would have
    caught it.

    Note: missions.json grew from 29 → 33 (4 suit-persona missions
    added in 2026-06-30). The regression intent is preserved.
    """
    board = JobBoard.load(data_dir / "missions" / "missions.json")
    assert len(board) >= 29, f"Expected ≥29 missions, got {len(board)}"


def test_job_board_mission_zones_all_valid(data_dir: Path) -> None:
    """Regression: every mission's zone field must be a valid ZoneDepth."""
    board = JobBoard.load(data_dir / "missions" / "missions.json")
    valid_zones = {z.value for z in ZoneDepth}
    for mission in board:
        assert mission.zone.value in valid_zones, (
            f"{mission.id}: zone {mission.zone.value!r} not in ZoneDepth"
        )


def test_zone_depth_has_deep_and_freeside() -> None:
    """Regression: ZoneDepth must include the DEEP and FREESIDE tiers
    introduced for Loa / construct zones and orbital colonies."""
    assert ZoneDepth.DEEP.value == "deep"
    assert ZoneDepth.FREESIDE.value == "freeside"


def test_job_board_available_for_filters_by_grade(data_dir: Path) -> None:
    board = JobBoard.load(data_dir / "missions" / "missions.json")
    g1 = board.available_for(grade=1)
    assert all(m.grade_min <= 1 <= m.grade_max for m in g1)
    g5 = board.available_for(grade=5)
    assert all(m.grade_min <= 5 <= m.grade_max for m in g5)
    # Arc 5 finales support grade_max=6 (master jockies)
    g6 = board.available_for(grade=6)
    assert all(m.grade_min <= 6 <= m.grade_max for m in g6)


def test_job_board_add_and_get() -> None:
    board = JobBoard()
    m = Mission(
        id="x",
        title="X",
        fixer="finn",
        arc=1,
        grade_min=1,
        grade_max=3,
        objective="x",
        matrix_seed=1,
        zone=ZoneDepth.SURFACE,
        reward_tier=1,
        reward_credits=0,
    )
    board.add(m)
    assert board.get("x") is m
    assert "x" in board
    assert "missing" not in board
