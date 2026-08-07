"""Tests for Run Mutators (ADR-0163)."""

from __future__ import annotations

from roguelike_sprawl.combat.run_mutators import (
    MUTATORS,
    RunMutator,
    apply_mutators,
    clear_mutators,
    get_active_mutators,
    get_alarm_multiplier,
    get_encounter_multiplier,
    get_mutator_info,
    hp_multiplier,
    is_heal_disabled,
    is_mutator_active,
    is_stealth_only,
)
from roguelike_sprawl.engine.state import AppState


def make_app_state() -> AppState:
    return AppState(
        player_hp=100,
        player_max_hp=100,
    )


def test_run_mutator_enum_has_5_entries() -> None:
    assert len(RunMutator) == 5
    assert RunMutator.LOW_HP.value == "low_hp"
    assert RunMutator.DOUBLE_ALARM.value == "double_alarm"
    assert RunMutator.ICE_X2.value == "ice_x2"
    assert RunMutator.NO_HEAL.value == "no_heal"
    assert RunMutator.STEALTH_ONLY.value == "stealth_only"


def test_mutators_registry_has_all() -> None:
    for mutator in RunMutator:
        assert mutator in MUTATORS
        info = MUTATORS[mutator]
        assert "name" in info
        assert "description" in info
        assert "icon" in info


def test_get_mutator_info_returns_config() -> None:
    info = get_mutator_info(RunMutator.LOW_HP)
    assert info["name"] == "FRAGILE WETWARE"
    assert "50%" in info["description"]


def test_apply_no_mutators() -> None:
    state = make_app_state()
    apply_mutators(state, [])
    assert get_active_mutators(state) == ()
    assert state.alarm_speed_multiplier == 1.0
    assert state.encounter_multiplier == 1
    assert not is_heal_disabled(state)
    assert not is_stealth_only(state)


def test_apply_low_hp_halves_max_hp() -> None:
    state = make_app_state()
    apply_mutators(state, [RunMutator.LOW_HP])
    assert state.player_max_hp == 50
    assert state.player_hp == 50
    assert is_mutator_active(state, RunMutator.LOW_HP)


def test_apply_double_alarm_doubles_alarm_speed() -> None:
    state = make_app_state()
    apply_mutators(state, [RunMutator.DOUBLE_ALARM])
    assert get_alarm_multiplier(state) == 2.0


def test_apply_ice_x2_doubles_encounter_multiplier() -> None:
    state = make_app_state()
    apply_mutators(state, [RunMutator.ICE_X2])
    assert get_encounter_multiplier(state) == 2


def test_apply_no_heal_disables_heal() -> None:
    state = make_app_state()
    apply_mutators(state, [RunMutator.NO_HEAL])
    assert is_heal_disabled(state)


def test_apply_stealth_only_sets_filter() -> None:
    state = make_app_state()
    apply_mutators(state, [RunMutator.STEALTH_ONLY])
    assert is_stealth_only(state)
    assert state.skill_filter == "stealth_only"


def test_apply_multiple_mutators() -> None:
    state = make_app_state()
    apply_mutators(state, [RunMutator.LOW_HP, RunMutator.DOUBLE_ALARM])
    assert state.player_max_hp == 50
    assert get_alarm_multiplier(state) == 2.0
    assert len(get_active_mutators(state)) == 2


def test_apply_mutators_is_idempotent() -> None:
    state = make_app_state()
    apply_mutators(state, [RunMutator.LOW_HP])
    apply_mutators(state, [RunMutator.DOUBLE_ALARM])
    assert state.player_max_hp == 100
    assert get_alarm_multiplier(state) == 2.0
    assert get_active_mutators(state) == (RunMutator.DOUBLE_ALARM,)


def test_clear_mutators_restores_state() -> None:
    state = make_app_state()
    apply_mutators(state, [RunMutator.LOW_HP, RunMutator.DOUBLE_ALARM])
    clear_mutators(state)
    assert state.player_max_hp == 100
    assert get_alarm_multiplier(state) == 1.0
    assert get_active_mutators(state) == ()


def test_is_mutator_active_false_when_not_applied() -> None:
    state = make_app_state()
    assert not is_mutator_active(state, RunMutator.LOW_HP)


def test_hp_multiplier() -> None:
    assert hp_multiplier(RunMutator.LOW_HP) == 0.5
    assert hp_multiplier(RunMutator.DOUBLE_ALARM) == 1.0
    assert hp_multiplier(RunMutator.ICE_X2) == 1.0
    assert hp_multiplier(RunMutator.NO_HEAL) == 1.0
    assert hp_multiplier(RunMutator.STEALTH_ONLY) == 1.0


def test_active_mutators_preserved_after_other_field_changes() -> None:
    state = make_app_state()
    apply_mutators(state, [RunMutator.ICE_X2])
    state.credits = 100
    assert is_mutator_active(state, RunMutator.ICE_X2)
    assert get_encounter_multiplier(state) == 2


def test_clear_is_safe_on_empty_mutators() -> None:
    state = make_app_state()
    clear_mutators(state)
    assert state.alarm_speed_multiplier == 1.0
    assert state.encounter_multiplier == 1


def test_low_hp_clamps_current_hp_to_new_max() -> None:
    state = AppState(player_hp=80, player_max_hp=100)
    apply_mutators(state, [RunMutator.LOW_HP])
    assert state.player_max_hp == 50
    assert state.player_hp == 50
