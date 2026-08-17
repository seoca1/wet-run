"""Run Replay System (ADR-0182).

Record key events during a run, then play them back as a cinematic.
Enables sharing and learning from runs.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReplayEvent:
    """A single recorded event in a run replay."""

    timestamp_ms: int
    event_type: str
    data: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunReplay:
    """A complete run replay."""

    run_id: str
    character_id: str
    events: tuple[ReplayEvent, ...]
    total_duration_ms: int


def start_replay(character_id: str) -> RunReplay:
    """Start a new empty replay for a character."""
    return RunReplay(
        run_id=str(uuid.uuid4()),
        character_id=character_id,
        events=(),
        total_duration_ms=0,
    )


def record_event(
    replay: RunReplay,
    event_type: str,
    data: dict[str, object] | None = None,
    timestamp_ms: int = 0,
) -> RunReplay:
    """Record a new event in the replay."""
    new_event = ReplayEvent(
        timestamp_ms=timestamp_ms,
        event_type=event_type,
        data=data or {},
    )
    return RunReplay(
        run_id=replay.run_id,
        character_id=replay.character_id,
        events=replay.events + (new_event,),
        total_duration_ms=max(replay.total_duration_ms, timestamp_ms),
    )


def get_replay_events_by_type(replay: RunReplay, event_type: str) -> tuple[ReplayEvent, ...]:
    """Return all events of a given type."""
    return tuple(e for e in replay.events if e.event_type == event_type)


def get_replay_duration(replay: RunReplay) -> int:
    """Return the total duration of the replay in ms."""
    return replay.total_duration_ms


def get_replay_event_count(replay: RunReplay) -> int:
    """Return the number of events in the replay."""
    return len(replay.events)


def get_replay_event_types(replay: RunReplay) -> tuple[str, ...]:
    """Return the unique event types in the replay."""
    return tuple(sorted({e.event_type for e in replay.events}))


def export_replay_json(replay: RunReplay) -> str:
    """Export replay as JSON string."""
    data = {
        "run_id": replay.run_id,
        "character_id": replay.character_id,
        "events": [
            {
                "timestamp_ms": e.timestamp_ms,
                "event_type": e.event_type,
                "data": e.data,
            }
            for e in replay.events
        ],
        "total_duration_ms": replay.total_duration_ms,
    }
    return json.dumps(data)


def import_replay_json(json_str: str) -> RunReplay:
    """Import replay from JSON string."""
    data = json.loads(json_str)
    return RunReplay(
        run_id=data["run_id"],
        character_id=data["character_id"],
        events=tuple(
            ReplayEvent(
                timestamp_ms=e["timestamp_ms"],
                event_type=e["event_type"],
                data=e.get("data", {}),
            )
            for e in data["events"]
        ),
        total_duration_ms=data["total_duration_ms"],
    )


def get_replay_event_at(replay: RunReplay, timestamp_ms: int) -> ReplayEvent | None:
    """Return the event at a given timestamp."""
    for e in replay.events:
        if e.timestamp_ms == timestamp_ms:
            return e
    return None


__all__ = [
    "ReplayEvent",
    "RunReplay",
    "export_replay_json",
    "get_replay_duration",
    "get_replay_event_at",
    "get_replay_event_count",
    "get_replay_event_types",
    "get_replay_events_by_type",
    "import_replay_json",
    "record_event",
    "start_replay",
]
