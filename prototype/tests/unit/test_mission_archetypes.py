"""Tests for Mission Archetypes (ADR-0164)."""

from __future__ import annotations

from wet_run.combat.mission_archetypes import (
    MISSION_ARCHETYPES,
    MissionArchetype,
    alarm_per_kill,
    apply_archetype,
    clear_archetype,
    fast_clear_bonus_per_ten_seconds,
    friendly_node_hp,
    get_active_archetype,
    get_archetype_info,
    get_archetype_rules,
    is_archetype_active,
    partial_pay_percent,
    wave_count,
)
from wet_run.engine.state import AppState


def make_app_state() -> AppState:
    return AppState()


def test_mission_archetype_enum_has_4_entries() -> None:
    assert len(MissionArchetype) == 4
    assert MissionArchetype.STEALTH.value == "stealth"
    assert MissionArchetype.RACE.value == "race"
    assert MissionArchetype.EXTRACTION.value == "extraction"
    assert MissionArchetype.DEFENSE.value == "defense"


def test_mission_archetypes_registry_has_all() -> None:
    for archetype in MissionArchetype:
        assert archetype in MISSION_ARCHETYPES
        info = MISSION_ARCHETYPES[archetype]
        assert "name" in info
        assert "description" in info
        assert "icon" in info


def test_get_archetype_info_returns_config() -> None:
    info = get_archetype_info(MissionArchetype.STEALTH)
    assert info["name"] == "STEALTH"
    assert "wintermute" in info["description"].lower()


def test_apply_archetype() -> None:
    state = make_app_state()
    apply_archetype(state, MissionArchetype.STEALTH)
    assert get_active_archetype(state) == MissionArchetype.STEALTH
    assert is_archetype_active(state, MissionArchetype.STEALTH)


def test_apply_archetype_replaces_existing() -> None:
    state = make_app_state()
    apply_archetype(state, MissionArchetype.STEALTH)
    apply_archetype(state, MissionArchetype.RACE)
    assert get_active_archetype(state) == MissionArchetype.RACE
    assert not is_archetype_active(state, MissionArchetype.STEALTH)


def test_clear_archetype() -> None:
    state = make_app_state()
    apply_archetype(state, MissionArchetype.STEALTH)
    clear_archetype(state)
    assert get_active_archetype(state) is None
    assert not is_archetype_active(state, MissionArchetype.STEALTH)


def test_is_archetype_active_returns_true_only_for_matching() -> None:
    state = make_app_state()
    apply_archetype(state, MissionArchetype.RACE)
    assert is_archetype_active(state, MissionArchetype.RACE)
    assert not is_archetype_active(state, MissionArchetype.STEALTH)
    assert not is_archetype_active(state, MissionArchetype.DEFENSE)


def test_get_archetype_rules_returns_dict() -> None:
    state = make_app_state()
    apply_archetype(state, MissionArchetype.STEALTH)
    rules = get_archetype_rules(state)
    assert rules["name"] == "STEALTH"
    assert "alarm_per_kill" in rules


def test_get_archetype_rules_empty_when_none() -> None:
    state = make_app_state()
    rules = get_archetype_rules(state)
    assert rules == {}


def test_alarm_per_kill_stealth() -> None:
    assert alarm_per_kill(MissionArchetype.STEALTH) == 5
    assert alarm_per_kill(MissionArchetype.RACE) == 0
    assert alarm_per_kill(MissionArchetype.EXTRACTION) == 0
    assert alarm_per_kill(MissionArchetype.DEFENSE) == 0


def test_fast_clear_bonus_per_ten_seconds_race() -> None:
    assert fast_clear_bonus_per_ten_seconds(MissionArchetype.RACE) == 30
    assert fast_clear_bonus_per_ten_seconds(MissionArchetype.STEALTH) == 0
    assert fast_clear_bonus_per_ten_seconds(MissionArchetype.EXTRACTION) == 0
    assert fast_clear_bonus_per_ten_seconds(MissionArchetype.DEFENSE) == 0


def test_partial_pay_percent_extraction() -> None:
    assert partial_pay_percent(MissionArchetype.EXTRACTION) == 30
    assert partial_pay_percent(MissionArchetype.STEALTH) == 0
    assert partial_pay_percent(MissionArchetype.RACE) == 0
    assert partial_pay_percent(MissionArchetype.DEFENSE) == 0


def test_friendly_node_hp_defense() -> None:
    assert friendly_node_hp(MissionArchetype.DEFENSE) == 500
    assert friendly_node_hp(MissionArchetype.STEALTH) == 0
    assert friendly_node_hp(MissionArchetype.RACE) == 0
    assert friendly_node_hp(MissionArchetype.EXTRACTION) == 0


def test_wave_count_defense() -> None:
    assert wave_count(MissionArchetype.DEFENSE) == 3
    assert wave_count(MissionArchetype.STEALTH) == 0
    assert wave_count(MissionArchetype.RACE) == 0
    assert wave_count(MissionArchetype.EXTRACTION) == 0


def test_main_state_intact_after_clear() -> None:
    state = make_app_state()
    state.credits = 100
    apply_archetype(state, MissionArchetype.STEALTH)
    clear_archetype(state)
    assert state.credits == 100
    assert get_active_archetype(state) is None
