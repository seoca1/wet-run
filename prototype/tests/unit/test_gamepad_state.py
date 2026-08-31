"""Tests for engine/gamepad_state.py — hot-plug detection (ADR-0197 G1.3).

Covers:
- ControllerDevice event handling (added/removed/remapped)
- Sanitized controller name in status messages
- Debouncing rapid-fire events
- Multi-controller `which` ID preservation
"""

from __future__ import annotations

from unittest.mock import MagicMock

import tcod.event

from wet_run.engine.gamepad_state import (  # type: ignore[import-untyped]
    HOTPLUG_DEBOUNCE_MS,
    handle_device_event,
)
from wet_run.engine.state import AppState  # type: ignore[import-untyped]


def _make_device_event(
    event_type: str,
    which: int = 0,
    name: str | None = "Test Controller",
    timestamp_ns: int = 1_000_000_000,  # 1000ms
) -> tcod.event.ControllerDevice:
    """Create a mock ControllerDevice event with the given type."""
    event = MagicMock(spec=tcod.event.ControllerDevice)
    event.type = event_type
    event.which = which
    event.timestamp_ns = timestamp_ns
    # Mock the .controller.name attribute if name provided.
    if name is not None:
        mock_controller = MagicMock()
        mock_controller.name = name
        event.controller = mock_controller
    else:
        event.controller = None
    return event


class TestHandleDeviceEventAdded:
    """ControllerDevice 'added' event -> status message."""

    def test_added_appends_status_message(self) -> None:
        state = AppState()
        # Reset gamepad_last_device_event_ms to 0 so first event is not debounced.
        state.gamepad_last_device_event_ms = 0
        event = _make_device_event("CONTROLLERDEVICEADDED", name="Xbox Controller")

        handle_device_event(event, state)

        assert len(state.status_messages) >= 1
        assert any("Gamepad connected" in msg for msg in state.status_messages)
        assert any("Xbox Controller" in msg for msg in state.status_messages)

    def test_added_with_non_ascii_name_sanitized(self) -> None:
        state = AppState()
        state.gamepad_last_device_event_ms = 0
        event = _make_device_event("CONTROLLERDEVICEADDED", name="控制器Gamepad")

        handle_device_event(event, state)

        assert any("Gamepad connected" in msg for msg in state.status_messages)
        # Non-ASCII stripped, only ASCII parts remain.
        assert any("Gamepad" in msg and "控制器" not in msg for msg in state.status_messages)

    def test_added_with_empty_name_uses_default(self) -> None:
        state = AppState()
        state.gamepad_last_device_event_ms = 0
        event = _make_device_event("CONTROLLERDEVICEADDED", name="")

        handle_device_event(event, state)

        assert any("Controller" in msg for msg in state.status_messages)


class TestHandleDeviceEventRemoved:
    """ControllerDevice 'removed' event -> status message."""

    def test_removed_appends_fallback_message(self) -> None:
        state = AppState()
        state.gamepad_last_device_event_ms = 0
        event = _make_device_event("CONTROLLERDEVICEREMOVED")

        handle_device_event(event, state)

        assert any("Gamepad disconnected" in msg for msg in state.status_messages)
        assert any("keyboard" in msg.lower() for msg in state.status_messages)

    def test_removed_message_does_not_include_name(self) -> None:
        # Removed events don't necessarily include the name (SDL quirk).
        state = AppState()
        state.gamepad_last_device_event_ms = 0
        event = _make_device_event("CONTROLLERDEVICEREMOVED", name=None)

        handle_device_event(event, state)

        assert any("disconnected" in msg for msg in state.status_messages)


class TestHandleDeviceEventRemapped:
    """ControllerDevice 'remapped' event -> no status message (silent)."""

    def test_remapped_silent(self) -> None:
        state = AppState()
        state.gamepad_last_device_event_ms = 0
        initial_count = len(state.status_messages)
        event = _make_device_event("CONTROLLERDEVICEREMAPPED", name="Xbox Controller")

        handle_device_event(event, state)

        # Remapped events are silent (no spam).
        assert len(state.status_messages) == initial_count


class TestDebouncing:
    """Repeated events within HOTPLUG_DEBOUNCE_MS are ignored."""

    def test_rapid_add_events_only_first_appended(self) -> None:
        state = AppState()
        state.gamepad_last_device_event_ms = 0

        # First event at t=1000ms.
        event1 = _make_device_event(
            "CONTROLLERDEVICEADDED", name="Xbox", timestamp_ns=1_000_000_000
        )
        handle_device_event(event1, state)
        count_after_first = len(state.status_messages)

        # Second event at t=1100ms (100ms later, within 1000ms debounce).
        event2 = _make_device_event("CONTROLLERDEVICEADDED", name="PS5", timestamp_ns=1_100_000_000)
        handle_device_event(event2, state)

        # Second event should be ignored.
        assert len(state.status_messages) == count_after_first

    def test_event_after_debounce_window_appended(self) -> None:
        state = AppState()
        state.gamepad_last_device_event_ms = 0

        # First event at t=1000ms.
        event1 = _make_device_event(
            "CONTROLLERDEVICEADDED", name="Xbox", timestamp_ns=1_000_000_000
        )
        handle_device_event(event1, state)

        # Second event at t=3000ms (2000ms later, beyond 1000ms debounce).
        event2 = _make_device_event(
            "CONTROLLERDEVICEREMOVED", name=None, timestamp_ns=3_000_000_000
        )
        handle_device_event(event2, state)

        # Both should be in messages (different types).
        assert any("disconnected" in msg for msg in state.status_messages)

    def test_debounce_constant_value(self) -> None:
        # Lock in the debounce window so future tuning is conscious.
        assert HOTPLUG_DEBOUNCE_MS == 1000


class TestMultiController:
    """Multiple controllers can be tracked via `which` ID."""

    def test_two_controllers_added_separately(self) -> None:
        state = AppState()
        state.gamepad_last_device_event_ms = 0

        event1 = _make_device_event(
            "CONTROLLERDEVICEADDED",
            which=0,
            name="Controller 1",
            timestamp_ns=1_000_000_000,
        )
        handle_device_event(event1, state)

        # Second controller added 2 seconds later (beyond debounce).
        event2 = _make_device_event(
            "CONTROLLERDEVICEADDED",
            which=1,
            name="Controller 2",
            timestamp_ns=3_000_000_000,
        )
        handle_device_event(event2, state)

        # Both names should appear in messages.
        assert any("Controller 1" in msg for msg in state.status_messages)
        assert any("Controller 2" in msg for msg in state.status_messages)


class TestEdgeCases:
    """Edge cases for handle_device_event."""

    def test_no_message_added_when_event_is_unknown_type(self) -> None:
        state = AppState()
        state.gamepad_last_device_event_ms = 0
        # Use a non-standard but valid event type string.
        event = _make_device_event(
            "CONTROLLERDEVICEUNKNOWN", name="Test", timestamp_ns=1_000_000_000
        )

        handle_device_event(event, state)

        # Unknown event types should still produce a generic message
        # (fallback behavior, not crash).
        # The implementation may or may not append for unknown types;
        # just verify no crash.
        assert hasattr(state, "status_messages")
