"""Run Mutators system (ADR-0163).

5+ optional mutators applied at run start that change the rules
per-playthrough. Mutators amplify Pillar 3 (death weight) and
Pillar 4 (build variety).
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine.state import AppState


class RunMutator(StrEnum):
    """Run modifiers that change game rules per-playthrough."""

    LOW_HP = "low_hp"
    DOUBLE_ALARM = "double_alarm"
    ICE_X2 = "ice_x2"
    NO_HEAL = "no_heal"
    STEALTH_ONLY = "stealth_only"


MUTATORS: dict[RunMutator, dict[str, str]] = {
    RunMutator.LOW_HP: {
        "name": "FRAGILE WETWARE",
        "description": "Start with 50% max HP. One bad run ends you.",
        "icon": "low_hp",
    },
    RunMutator.DOUBLE_ALARM: {
        "name": "HOT TRACE",
        "description": "Alarm ticks 2x faster. ICE pursues.",
        "icon": "double_alarm",
    },
    RunMutator.ICE_X2: {
        "name": "POPULATED GRID",
        "description": "Every encounter is 1v2 or 1v3. The grid is *crowded*.",
        "icon": "ice_x2",
    },
    RunMutator.NO_HEAL: {
        "name": "DEAD MAN WALKING",
        "description": "Cannot salvage HEAL from kills. No recovery.",
        "icon": "no_heal",
    },
    RunMutator.STEALTH_ONLY: {
        "name": "GHOST PROTOCOL",
        "description": "Only stealth skills available. Silent runs.",
        "icon": "stealth_only",
    },
}


def get_mutator_info(mutator: RunMutator) -> dict[str, str]:
    """Return display info for a mutator."""
    return MUTATORS[mutator]


def apply_mutators(app_state: AppState, mutators: list[RunMutator]) -> None:
    """Apply mutators to AppState (idempotent — clears previous first)."""
    clear_mutators(app_state)
    for mutator in mutators:
        if mutator == RunMutator.LOW_HP:
            app_state.player_max_hp = app_state.player_max_hp // 2
            app_state.player_hp = min(app_state.player_hp, app_state.player_max_hp)
        elif mutator == RunMutator.DOUBLE_ALARM:
            app_state.alarm_speed_multiplier = 2.0
        elif mutator == RunMutator.ICE_X2:
            app_state.encounter_multiplier = 2
        elif mutator == RunMutator.NO_HEAL:
            app_state.heal_disabled = True
        elif mutator == RunMutator.STEALTH_ONLY:
            app_state.skill_filter = "stealth_only"
    app_state.active_mutators = tuple(mutators)


def clear_mutators(app_state: AppState) -> None:
    """Clear all mutator effects from AppState."""
    for mutator in app_state.active_mutators:
        if mutator == RunMutator.LOW_HP:
            app_state.player_max_hp = app_state.player_max_hp * 2
        elif mutator == RunMutator.DOUBLE_ALARM:
            app_state.alarm_speed_multiplier = 1.0
        elif mutator == RunMutator.ICE_X2:
            app_state.encounter_multiplier = 1
        elif mutator == RunMutator.NO_HEAL:
            app_state.heal_disabled = False
        elif mutator == RunMutator.STEALTH_ONLY:
            app_state.skill_filter = None
    app_state.active_mutators = ()


def is_mutator_active(app_state: AppState, mutator: RunMutator) -> bool:
    """Check if a mutator is currently active."""
    return mutator in app_state.active_mutators


def get_active_mutators(app_state: AppState) -> tuple[RunMutator, ...]:
    """Return the active mutators list."""
    result: tuple[RunMutator, ...] = tuple(RunMutator(m) for m in app_state.active_mutators)
    return result


def get_alarm_multiplier(app_state: AppState) -> float:
    """Return the alarm speed multiplier (1.0 = normal, 2.0 = DOUBLE_ALARM)."""
    return app_state.alarm_speed_multiplier


def get_encounter_multiplier(app_state: AppState) -> int:
    """Return the encounter count multiplier (1 = normal, 2 = ICE_X2)."""
    return app_state.encounter_multiplier


def is_heal_disabled(app_state: object) -> bool:
    """Return True if HEAL salvage is disabled (NO_HEAL mutator)."""
    return bool(getattr(app_state, "heal_disabled", False))


def is_stealth_only(app_state: AppState) -> bool:
    """Return True if only stealth skills available (STEALTH_ONLY mutator)."""
    return app_state.skill_filter == "stealth_only"


def hp_multiplier(mutator: RunMutator) -> float:
    """Return HP multiplier for a mutator (LOW_HP = 0.5, others = 1.0)."""
    if mutator == RunMutator.LOW_HP:
        return 0.5
    return 1.0


__all__ = [
    "MUTATORS",
    "RunMutator",
    "apply_mutators",
    "clear_mutators",
    "get_active_mutators",
    "get_alarm_multiplier",
    "get_encounter_multiplier",
    "get_mutator_info",
    "hp_multiplier",
    "is_heal_disabled",
    "is_mutator_active",
    "is_stealth_only",
]
