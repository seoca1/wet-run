"""Telemetry (ADR-0184).

Anonymous player behavior tracking for balance tuning.
Opt-in only. Aggregated data only — no per-user data.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

TELEMETRY_EVENT_TYPES: tuple[str, ...] = (
    "death",
    "kill",
    "deck_chosen",
    "mutator_chosen",
    "boss_reached",
    "mission_completed",
    "run_completed",
)


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    """A single telemetry event."""

    timestamp_ms: int
    event_type: str
    data: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TelemetrySession:
    """A telemetry session — opt-in only."""

    session_id: str
    events: tuple[TelemetryEvent, ...] = ()
    opt_in: bool = False


def start_telemetry_session(opt_in: bool = False) -> TelemetrySession:
    """Start a new telemetry session."""
    return TelemetrySession(
        session_id=str(uuid.uuid4()),
        events=(),
        opt_in=opt_in,
    )


def record_telemetry_event(
    session: TelemetrySession,
    event_type: str,
    data: dict[str, object] | None = None,
    timestamp_ms: int = 0,
) -> TelemetrySession:
    """Record a telemetry event. No-op if not opted in."""
    if not session.opt_in:
        return session
    if event_type not in TELEMETRY_EVENT_TYPES:
        return session
    event = TelemetryEvent(
        timestamp_ms=timestamp_ms,
        event_type=event_type,
        data=data or {},
    )
    return TelemetrySession(
        session_id=session.session_id,
        events=session.events + (event,),
        opt_in=True,
    )


def is_opted_in(session: TelemetrySession) -> bool:
    """Return True if the session is opted in."""
    return session.opt_in


def get_event_count(session: TelemetrySession) -> int:
    """Return the number of events recorded."""
    return len(session.events)


def aggregate_death_rates(session: TelemetrySession) -> dict[str, int]:
    """Return count of deaths by ICE type."""
    counts: dict[str, int] = {}
    for event in session.events:
        if event.event_type == "death":
            ice_type = str(event.data.get("ice_type", "unknown"))
            counts[ice_type] = counts.get(ice_type, 0) + 1
    return counts


def aggregate_kill_counts(session: TelemetrySession) -> dict[str, int]:
    """Return count of kills by ICE type."""
    counts: dict[str, int] = {}
    for event in session.events:
        if event.event_type == "kill":
            ice_type = str(event.data.get("ice_type", "unknown"))
            counts[ice_type] = counts.get(ice_type, 0) + 1
    return counts


def aggregate_deck_distribution(session: TelemetrySession) -> dict[str, int]:
    """Return count of deck choices."""
    counts: dict[str, int] = {}
    for event in session.events:
        if event.event_type == "deck_chosen":
            deck = str(event.data.get("deck", "unknown"))
            counts[deck] = counts.get(deck, 0) + 1
    return counts


def aggregate_mutator_choices(session: TelemetrySession) -> dict[str, int]:
    """Return count of mutator choices."""
    counts: dict[str, int] = {}
    for event in session.events:
        if event.event_type == "mutator_chosen":
            mutator = str(event.data.get("mutator", "unknown"))
            counts[mutator] = counts.get(mutator, 0) + 1
    return counts


def get_telemetry_event_types() -> tuple[str, ...]:
    """Return all supported telemetry event types."""
    return TELEMETRY_EVENT_TYPES


__all__ = [
    "TELEMETRY_EVENT_TYPES",
    "TelemetryEvent",
    "TelemetrySession",
    "aggregate_death_rates",
    "aggregate_deck_distribution",
    "aggregate_kill_counts",
    "aggregate_mutator_choices",
    "get_event_count",
    "get_telemetry_event_types",
    "is_opted_in",
    "record_telemetry_event",
    "start_telemetry_session",
]
