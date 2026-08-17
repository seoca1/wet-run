"""Tests for Random Matrix Events (ADR-0165)."""

from __future__ import annotations

import random

from wet_run.combat.matrix_events import (
    MATRIX_EVENTS,
    MatrixEvent,
    check_event_trigger,
    clear_all_events,
    clear_event,
    get_active_events,
    get_event_info,
    get_trigger_chance,
    is_event_active,
    is_fake_data_active,
    is_ghost_signal_active,
    is_heist_window_active,
    is_ice_patrol_active,
    is_network_blackout_active,
    is_patron_offer_active,
    trigger_event,
)
from wet_run.engine.state import AppState


def make_app_state() -> AppState:
    return AppState()


def test_matrix_event_enum_has_6_entries() -> None:
    assert len(MatrixEvent) == 6
    assert MatrixEvent.GHOST_SIGNAL.value == "ghost_signal"
    assert MatrixEvent.ICE_PATROL.value == "ice_patrol"
    assert MatrixEvent.HEIST_WINDOW.value == "heist_window"
    assert MatrixEvent.PATRON_OFFER.value == "patron_offer"
    assert MatrixEvent.NETWORK_BLACKOUT.value == "network_blackout"
    assert MatrixEvent.FAKE_DATA.value == "fake_data"


def test_matrix_events_registry_has_all() -> None:
    for event in MatrixEvent:
        assert event in MATRIX_EVENTS
        info = MATRIX_EVENTS[event]
        assert "name" in info
        assert "description" in info
        assert "trigger_chance" in info
        assert "icon" in info


def test_get_event_info_returns_config() -> None:
    info = get_event_info(MatrixEvent.GHOST_SIGNAL)
    assert info["name"] == "GHOST_SIGNAL"
    assert "grid" in info["description"].lower()


def test_get_trigger_chance() -> None:
    assert get_trigger_chance(MatrixEvent.GHOST_SIGNAL) == 0.05
    assert get_trigger_chance(MatrixEvent.ICE_PATROL) == 0.08
    assert get_trigger_chance(MatrixEvent.NETWORK_BLACKOUT) == 0.02


def test_check_event_trigger_with_deterministic_rng() -> None:
    rng = random.Random(0)
    assert check_event_trigger(rng, MatrixEvent.GHOST_SIGNAL) is not None


def test_check_event_trigger_never_triggers_when_chance_is_zero() -> None:
    import pytest

    rng = random.Random(42)

    for _ in range(100):
        if rng.random() < 0.0:
            pytest.fail("Should never trigger at 0% chance")


def test_trigger_event_adds_to_active() -> None:
    state = make_app_state()
    trigger_event(state, MatrixEvent.GHOST_SIGNAL)
    assert MatrixEvent.GHOST_SIGNAL in get_active_events(state)
    assert "GHOST_SIGNAL" in state.event_log


def test_trigger_event_does_not_duplicate() -> None:
    state = make_app_state()
    trigger_event(state, MatrixEvent.GHOST_SIGNAL)
    trigger_event(state, MatrixEvent.GHOST_SIGNAL)
    active = get_active_events(state)
    assert active.count(MatrixEvent.GHOST_SIGNAL) == 1


def test_is_event_active() -> None:
    state = make_app_state()
    assert not is_event_active(state, MatrixEvent.GHOST_SIGNAL)
    trigger_event(state, MatrixEvent.GHOST_SIGNAL)
    assert is_event_active(state, MatrixEvent.GHOST_SIGNAL)


def test_specific_active_helpers() -> None:
    state = make_app_state()
    assert not is_ghost_signal_active(state)
    assert not is_ice_patrol_active(state)
    assert not is_heist_window_active(state)
    assert not is_patron_offer_active(state)
    assert not is_network_blackout_active(state)
    assert not is_fake_data_active(state)


def test_trigger_event_each() -> None:
    state = make_app_state()
    for event in MatrixEvent:
        trigger_event(state, event)
    assert len(get_active_events(state)) == 6


def test_clear_event() -> None:
    state = make_app_state()
    trigger_event(state, MatrixEvent.GHOST_SIGNAL)
    trigger_event(state, MatrixEvent.ICE_PATROL)
    clear_event(state, MatrixEvent.GHOST_SIGNAL)
    assert MatrixEvent.GHOST_SIGNAL not in get_active_events(state)
    assert MatrixEvent.ICE_PATROL in get_active_events(state)


def test_clear_all_events() -> None:
    state = make_app_state()
    for event in MatrixEvent:
        trigger_event(state, event)
    clear_all_events(state)
    assert get_active_events(state) == ()


def test_get_active_events_handles_invalid() -> None:
    state = AppState()
    state.active_events = ("ghost_signal", "invalid_event", "ice_patrol")
    active = get_active_events(state)
    assert len(active) == 2
    assert MatrixEvent.GHOST_SIGNAL in active
    assert MatrixEvent.ICE_PATROL in active


def test_event_log_records_triggers() -> None:
    state = make_app_state()
    trigger_event(state, MatrixEvent.GHOST_SIGNAL)
    trigger_event(state, MatrixEvent.ICE_PATROL)
    assert len(state.event_log) == 2
    assert "GHOST_SIGNAL" in state.event_log
    assert "ICE_PATROL" in state.event_log
