"""Telemetry Integration (ADR-0184, Round 5).

Wires combat/telemetry.py event tracking into the game state.
Provides:
- TelemetryConfig: opt-in/opt-out settings
- TelemetryIntegrator: high-level event recording
- Aggregation helpers for player behavior analysis
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from .telemetry import (
    TELEMETRY_EVENT_TYPES,
    TelemetryEvent,
    TelemetrySession,
    aggregate_death_rates,
    aggregate_deck_distribution,
    aggregate_kill_counts,
    aggregate_mutator_choices,
    get_event_count,
    is_opted_in,
    record_telemetry_event,
    start_telemetry_session,
)


@dataclass(frozen=True, slots=True)
class TelemetryConfig:
    """Telemetry configuration for a game session."""

    enabled: bool = False
    session_id: str = ""
    opted_in_at_start: bool = False


class TelemetryIntegrator:
    """High-level telemetry wrapper for game integration."""

    def __init__(self, config: TelemetryConfig | None = None) -> None:
        self._session: TelemetrySession = start_telemetry_session(
            opt_in=config.opted_in_at_start if config else False
        )
        self._config = config or TelemetryConfig()

    @property
    def session(self) -> TelemetrySession:
        """Return the current session."""
        return self._session

    @property
    def config(self) -> TelemetryConfig:
        """Return the current configuration."""
        return self._config

    def is_enabled(self) -> bool:
        """Return True if telemetry is enabled."""
        return is_opted_in(self._session)

    def record(
        self,
        event_type: str,
        data: dict | None = None,
        timestamp_ms: int | None = None,
    ) -> TelemetrySession:
        """Record a telemetry event."""
        if event_type not in TELEMETRY_EVENT_TYPES:
            return self._session
        ts = timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
        self._session = record_telemetry_event(
            self._session, event_type, data, ts
        )
        return self._session

    def record_death(self, ice_type: str, turn: int = 0) -> None:
        """Record a death event."""
        self.record("death", {"ice_type": ice_type, "turn": turn})

    def record_kill(self, ice_kind: str, turn: int = 0) -> None:
        """Record an ICE kill event (called from combat state when target HP <= 0)."""
        self.record("kill", {"ice_kind": ice_kind, "turn": turn})

    def record_deck_chosen(self, deck_size: str) -> None:
        """Record a deck choice event."""
        self.record("deck_chosen", {"deck": deck_size})

    def record_mutator_chosen(self, mutator: str) -> None:
        """Record a mutator choice event."""
        self.record("mutator_chosen", {"mutator": mutator})

    def record_boss_reached(self, boss_id: str) -> None:
        """Record a boss reach event."""
        self.record("boss_reached", {"boss": boss_id})

    def record_mission_completed(self, mission_id: str, grade: int = 0) -> None:
        """Record a mission completion event."""
        self.record("mission_completed", {"mission": mission_id, "grade": grade})

    def record_run_completed(self, run_id: str, grade: int = 0) -> None:
        """Record a run completion event."""
        self.record("run_completed", {"run": run_id, "grade": grade})

    def get_event_count(self) -> int:
        """Return total number of events recorded."""
        return get_event_count(self._session)

    def aggregate_death_rates(self) -> dict[str, int]:
        """Get death rates by ICE type."""
        return aggregate_death_rates(self._session)

    def aggregate_kill_counts(self) -> dict[str, int]:
        """Get kill counts by ICE type."""
        return aggregate_kill_counts(self._session)

    def aggregate_deck_distribution(self) -> dict[str, int]:
        """Get deck choice distribution."""
        return aggregate_deck_distribution(self._session)

    def aggregate_mutator_choices(self) -> dict[str, int]:
        """Get mutator choice distribution."""
        return aggregate_mutator_choices(self._session)

    def get_supported_events(self) -> tuple[str, ...]:
        """Return all supported telemetry event types."""
        return TELEMETRY_EVENT_TYPES


def record_kill(ice_kind: str, turn: int = 0) -> None:
    """Module-level convenience for combat state integration.

    Wired to the active TelemetryIntegrator in a future Phase 14 integration.
    Currently a no-op stub satisfying the import contract.
    """
    del ice_kind, turn


def should_record_event(event_type: str) -> bool:
    """Return True if event_type is supported for telemetry."""
    return event_type in TELEMETRY_EVENT_TYPES


def make_event(event_type: str, data: dict[str, object] | None = None) -> TelemetryEvent:
    """Create a TelemetryEvent with current timestamp."""
    return TelemetryEvent(
        timestamp_ms=int(time.time() * 1000),
        event_type=event_type,
        data=data or {},
    )


__all__ = [
    "TelemetryConfig",
    "TelemetryIntegrator",
    "make_event",
    "should_record_event",
]
