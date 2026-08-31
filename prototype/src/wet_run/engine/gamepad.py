"""Gamepad / controller input mapping (ADR-0197 Tier 1).

Pure mapping functions translating tcod gamepad events to synthetic
keyboard events. NO event-loop side effects — this module is testable
in isolation.

Architecture:
    ControllerButton + ControllerAxis + ControllerDevice
        -> gamepad_to_keysym() / trigger_to_skill_index()
        -> synthetic KeyDown (in app.py event loop)

Mapping table (Tier 1 standard SDL GameController layout):
    D-Pad/Left Stick -> Arrow keys (deadzone 0.5)
    A (south)        -> ENTER (confirm)
    B (east)         -> ESC (cancel/back)
    X (west)         -> S (skip GN/cinematic)
    Y (north)        -> Q (quit; context-sensitive)
    START            -> ESC (pause/menu toggle)
    BACK             -> ESC (quit menu)
    LEFTSHOULDER     -> PAGEUP (page nav)
    RIGHTSHOULDER    -> PAGEDOWN
    LTRIGGER         -> 1 (combat skill 1)
    RTRIGGER         -> 2 (combat skill 2)
    RTRIGGER/RTRIGGER held continuously -> button repeat (400ms/100ms)

Implementation Status:
    [G1.1a] Phase 1 — pure mapping function + constants
"""

from __future__ import annotations

from tcod.event import KeySym
from tcod.sdl.joystick import ControllerAxis, ControllerButton

# Button repeat timings (ms).
GAMEPAD_REPEAT_INITIAL_MS = 400
GAMEPAD_REPEAT_INTERVAL_MS = 100

# Analog stick deadzone (axis value range: -1.0 to +1.0).
GAMEPAD_DEADZONE = 0.5

# Trigger thresholds (0.0 to 1.0).
GAMEPAD_TRIGGER_THRESHOLD = 0.5


# Tier 1 button -> keysym mapping (Tier 2 will add per-screen overrides).
BUTTON_TO_KEYSYM: dict[ControllerButton, KeySym] = {
    # D-Pad -> Arrow keys
    ControllerButton.DPAD_UP: KeySym.UP,
    ControllerButton.DPAD_DOWN: KeySym.DOWN,
    ControllerButton.DPAD_LEFT: KeySym.LEFT,
    ControllerButton.DPAD_RIGHT: KeySym.RIGHT,
    # Face buttons -> unified action keys (reuse is_confirm_key/is_cancel_key)
    ControllerButton.A: KeySym.RETURN,  # confirm (ENTER)
    ControllerButton.B: KeySym.ESCAPE,  # cancel (ESC)
    ControllerButton.X: KeySym.S,  # skip (GN/cinematic)
    ControllerButton.Y: KeySym.Q,  # quit (context-sensitive)
    # Menu buttons -> ESC (pause/menu)
    ControllerButton.START: KeySym.ESCAPE,
    ControllerButton.BACK: KeySym.ESCAPE,
    # Shoulders -> Page navigation
    ControllerButton.LEFTSHOULDER: KeySym.PAGEUP,
    ControllerButton.RIGHTSHOULDER: KeySym.PAGEDOWN,
}


def gamepad_to_keysym(button: ControllerButton) -> KeySym | None:
    """Map a controller button to a synthetic KeySym (or None if unmapped).

    Pure function — does NOT read state, does NOT emit events. The caller
    (app.py event loop) is responsible for synthesizing the actual KeyDown
    event and dispatching.

    Args:
        button: ControllerButton enum value (e.g., ControllerButton.A).

    Returns:
        KeySym if the button has a mapping (D-Pad/A/B/X/Y/START/BACK/l/r shoulders).
        None if the button is unmapped (touchpad, paddles, guide, etc.).

    Examples:
        >>> gamepad_to_keysym(ControllerButton.A)
        <KeySym.RETURN: ...>
        >>> gamepad_to_keysym(ControllerButton.B)
        <KeySym.ESCAPE: ...>
        >>> gamepad_to_keysym(ControllerButton.TOUCHPAD)  # unmapped
        None
    """
    return BUTTON_TO_KEYSYM.get(button)


def is_dpad_button(button: ControllerButton) -> bool:
    """Check if the button is a D-Pad directional button."""
    return button in (
        ControllerButton.DPAD_UP,
        ControllerButton.DPAD_DOWN,
        ControllerButton.DPAD_LEFT,
        ControllerButton.DPAD_RIGHT,
    )


