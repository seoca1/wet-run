"""Tests for Phase 6 Arc - Aftermath (ADR-0166)."""

from __future__ import annotations

import dataclasses

import pytest

from wet_run.combat.arc6 import (
    ARC6_MISSIONS,
    arc6_mission_count,
    arc6_mission_ids,
    arc6_missions_by_difficulty,
    get_arc6_mission,
    is_arc6_mission,
)


def test_arc6_mission_count() -> None:
    assert arc6_mission_count() == 4
    assert len(ARC6_MISSIONS) == 4


def test_arc6_mission_ids_complete() -> None:
    ids = arc6_mission_ids()
    assert "ghost_signal_origin" in ids
    assert "wintermute_residue" in ids
    assert "tessier_ashpool_aftermath" in ids
    assert "neuromancer_merger_residue" in ids


def test_arc6_mission_ids_returns_4() -> None:
    assert len(arc6_mission_ids()) == 4


def test_get_arc6_mission_existing() -> None:
    mission = get_arc6_mission("ghost_signal_origin")
    assert mission is not None
    assert mission.id == "ghost_signal_origin"
    assert mission.difficulty == "novice"
    assert mission.zone == "aftermath"


def test_get_arc6_mission_nonexistent() -> None:
    assert get_arc6_mission("nonexistent") is None


def test_is_arc6_mission_true() -> None:
    assert is_arc6_mission("ghost_signal_origin")
    assert is_arc6_mission("wintermute_residue")
    assert is_arc6_mission("tessier_ashpool_aftermath")
    assert is_arc6_mission("neuromancer_merger_residue")


def test_is_arc6_mission_false() -> None:
    assert not is_arc6_mission("nonexistent")
    assert not is_arc6_mission("first_jack")
    assert not is_arc6_mission("")


def test_arc6_missions_by_difficulty_novice() -> None:
    novice = arc6_missions_by_difficulty("novice")
    assert len(novice) == 1
    assert novice[0].id == "ghost_signal_origin"


def test_arc6_missions_by_difficulty_veteran() -> None:
    veteran = arc6_missions_by_difficulty("veteran")
    assert len(veteran) == 2
    ids = {m.id for m in veteran}
    assert "wintermute_residue" in ids
    assert "tessier_ashpool_aftermath" in ids


def test_arc6_missions_by_difficulty_heretic() -> None:
    heretic = arc6_missions_by_difficulty("heretic")
    assert len(heretic) == 1
    assert heretic[0].id == "neuromancer_merger_residue"


def test_arc6_missions_by_difficulty_none() -> None:
    assert arc6_missions_by_difficulty("nonexistent") == ()


def test_all_arc6_missions_are_aftermath_zone() -> None:
    for mission in ARC6_MISSIONS:
        assert mission.zone == "aftermath"


def test_all_arc6_missions_have_ice() -> None:
    for mission in ARC6_MISSIONS:
        assert len(mission.primary_ice) > 0


def test_arc6_mission_immutable() -> None:
    mission = get_arc6_mission("ghost_signal_origin")
    assert mission is not None
    try:
        mission.id = "modified"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass
