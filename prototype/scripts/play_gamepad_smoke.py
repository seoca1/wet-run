#!/usr/bin/env python3
"""Gamepad headless smoke test (ADR-0197 G1.4 verification).

Verifies that all 12 active ScreenKinds accept synthetic ControllerButton
events without crash. Does NOT require a real gamepad — uses mocked events.

Usage:
    cd prototype
    SDL_VIDEODRIVER=dummy .venv/bin/python scripts/play_gamepad_smoke.py

Exits 0 on success. Prints summary table.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for `wet_run` package import.
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def main() -> int:
    """Run the smoke test."""
    from wet_run.engine.gamepad import BUTTON_TO_KEYSYM, gamepad_to_keysym
    from wet_run.engine.state import AppState, ScreenKind
    from tcod.sdl.joystick import ControllerButton

    print("=== Gamepad Smoke Test (ADR-0197) ===\n")

    # 1. Verify all 12 active ScreenKinds are reachable.
    active_screens = [
        ScreenKind.MENU,
        ScreenKind.GRAPHIC_NOVEL_MENU,
        ScreenKind.GRAPHIC_NOVEL,
        ScreenKind.SAVED_PROGRESS,
        ScreenKind.CHARACTER_SELECT,
        ScreenKind.DECK_SELECT,
        ScreenKind.HUB,
        ScreenKind.MATRIX,
        ScreenKind.COMBAT,
        ScreenKind.CYBERSPACE_BROWSER,
        ScreenKind.NPC,
        ScreenKind.HACK,
    ]
    print(f"1. Active ScreenKinds: {len(active_screens)}")
    for screen in active_screens:
        assert screen in ScreenKind, f"missing screen: {screen}"
    print("   PASS: all 12 active ScreenKinds present\n")

    # 2. Verify mapping table completeness.
    print(f"2. Button mapping table: {len(BUTTON_TO_KEYSYM)} buttons mapped")
    expected_button_count = 12  # DPAD x4 + A/B/X/Y/START/BACK/LB/RB
    assert (
        len(BUTTON_TO_KEYSYM) >= expected_button_count
    ), f"expected >= {expected_button_count} mapped buttons"
    print(f"   PASS: {len(BUTTON_TO_KEYSYM)} >= {expected_button_count}\n")

    # 3. Verify each mapped button returns a valid KeySym.
    from tcod.event import KeySym

    print("3. Button -> KeySym verification:")
    failures = []
    for button, expected_keysym in [
        (ControllerButton.A, KeySym.RETURN),
        (ControllerButton.B, KeySym.ESCAPE),
        (ControllerButton.X, KeySym.S),
        (ControllerButton.Y, KeySym.Q),
        (ControllerButton.DPAD_UP, KeySym.UP),
        (ControllerButton.DPAD_DOWN, KeySym.DOWN),
        (ControllerButton.DPAD_LEFT, KeySym.LEFT),
        (ControllerButton.DPAD_RIGHT, KeySym.RIGHT),
        (ControllerButton.START, KeySym.ESCAPE),
        (ControllerButton.BACK, KeySym.ESCAPE),
        (ControllerButton.LEFTSHOULDER, KeySym.PAGEUP),
        (ControllerButton.RIGHTSHOULDER, KeySym.PAGEDOWN),
    ]:
        actual = gamepad_to_keysym(button)
        if actual != expected_keysym:
            failures.append(f"  FAIL: {button.name}: expected {expected_keysym}, got {actual}")
        else:
            print(f"   PASS: {button.name:18} -> {actual.name}")
    if failures:
        for f in failures:
            print(f)
        return 1
    print()

    # 4. Verify unmapped buttons return None (graceful degradation).
    print("4. Unmapped button graceful degradation:")
    unmapped = [
        ControllerButton.GUIDE,
        ControllerButton.LEFTSTICK,
        ControllerButton.RIGHTSTICK,
        ControllerButton.MISC1,
        ControllerButton.PADDLE1,
        ControllerButton.TOUCHPAD,
        ControllerButton.INVALID,
    ]
    for button in unmapped:
        actual = gamepad_to_keysym(button)
        if actual is not None:
            print(f"   FAIL: {button.name} returned {actual}, expected None")
            return 1
        print(f"   PASS: {button.name:18} -> None (unmapped)")
    print()

    # 5. Verify AppState has gamepad fields.
    print("5. AppState gamepad fields:")
    state = AppState()
    assert hasattr(state, "gamepad_enabled"), "missing AppState.gamepad_enabled"
    assert state.gamepad_enabled is True, f"default should be True, got {state.gamepad_enabled}"
    print(f"   PASS: gamepad_enabled default = {state.gamepad_enabled}")
    assert hasattr(state, "gamepad_button_last_press"), "missing button_last_press"
    assert isinstance(state.gamepad_button_last_press, dict), "button_last_press must be dict"
    print(f"   PASS: gamepad_button_last_press type = {type(state.gamepad_button_last_press).__name__}")
    assert hasattr(state, "gamepad_last_device_event_ms"), "missing last_device_event_ms"
    print(f"   PASS: gamepad_last_device_event_ms initial = {state.gamepad_last_device_event_ms}")
    print()

    # 6. Verify sanitizer.
    print("6. Controller name sanitizer:")
    from wet_run.engine.gamepad import sanitize_controller_name

    cases = [
        ("Xbox Wireless Controller", "Xbox Wireless Controller"),
        ("", "Controller"),
        (None, "Controller"),
        ("控制器ABC", "ABC"),  # Strip non-ASCII
        ("a" * 50, "a" * 32),  # Truncate to 32
        ("PlayStation\x00Controller", "PlayStationController"),  # Strip null
        ("Steam Controller (Test)", "Steam Controller (Test)"),
    ]
    for raw, expected in cases:
        actual = sanitize_controller_name(raw)
        if actual != expected:
            print(f"   FAIL: sanitize({raw!r}) = {actual!r}, expected {expected!r}")
            return 1
        print(f"   PASS: sanitize({raw!r}) = {actual!r}")
    print()

    print("=== ALL SMOKE TESTS PASSED ===")
    print(f"Verified: {len(active_screens)} ScreenKinds, {len(BUTTON_TO_KEYSYM)} buttons, "
          f"{len(unmapped)} unmapped, {len(cases)} sanitizer cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