def dpad_button_to_keysym(button: ControllerButton) -> KeySym | None:
    """Map a D-Pad button to its arrow-key equivalent.

    Convenience wrapper around gamepad_to_keysym for clarity at call sites.
    Returns None for non-D-Pad buttons.
    """
    if not is_dpad_button(button):
        return None
    return BUTTON_TO_KEYSYM.get(button)


def axis_to_navigation_keysym(axis: ControllerAxis, value: int) -> KeySym | None:
    """Map a stick/trigger axis value to a navigation KeySym.

    Args:
        axis: ControllerAxis enum value (LEFTX, LEFTY, RIGHTX, RIGHTY, etc.).
        value: Axis value in range -32768..+32767 (SDL convention).

    Returns:
        KeySym for arrow direction if magnitude exceeds GAMEPAD_DEADZONE.
        None if within deadzone or axis is not a navigation axis.

    Notes:
        - Left stick: LEFTX -> LEFT/RIGHT, LEFTY -> UP/DOWN.
        - Right stick: same mapping (for parity; menus rarely need right stick).
        - Triggers: not navigation axes; use trigger_to_skill_index instead.
    """
    # Normalize to -1.0..+1.0.
    normalized = value / 32767.0
    magnitude = abs(normalized)
    if magnitude < GAMEPAD_DEADZONE:
        return None
    positive = normalized > 0

    if axis is ControllerAxis.LEFTX:
        return KeySym.RIGHT if positive else KeySym.LEFT
    if axis is ControllerAxis.LEFTY:
        # SDL axis convention: positive Y = up, negative Y = down (camera-style).
        # SDL GameController convention: positive Y = down, negative Y = up.
        # python-tcod follows SDL GameController: positive = DOWN.
        return KeySym.DOWN if positive else KeySym.UP
    if axis is ControllerAxis.RIGHTX:
        return KeySym.RIGHT if positive else KeySym.LEFT
    if axis is ControllerAxis.RIGHTY:
        return KeySym.DOWN if positive else KeySym.UP
    return None


def trigger_to_skill_index(axis: ControllerAxis, value: int) -> int | None:
    """Map a trigger axis to a combat skill index (0-based).

    Args:
        axis: ControllerAxis enum (TRIGGERLEFT or TRIGGERRIGHT).
        value: Trigger value in range 0..32767 (0 = released, 32767 = fully pressed).

    Returns:
        0 for LEFT trigger pressed beyond threshold (skill[0]).
        1 for RIGHT trigger pressed beyond threshold (skill[1]).
        None if axis is not a trigger or value below threshold.

    Notes:
        - Triggers are digital in Tier 1 (above threshold = skill activated).
        - Tier 2 may add analog sensitivity for skill power scaling.
        - Maps to combat skill shortcuts 1 and 2 (existing _COMBAT_NUMBER_KEYS pattern).
    """
    if axis not in (ControllerAxis.TRIGGERLEFT, ControllerAxis.TRIGGERRIGHT):
        return None
    normalized = value / 32767.0
    if normalized < GAMEPAD_TRIGGER_THRESHOLD:
        return None
    return 0 if axis is ControllerAxis.TRIGGERLEFT else 1


def sanitize_controller_name(raw: str | None, max_length: int = 32) -> str:
    """Sanitize a controller name for display in status messages.

    Filters out non-printable / non-ASCII characters (some controllers
    have weird Unicode in their names). Truncates to ``max_length``.

    Args:
        raw: Raw controller name string (may be None or contain garbage).
        max_length: Maximum length for the returned string.

    Returns:
        Sanitized, ASCII-printable name. Returns "Controller" if raw is empty.
    """
    if not raw:
        return "Controller"
    sanitized = "".join(ch for ch in raw if ch.isprintable() and ord(ch) < 128)
    sanitized = sanitized.strip()
    if not sanitized:
        return "Controller"
    return sanitized[:max_length]


__all__ = [
    "BUTTON_TO_KEYSYM",
    "GAMEPAD_DEADZONE",
    "GAMEPAD_REPEAT_INITIAL_MS",
    "GAMEPAD_REPEAT_INTERVAL_MS",
    "GAMEPAD_TRIGGER_THRESHOLD",
    "axis_to_navigation_keysym",
    "dpad_button_to_keysym",
    "gamepad_to_keysym",
    "is_dpad_button",
    "sanitize_controller_name",
    "trigger_to_skill_index",
]
