"""Tests for Telemetry (ADR-0184)."""

from __future__ import annotations

import dataclasses

import pytest

from roguelike_sprawl.combat.telemetry import (
    TELEMETRY_EVENT_TYPES,
    aggregate_death_rates,
    aggregate_deck_distribution,
    aggregate_kill_counts,
    aggregate_mutator_choices,
    get_event_count,
    get_telemetry_event_types,
    is_opted_in,
    record_telemetry_event,
    start_telemetry_session,
)


def test_start_telemetry_session_default() -> None:
    session = start_telemetry_session()
    assert session.opt_in is False
    assert session.events == ()


def test_start_telemetry_session_opt_in() -> None:
    session = start_telemetry_session(opt_in=True)
    assert session.opt_in is True


def test_record_event_opted_in() -> None:
    session = start_telemetry_session(opt_in=True)
    session = record_telemetry_event(session, "death", {"ice_type": "wintermute"})
    assert len(session.events) == 1


def test_record_event_not_opted_in_no_op() -> None:
    session = start_telemetry_session(opt_in=False)
    session = record_telemetry_event(session, "death", {"ice_type": "wintermute"})
    assert len(session.events) == 0


def test_record_event_invalid_type() -> None:
    session = start_telemetry_session(opt_in=True)
    session = record_telemetry_event(session, "invalid_type")
    assert len(session.events) == 0


def test_is_opted_in() -> None:
    assert not is_opted_in(start_telemetry_session(opt_in=False))
    assert is_opted_in(start_telemetry_session(opt_in=True))


def test_get_event_count() -> None:
    session = start_telemetry_session(opt_in=True)
    session = record_telemetry_event(session, "death")
    session = record_telemetry_event(session, "kill")
    assert get_event_count(session) == 2


def test_aggregate_death_rates() -> None:
    session = start_telemetry_session(opt_in=True)
    session = record_telemetry_event(session, "death", {"ice_type": "wintermute"})
    session = record_telemetry_event(session, "death", {"ice_type": "wintermute"})
    session = record_telemetry_event(session, "death", {"ice_type": "goliath"})
    rates = aggregate_death_rates(session)
    assert rates["wintermute"] == 2
    assert rates["goliath"] == 1


def test_aggregate_kill_counts() -> None:
    session = start_telemetry_session(opt_in=True)
    session = record_telemetry_event(session, "kill", {"ice_type": "watchdog"})
    session = record_telemetry_event(session, "kill", {"ice_type": "watchdog"})
    session = record_telemetry_event(session, "kill", {"ice_type": "standard"})
    counts = aggregate_kill_counts(session)
    assert counts["watchdog"] == 2
    assert counts["standard"] == 1


def test_aggregate_deck_distribution() -> None:
    session = start_telemetry_session(opt_in=True)
    session = record_telemetry_event(session, "deck_chosen", {"deck": "standard"})
    session = record_telemetry_event(session, "deck_chosen", {"deck": "light"})
    dist = aggregate_deck_distribution(session)
    assert dist["standard"] == 1
    assert dist["light"] == 1


def test_aggregate_mutator_choices() -> None:
    session = start_telemetry_session(opt_in=True)
    session = record_telemetry_event(session, "mutator_chosen", {"mutator": "low_hp"})
    session = record_telemetry_event(session, "mutator_chosen", {"mutator": "low_hp"})
    session = record_telemetry_event(session, "mutator_chosen", {"mutator": "no_heal"})
    counts = aggregate_mutator_choices(session)
    assert counts["low_hp"] == 2
    assert counts["no_heal"] == 1


def test_get_telemetry_event_types() -> None:
    types = get_telemetry_event_types()
    assert "death" in types
    assert "kill" in types
    assert "deck_chosen" in types


def test_session_immutable() -> None:
    session = start_telemetry_session(opt_in=True)
    try:
        session.opt_in = False  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_event_immutable() -> None:
    session = start_telemetry_session(opt_in=True)
    session = record_telemetry_event(session, "death")
    event = session.events[0]
    try:
        event.event_type = "modified"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_unique_session_ids() -> None:
    s1 = start_telemetry_session()
    s2 = start_telemetry_session()
    assert s1.session_id != s2.session_id


def test_aggregate_empty_session() -> None:
    session = start_telemetry_session()
    assert aggregate_death_rates(session) == {}
    assert aggregate_kill_counts(session) == {}
    assert aggregate_deck_distribution(session) == {}
    assert aggregate_mutator_choices(session) == {}


def test_event_type_count() -> None:
    assert len(TELEMETRY_EVENT_TYPES) >= 5
