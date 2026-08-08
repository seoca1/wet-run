"""Tests for Run Replay System (ADR-0182)."""

from __future__ import annotations

import dataclasses

import pytest

from roguelike_sprawl.combat.replay import (
    export_replay_json,
    get_replay_duration,
    get_replay_event_at,
    get_replay_event_count,
    get_replay_event_types,
    get_replay_events_by_type,
    import_replay_json,
    record_event,
    start_replay,
)


def test_start_replay() -> None:
    replay = start_replay("construct")
    assert replay.character_id == "construct"
    assert replay.events == ()


def test_record_event() -> None:
    replay = start_replay("construct")
    replay = record_event(replay, "combat_start", {"enemy": "watchdog"})
    assert len(replay.events) == 1
    assert replay.events[0].event_type == "combat_start"


def test_record_multiple_events() -> None:
    replay = start_replay("construct")
    replay = record_event(replay, "combat_start", timestamp_ms=0)
    replay = record_event(replay, "skill_used", {"skill": "probe"}, timestamp_ms=1000)
    replay = record_event(replay, "damage", {"amount": 10}, timestamp_ms=2000)
    assert len(replay.events) == 3


def test_get_replay_events_by_type() -> None:
    replay = start_replay("construct")
    replay = record_event(replay, "combat_start", timestamp_ms=0)
    replay = record_event(replay, "damage", timestamp_ms=1000)
    replay = record_event(replay, "damage", timestamp_ms=2000)
    damages = get_replay_events_by_type(replay, "damage")
    assert len(damages) == 2


def test_get_replay_duration() -> None:
    replay = start_replay("construct")
    replay = record_event(replay, "test", timestamp_ms=5000)
    assert get_replay_duration(replay) == 5000


def test_get_replay_event_count() -> None:
    replay = start_replay("construct")
    replay = record_event(replay, "test")
    replay = record_event(replay, "test")
    assert get_replay_event_count(replay) == 2


def test_get_replay_event_types() -> None:
    replay = start_replay("construct")
    replay = record_event(replay, "combat_start")
    replay = record_event(replay, "damage")
    replay = record_event(replay, "death")
    types = get_replay_event_types(replay)
    assert "combat_start" in types
    assert "damage" in types
    assert "death" in types


def test_export_import_json() -> None:
    replay = start_replay("construct")
    replay = record_event(replay, "combat_start", {"enemy": "watchdog"}, timestamp_ms=1000)
    json_str = export_replay_json(replay)
    replay2 = import_replay_json(json_str)
    assert replay2.run_id == replay.run_id
    assert replay2.character_id == replay.character_id
    assert len(replay2.events) == 1


def test_get_replay_event_at() -> None:
    replay = start_replay("construct")
    replay = record_event(replay, "test", timestamp_ms=5000)
    event = get_replay_event_at(replay, 5000)
    assert event is not None
    assert event.timestamp_ms == 5000


def test_get_replay_event_at_nonexistent() -> None:
    replay = start_replay("construct")
    assert get_replay_event_at(replay, 9999) is None


def test_replay_immutable() -> None:
    replay = start_replay("construct")
    try:
        replay.character_id = "modified"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_event_immutable() -> None:
    replay = start_replay("construct")
    replay = record_event(replay, "test")
    event = replay.events[0]
    try:
        event.event_type = "modified"  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_unique_run_ids() -> None:
    r1 = start_replay("character")
    r2 = start_replay("character")
    assert r1.run_id != r2.run_id


def test_record_event_with_data() -> None:
    replay = start_replay("construct")
    replay = record_event(replay, "damage", {"amount": 50, "source": "probe"})
    event = replay.events[0]
    assert event.data["amount"] == 50
    assert event.data["source"] == "probe"


def test_export_json_roundtrip() -> None:
    replay = start_replay("construct")
    replay = record_event(replay, "combat_start", {"seed": 42})
    replay = record_event(replay, "victory", {"score": 1000})
    json_str = export_replay_json(replay)
    replay2 = import_replay_json(json_str)
    assert len(replay2.events) == 2
    assert replay2.events[0].data["seed"] == 42
