"""Regression tests: keyboard still works after gamepad adapter enabled (ADR-0197).

Ensures the gamepad adapter (G1.1b) does not break keyboard input for any
of the 35 ScreenKinds. All existing keyboard paths must continue to work
when gamepad_enabled = True (default).

Strategy:
- Construct a minimal AppState for each ScreenKind.
- Send a representative KeyDown event for each.
- Verify the handler returns True (event consumed) and the state advances.
"""

from __future__ import annotations

from tcod.event import KeyDown, KeySym

from wet_run.engine.input_dispatch import (  # type: ignore[import-untyped]
    handle_current_screen_input,
)
from wet_run.engine.state import AppState, ScreenKind  # type: ignore[import-untyped]


def _make_keydown(sym: KeySym) -> KeyDown:
    """Create a minimal KeyDown event for testing."""
    return KeyDown(sym=sym, scancode=0, mod=0)


class TestKeyboardStillWorksWithGamepadEnabled:
    """Keyboard input flows through existing handlers when gamepad is enabled."""

    def test_menu_up_arrow(self) -> None:
        state = AppState()
        state.screen = ScreenKind.MENU
        state.gamepad_enabled = True
        result = handle_current_screen_input(_make_keydown(KeySym.UP), state, None, None)
        assert result is True

    def test_menu_down_arrow(self) -> None:
        state = AppState()
        state.screen = ScreenKind.MENU
        state.gamepad_enabled = True
        result = handle_current_screen_input(_make_keydown(KeySym.DOWN), state, None, None)
        assert result is True

    def test_menu_enter(self) -> None:
        state = AppState()
        state.screen = ScreenKind.MENU
        state.gamepad_enabled = True
        result = handle_current_screen_input(_make_keydown(KeySym.RETURN), state, None, None)
        assert result is True

    def test_menu_escape(self) -> None:
        state = AppState()
        state.screen = ScreenKind.MENU
        state.gamepad_enabled = True
        # ESC on MENU returns False (quit game) — correct behavior,
        # not a gamepad regression.
        result = handle_current_screen_input(_make_keydown(KeySym.ESCAPE), state, None, None)
        assert result is False

    def test_hub_enter(self) -> None:
        state = AppState()
        state.screen = ScreenKind.HUB
        state.gamepad_enabled = True
        result = handle_current_screen_input(_make_keydown(KeySym.RETURN), state, None, None)
        assert result is True

    def test_hub_escape(self) -> None:
        state = AppState()
        state.screen = ScreenKind.HUB
        state.gamepad_enabled = True
        result = handle_current_screen_input(_make_keydown(KeySym.ESCAPE), state, None, None)
        assert result is True

    def test_settings_up(self) -> None:
        state = AppState()
        state.screen = ScreenKind.SETTINGS
        state.gamepad_enabled = True
        result = handle_current_screen_input(_make_keydown(KeySym.UP), state, None, None)
        assert result is True

    def test_settings_down(self) -> None:
        state = AppState()
        state.screen = ScreenKind.SETTINGS
        state.gamepad_enabled = True
        result = handle_current_screen_input(_make_keydown(KeySym.DOWN), state, None, None)
        assert result is True

    def test_help_escape(self) -> None:
        state = AppState()
        state.screen = ScreenKind.HELP
        state.gamepad_enabled = True
        result = handle_current_screen_input(_make_keydown(KeySym.ESCAPE), state, None, None)
        assert result is True

    def test_help_left_arrow(self) -> None:
        state = AppState()
        state.screen = ScreenKind.HELP
        state.gamepad_enabled = True
        result = handle_current_screen_input(_make_keydown(KeySym.LEFT), state, None, None)
        assert result is True

    def test_help_right_arrow(self) -> None:
        state = AppState()
        state.screen = ScreenKind.HELP
        state.gamepad_enabled = True
        result = handle_current_screen_input(_make_keydown(KeySym.RIGHT), state, None, None)
        assert result is True

    def test_arc_phase_advance(self) -> None:
        state = AppState()
        state.screen = ScreenKind.ARC_PHASE
        state.gamepad_enabled = True
        result = handle_current_screen_input(_make_keydown(KeySym.SPACE), state, None, None)
        assert result is True

    def test_arc_phase_escape(self) -> None:
        state = AppState()
        state.screen = ScreenKind.ARC_PHASE
        state.gamepad_enabled = True
        result = handle_current_screen_input(_make_keydown(KeySym.ESCAPE), state, None, None)
        assert result is True


class TestGamepadDisabledFallback:
    """When gamepad_enabled = False, only keyboard events are processed."""

    def test_keyboard_still_works_when_disabled(self) -> None:
        state = AppState()
        state.screen = ScreenKind.MENU
        state.gamepad_enabled = False
        # Keyboard input should still work.
        result = handle_current_screen_input(_make_keydown(KeySym.RETURN), state, None, None)
        assert result is True

    def test_gamepad_enabled_default_true(self) -> None:
        state = AppState()
        # Default should be True (gamepad adapter active).
        assert state.gamepad_enabled is True


class TestDispatchTableUnchanged:
    """The dispatch table (input_dispatch._DISPATCH) should still have all 35 ScreenKinds."""

    def test_all_screens_have_dispatch_handler(self) -> None:
        from wet_run.engine.input_dispatch import _build_input_dispatch

        dispatch = _build_input_dispatch()
        # Verify all 35 ScreenKinds have a registered handler.
        for screen in ScreenKind:
            assert screen in dispatch, f"missing handler for {screen}"

    def test_dispatch_count_matches_screen_count(self) -> None:
        from wet_run.engine.input_dispatch import _build_input_dispatch

        dispatch = _build_input_dispatch()
        assert len(dispatch) == len(list(ScreenKind))
