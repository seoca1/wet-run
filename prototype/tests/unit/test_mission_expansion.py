"""Tests for Mission Expansion (ADR-0167)."""

from __future__ import annotations

import dataclasses

import pytest

from roguelike_sprawl.combat.mission_expansion import (
    EXPANSION_MISSIONS,
    expansion_mission_count,
    expansion_mission_ids,
    expansion_missions_by_difficulty,
    get_expansion_mission,
    is_expansion_mission,
)


def test_expansion_mission_count() -> None:
    assert expansion_mission_count() == 6
    assert len(EXPANSION_MISSIONS) == 6


def test_expansion_mission_ids_complete() -> None:
    ids = expansion_mission_ids()
    assert "hosaka_after_hours" in ids
    assert "sense_net_infiltration" in ids
    assert "yakuza_meeting" in ids
    assert "t_a_construction_site" in ids
    assert "zion_lab_breach" in ids
    assert "construct_market" in ids


def test_get_expansion_mission_existing() -> None:
    mission = get_expansion_mission("hosaka_after_hours")
    assert mission is not None
    assert mission.id == "hosaka_after_hours"
    assert mission.difficulty == "novice"


def test_get_expansion_mission_nonexistent() -> None:
    assert get_expansion_mission("nonexistent") is None


def test_is_expansion_mission_true() -> None:
    assert is_expansion_mission("hosaka_after_hours")
    assert is_expansion_mission("sense_net_infiltration")
    assert is_expansion_mission("yakuza_meeting")
    assert is_expansion_mission("t_a_construction_site")
    assert is_expansion_mission("zion_lab_breach")
    assert is_expansion_mission("construct_market")


def test_is_expansion_mission_false() -> None:
    assert not is_expansion_mission("nonexistent")
    assert not is_expansion_mission("first_jack")
    assert not is_expansion_mission("ghost_signal_origin")


def test_expansion_missions_by_difficulty_novice() -> None:
    novice = expansion_missions_by_difficulty("novice")
    assert len(novice) == 2
    ids = {m.id for m in novice}
    assert "hosaka_after_hours" in ids
    assert "construct_market" in ids


def test_expansion_missions_by_difficulty_veteran() -> None:
    veteran = expansion_missions_by_difficulty("veteran")
    assert len(veteran) == 2
    ids = {m.id for m in veteran}
    assert "sense_net_infiltration" in ids
    assert "yakuza_meeting" in ids


def test_expansion_missions_by_difficulty_heretic() -> None:
    heretic = expansion_missions_by_difficulty("heretic")
    assert len(heretic) == 2
    ids = {m.id for m in heretic}
    assert "t_a_construction_site" in ids
    assert "zion_lab_breach" in ids


def test_expansion_missions_by_difficulty_none() -> None:
    assert expansion_missions_by_difficulty("nonexistent") == ()


def test_all_expansion_missions_have_ice() -> None:
    for mission in EXPANSION_MISSIONS:
        assert len(mission.primary_ice) > 0


def test_expansion_mission_immutable() -> None:
    mission = get_expansion_mission("hosaka_after_hours")
    assert mission is not None
    try:
        mission.id = "modified"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass
