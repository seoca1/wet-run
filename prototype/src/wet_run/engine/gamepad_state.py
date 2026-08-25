"""Gamepad hot-plug detection (ADR-0197 G1.3).

Handles ControllerDevice events from SDL (controller added/removed/remapped).
Appends status messages to AppState so players see connect/disconnect toasts.

Architecture:
    ControllerDevice event -> handle_device_event()
        -> sanitize_controller_name()
        -> state.status_messages.append(...)

Safety:
    - Hot-plug toasts are debounced (no spam on Windows 10 polling).
    - Controller names sanitized to ASCII printable (some MFi controllers
      include garbage Unicode).
    - Status messages auto-truncated by StatusMessageList (state.py).
"""

from __future__ import annotations

import tcod.event

from . import gamepad as _gamepad
from .state import AppState

# Debounce interval (ms) — ignore repeated device events within this window.
HOTPLUG_DEBOUNCE_MS = 1000


def handle_device_event(event: tcod.event.ControllerDevice, state: AppState) -> None:
    """Handle a ControllerDevice event from tcod.

    Appends a status message based on event.type:
        CONTROLLERDEVICEADDED    -> ">>> Gamepad connected: <name>"
        CONTROLLERDEVICEREMOVED  -> ">>> Gamepad disconnected (falling back to keyboard)"
        CONTROLLERDEVICEREMAPPED -> (silent; just refresh internal state)

    Debounces by ignoring events within HOTPLUG_DEBOUNCE_MS of the last
    device event (Windows polls controllers frequently).
    """
    # Debounce: skip if same event type fired recently.
    # Use timestamp_ns / 1_000_000 for ms.
    now_ms = (event.timestamp_ns or 0) // 1_000_000
    last_ms = getattr(state, "gamepad_last_device_event_ms", 0)
    if last_ms and (now_ms - last_ms) < HOTPLUG_DEBOUNCE_MS:
        return
    state.gamepad_last_device_event_ms = now_ms

    raw_name = getattr(event, "name", None) or _get_controller_name(event)
    safe_name = _gamepad.sanitize_controller_name(raw_name)

    if event.type == "CONTROLLERDEVICEADDED":
        state.status_messages.append(f">>> Gamepad connected: {safe_name}")
    elif event.type == "CONTROLLERDEVICEREMOVED":
        state.status_messages.append(
            ">>> Gamepad disconnected (falling back to keyboard)"
        )
    elif event.type == "CONTROLLERDEVICEREMAPPED":
        # Silent — just refresh; do not spam status panel.
        return
    else:
        # Unknown event type — log generically.
        state.status_messages.append(
            f">>> Gamepad event: {event.type} ({safe_name})"
        )


def _get_controller_name(event: tcod.event.ControllerDevice) -> str | None:
    """Best-effort controller name extraction.

    Falls back through several SDL properties:
        1. event.controller.name (if available via tcod)
        2. None (caller will use 'Controller' default)

    Args:
        event: ControllerDevice event.

    Returns:
        Controller name string or None if unavailable.
    """
    try:
        controller = event.controller
        if controller is not None:
            name = getattr(controller, "name", None)
            if name is not None:
                return str(name)
    except Exception:
        pass
    return None


__all__ = ["HOTPLUG_DEBOUNCE_MS", "handle_device_event"]
