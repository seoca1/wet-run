"""Random Matrix Events system (ADR-0165).

6 mid-run surprises that fire during node encounters.
"""

from __future__ import annotations

import random
from enum import StrEnum

from ..engine.state import AppState


class MatrixEvent(StrEnum):
    """Random matrix events that fire mid-run."""

    GHOST_SIGNAL = "ghost_signal"
    ICE_PATROL = "ice_patrol"
    HEIST_WINDOW = "heist_window"
    PATRON_OFFER = "patron_offer"
    NETWORK_BLACKOUT = "network_blackout"
    FAKE_DATA = "fake_data"


MATRIX_EVENTS: dict[MatrixEvent, dict[str, str | float]] = {
    MatrixEvent.GHOST_SIGNAL: {
        "name": "GHOST_SIGNAL",
        "description": "The grid remembers. Free info about next ICE.",
        "trigger_chance": 0.05,
        "icon": "ghost_signal",
    },
    MatrixEvent.ICE_PATROL: {
        "name": "ICE_PATROL",
        "description": "Extra ICE spawns. 1v2.",
        "trigger_chance": 0.08,
        "icon": "ice_patrol",
    },
    MatrixEvent.HEIST_WINDOW: {
        "name": "HEIST_WINDOW",
        "description": "Next 3 nodes give 2x CRED.",
        "trigger_chance": 0.03,
        "icon": "heist_window",
    },
    MatrixEvent.PATRON_OFFER: {
        "name": "PATRON_OFFER",
        "description": "Buy intel mid-run. CRED for hints.",
        "trigger_chance": 0.05,
        "icon": "patron_offer",
    },
    MatrixEvent.NETWORK_BLACKOUT: {
        "name": "NETWORK_BLACKOUT",
        "description": "Alarm paused for 30s.",
        "trigger_chance": 0.02,
        "icon": "network_blackout",
    },
    MatrixEvent.FAKE_DATA: {
        "name": "FAKE_DATA",
        "description": "Data node is rigged. Alarm spike.",
        "trigger_chance": 0.05,
        "icon": "fake_data",
    },
}


def get_event_info(event: MatrixEvent) -> dict[str, str | float]:
    """Return display info for an event."""
    return MATRIX_EVENTS[event]


def get_trigger_chance(event: MatrixEvent) -> float:
    """Return the trigger probability for an event."""
    return float(MATRIX_EVENTS[event]["trigger_chance"])


def check_event_trigger(rng: random.Random, event: MatrixEvent) -> bool:
    """Check if a matrix event triggers given RNG."""
    chance = get_trigger_chance(event)
    return rng.random() < chance


def trigger_event(app_state: AppState, event: MatrixEvent) -> None:
    """Trigger a matrix event and add to active events."""
    info = MATRIX_EVENTS[event]
    event_name = str(info["name"])
    if event not in app_state.active_events:
        new_events = app_state.active_events + (event.value,)
        app_state.active_events = new_events
    app_state.event_log.append(event_name)


def get_active_events(app_state: AppState) -> tuple[MatrixEvent, ...]:
    """Return active matrix events."""
    result: list[MatrixEvent] = []
    for event_str in app_state.active_events:
        try:
            result.append(MatrixEvent(event_str))
        except ValueError:
            pass
    return tuple(result)


def is_event_active(app_state: AppState, event: MatrixEvent) -> bool:
    """Check if an event is currently active."""
    return event.value in app_state.active_events


def is_heist_window_active(app_state: AppState) -> bool:
    """Return True if HEIST_WINDOW is active (CRED × 2)."""
    return is_event_active(app_state, MatrixEvent.HEIST_WINDOW)


def is_network_blackout_active(app_state: AppState) -> bool:
    """Return True if NETWORK_BLACKOUT is active (alarm paused)."""
    return is_event_active(app_state, MatrixEvent.NETWORK_BLACKOUT)


def is_ice_patrol_active(app_state: AppState) -> bool:
    """Return True if ICE_PATROL is active (extra ICE spawns)."""
    return is_event_active(app_state, MatrixEvent.ICE_PATROL)


def is_fake_data_active(app_state: AppState) -> bool:
    """Return True if FAKE_DATA is active (alarm spike on data)."""
    return is_event_active(app_state, MatrixEvent.FAKE_DATA)


def is_ghost_signal_active(app_state: AppState) -> bool:
    """Return True if GHOST_SIGNAL is active (free intel)."""
    return is_event_active(app_state, MatrixEvent.GHOST_SIGNAL)


def is_patron_offer_active(app_state: AppState) -> bool:
    """Return True if PATRON_OFFER is active (buy intel)."""
    return is_event_active(app_state, MatrixEvent.PATRON_OFFER)


def clear_event(app_state: AppState, event: MatrixEvent) -> None:
    """Clear a specific event from active list."""
    remaining = tuple(e for e in app_state.active_events if e != event.value)
    app_state.active_events = remaining


def clear_all_events(app_state: AppState) -> None:
    """Clear all active events."""
    app_state.active_events = ()


__all__ = [
    "MATRIX_EVENTS",
    "MatrixEvent",
    "check_event_trigger",
    "clear_all_events",
    "clear_event",
    "get_active_events",
    "get_event_info",
    "get_trigger_chance",
    "is_event_active",
    "is_fake_data_active",
    "is_ghost_signal_active",
    "is_heist_window_active",
    "is_ice_patrol_active",
    "is_network_blackout_active",
    "is_patron_offer_active",
    "trigger_event",
]
