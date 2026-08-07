"""Mission Archetypes system (ADR-0164).

4 mission types that change rules per-mission:
- STEALTH: kills increase alarm; bonus for no-kill
- RACE: time limit; bonus for fast clear
- EXTRACTION: multi-objective; partial success pays
- DEFENSE: protect friendly node; survive waves
"""

from __future__ import annotations

from enum import StrEnum

from ..engine.state import AppState


class MissionArchetype(StrEnum):
    """Mission types that change rules per-mission."""

    STEALTH = "stealth"
    RACE = "race"
    EXTRACTION = "extraction"
    DEFENSE = "defense"


MISSION_ARCHETYPES: dict[MissionArchetype, dict[str, str]] = {
    MissionArchetype.STEALTH: {
        "name": "STEALTH",
        "description": "Move like wintermute. Kills spike alarm.",
        "icon": "stealth",
        "alarm_per_kill": "+5",
        "no_kill_bonus": "+50 CRED",
        "time_limit": "none",
    },
    MissionArchetype.RACE: {
        "name": "RACE",
        "description": "Fast or dead. Beat the clock.",
        "icon": "race",
        "time_limit": "45s",
        "fast_clear_bonus": "+30 CRED per 10s under",
    },
    MissionArchetype.EXTRACTION: {
        "name": "EXTRACTION",
        "description": "Multi-objective. Partial pays.",
        "icon": "extraction",
        "objectives": "3 packages",
        "partial_pay": "30% per package",
    },
    MissionArchetype.DEFENSE: {
        "name": "DEFENSE",
        "description": "Hold the node. Survive the wave.",
        "icon": "defense",
        "friendly_node_hp": "500",
        "wave_count": "3",
    },
}


def get_archetype_info(archetype: MissionArchetype) -> dict[str, str]:
    """Return display info for a mission archetype."""
    return MISSION_ARCHETYPES[archetype]


def apply_archetype(app_state: AppState, archetype: MissionArchetype) -> None:
    """Apply a mission archetype to AppState."""
    clear_archetype(app_state)
    app_state.active_archetype = archetype


def clear_archetype(app_state: AppState) -> None:
    """Clear the active mission archetype."""
    app_state.active_archetype = None


def is_archetype_active(app_state: AppState, archetype: MissionArchetype) -> bool:
    """Check if a specific archetype is active."""
    return app_state.active_archetype == archetype.value


def get_active_archetype(app_state: AppState) -> MissionArchetype | None:
    """Return the active archetype or None."""
    if app_state.active_archetype is None:
        return None
    return MissionArchetype(app_state.active_archetype)


def get_archetype_rules(app_state: AppState) -> dict[str, str]:
    """Return rules for the active archetype, or empty dict if none."""
    if app_state.active_archetype is None:
        return {}
    archetype = MissionArchetype(app_state.active_archetype)
    return MISSION_ARCHETYPES[archetype]


def alarm_per_kill(archetype: MissionArchetype) -> int:
    """Return the alarm penalty per kill for a given archetype."""
    if archetype == MissionArchetype.STEALTH:
        return 5
    return 0


def fast_clear_bonus_per_ten_seconds(archetype: MissionArchetype) -> int:
    """Return the CRED bonus per 10s under time limit for a given archetype."""
    if archetype == MissionArchetype.RACE:
        return 30
    return 0


def partial_pay_percent(archetype: MissionArchetype) -> int:
    """Return the per-objective partial pay percentage for a given archetype."""
    if archetype == MissionArchetype.EXTRACTION:
        return 30
    return 0


def friendly_node_hp(archetype: MissionArchetype) -> int:
    """Return the friendly node HP for a given archetype."""
    if archetype == MissionArchetype.DEFENSE:
        return 500
    return 0


def wave_count(archetype: MissionArchetype) -> int:
    """Return the wave count for a given archetype."""
    if archetype == MissionArchetype.DEFENSE:
        return 3
    return 0


__all__ = [
    "MISSION_ARCHETYPES",
    "MissionArchetype",
    "alarm_per_kill",
    "apply_archetype",
    "clear_archetype",
    "fast_clear_bonus_per_ten_seconds",
    "friendly_node_hp",
    "get_active_archetype",
    "get_archetype_info",
    "get_archetype_rules",
    "is_archetype_active",
    "partial_pay_percent",
    "wave_count",
]
