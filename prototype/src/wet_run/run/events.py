"""Stage event system — hooks for UI/sound/narrative on stage transitions.

This module provides an event bus for stage lifecycle events:
- on_enter: when entering a stage
- on_exit: when leaving a stage
- on_complete: when a stage's objective is satisfied (just before advance)
- on_failed: when the run transitions to FAILED

Events can be subscribed to globally (all stages) or per-stage. Handlers
are called in subscription order. The system is fire-and-forget — handlers
should not raise.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from .state import RunState, Stage


class StageEventKind(StrEnum):
    """Types of stage lifecycle events."""

    ENTER = "enter"  # Stage just entered
    EXIT = "exit"  # Stage just left (about to advance)
    COMPLETE = "complete"  # Stage objective satisfied
    FAILED = "failed"  # Run failed
    ADVANCE = "advance"  # Stage transition just happened


@dataclass(frozen=True, slots=True)
class StageEvent:
    """A single stage event.

    Attributes:
        kind: Type of event.
        run_state: The current RunState.
        from_stage: The stage we're leaving (None for ENTER from initial).
        to_stage: The stage we're entering (None for EXIT to terminal).
        timestamp_ms: When the event was created.
    """

    kind: StageEventKind
    run_state: RunState
    from_stage: Stage | None
    to_stage: Stage | None
    timestamp_ms: int = 0


# Type alias for event handlers
StageEventHandler = Callable[[StageEvent], None]


@dataclass
class StageEventBus:
    """Pub/sub bus for stage events.

    Handlers can be subscribed globally (all events) or filtered to
    a specific event kind and/or stage.
    """

    _global_handlers: list[StageEventHandler] = field(default_factory=list)
    _kind_handlers: dict[StageEventKind, list[StageEventHandler]] = field(default_factory=dict)
    _stage_handlers: dict[tuple[StageEventKind, Stage], list[StageEventHandler]] = field(
        default_factory=dict
    )

    def subscribe(self, handler: StageEventHandler) -> None:
        """Subscribe to ALL events (any kind, any stage)."""
        self._global_handlers.append(handler)

    def subscribe_kind(self, kind: StageEventKind, handler: StageEventHandler) -> None:
        """Subscribe to all events of a specific kind."""
        self._kind_handlers.setdefault(kind, []).append(handler)

    def subscribe_stage(
        self, kind: StageEventKind, stage: Stage, handler: StageEventHandler
    ) -> None:
        """Subscribe to events of a specific kind for a specific stage."""
        key = (kind, stage)
        self._stage_handlers.setdefault(key, []).append(handler)

    def unsubscribe(self, handler: StageEventHandler) -> None:
        """Remove a handler from all subscriptions."""
        if handler in self._global_handlers:
            self._global_handlers.remove(handler)
        for kind_list in self._kind_handlers.values():
            if handler in kind_list:
                kind_list.remove(handler)
        for stage_list in self._stage_handlers.values():
            if handler in stage_list:
                stage_list.remove(handler)

    def emit(self, event: StageEvent) -> None:
        """Emit an event to all subscribers.

        Handlers are called in this order:
        1. Stage-specific handlers (kind + stage)
        2. Kind handlers (kind)
        3. Global handlers

        Exceptions in handlers are caught and ignored to prevent one
        bad handler from breaking the whole flow.
        """
        handlers: list[StageEventHandler] = []

        # Stage-specific: ENTER uses to_stage, others use from_stage
        if event.kind is StageEventKind.ENTER and event.to_stage is not None:
            key: tuple[StageEventKind, Stage] = (event.kind, event.to_stage)
            handlers.extend(self._stage_handlers.get(key, []))
        elif event.from_stage is not None:
            key = (event.kind, event.from_stage)
            handlers.extend(self._stage_handlers.get(key, []))

        # Kind handlers
        handlers.extend(self._kind_handlers.get(event.kind, []))

        # Global handlers
        handlers.extend(self._global_handlers)

        for handler in handlers:
            try:
                handler(event)
            except Exception:  # noqa: BLE001
                # Silently ignore handler errors to keep event flow alive
                pass

    def clear(self) -> None:
        """Remove all subscriptions."""
        self._global_handlers.clear()
        self._kind_handlers.clear()
        self._stage_handlers.clear()


# --- Singleton ---


_DEFAULT_BUS: StageEventBus | None = None


def get_event_bus() -> StageEventBus:
    """Return the default stage event bus singleton."""
    global _DEFAULT_BUS
    if _DEFAULT_BUS is None:
        _DEFAULT_BUS = StageEventBus()
    return _DEFAULT_BUS


def reset_event_bus() -> None:
    """Reset the default event bus (for testing)."""
    global _DEFAULT_BUS
    _DEFAULT_BUS = None
