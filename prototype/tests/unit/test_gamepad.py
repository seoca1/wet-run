"""Tests for engine/gamepad.py (ADR-0197 G1.1a).

Covers:
- BUTTON_TO_KEYSYM mapping completeness (12 buttons)
- gamepad_to_keysym() return values
- dpad_button_to_keysym() correctness
- is_dpad_button() classification
- axis_to_navigation_keysym() with deadzone edge cases
- trigger_to_skill_index() with threshold edge cases
- sanitize_controller_name() with various inputs (None, ASCII, non-ASCII, control chars, length)
"""

from __future__ import annotations

from tcod.event import KeySym
from tcod.sdl.joystick import ControllerAxis, ControllerButton

from wet_run.engine.gamepad import (  # type: ignore[import-untyped]
    BUTTON_TO_KEYSYM,
    GAMEPAD_DEADZONE,
    GAMEPAD_REPEAT_INITIAL_MS,
    GAMEPAD_REPEAT_INTERVAL_MS,
    GAMEPAD_TRIGGER_THRESHOLD,
    axis_to_navigation_keysym,
    dpad_button_to_keysym,
    gamepad_to_keysym,
    is_dpad_button,
    sanitize_controller_name,
    trigger_to_skill_index,
)


class TestButtonToKeysymMapping:
    """BUTTON_TO_KEYSYM table completeness and correctness."""

    def test_dpad_up_maps_to_arrow_up(self) -> None:
        assert BUTTON_TO_KEYSYM[ControllerButton.DPAD_UP] is KeySym.UP

    def test_dpad_down_maps_to_arrow_down(self) -> None:
        assert BUTTON_TO_KEYSYM[ControllerButton.DPAD_DOWN] is KeySym.DOWN

    def test_dpad_left_maps_to_arrow_left(self) -> None:
        assert BUTTON_TO_KEYSYM[ControllerButton.DPAD_LEFT] is KeySym.LEFT

    def test_dpad_right_maps_to_arrow_right(self) -> None:
        assert BUTTON_TO_KEYSYM[ControllerButton.DPAD_RIGHT] is KeySym.RIGHT

    def test_a_button_maps_to_enter(self) -> None:
        assert BUTTON_TO_KEYSYM[ControllerButton.A] is KeySym.RETURN

    def test_b_button_maps_to_escape(self) -> None:
        assert BUTTON_TO_KEYSYM[ControllerButton.B] is KeySym.ESCAPE

    def test_x_button_maps_to_s(self) -> None:
        assert BUTTON_TO_KEYSYM[ControllerButton.X] is KeySym.S

    def test_y_button_maps_to_q(self) -> None:
        assert BUTTON_TO_KEYSYM[ControllerButton.Y] is KeySym.Q

    def test_start_maps_to_escape(self) -> None:
        assert BUTTON_TO_KEYSYM[ControllerButton.START] is KeySym.ESCAPE

    def test_back_maps_to_escape(self) -> None:
        assert BUTTON_TO_KEYSYM[ControllerButton.BACK] is KeySym.ESCAPE

    def test_left_shoulder_maps_to_pageup(self) -> None:
        assert BUTTON_TO_KEYSYM[ControllerButton.LEFTSHOULDER] is KeySym.PAGEUP

    def test_right_shoulder_maps_to_pagedown(self) -> None:
        assert BUTTON_TO_KEYSYM[ControllerButton.RIGHTSHOULDER] is KeySym.PAGEDOWN

    def test_at_least_12_buttons_mapped(self) -> None:
        assert len(BUTTON_TO_KEYSYM) >= 12


class TestGamepadToKeysym:
    """gamepad_to_keysym(button) -> KeySym | None."""

    def test_a_returns_enter(self) -> None:
        assert gamepad_to_keysym(ControllerButton.A) is KeySym.RETURN

    def test_b_returns_escape(self) -> None:
        assert gamepad_to_keysym(ControllerButton.B) is KeySym.ESCAPE

    def test_dpad_up_returns_up_arrow(self) -> None:
        assert gamepad_to_keysym(ControllerButton.DPAD_UP) is KeySym.UP

    def test_unmapped_touchpad_returns_none(self) -> None:
        assert gamepad_to_keysym(ControllerButton.TOUCHPAD) is None

    def test_unmapped_guide_returns_none(self) -> None:
        assert gamepad_to_keysym(ControllerButton.GUIDE) is None

    def test_unmapped_paddle_returns_none(self) -> None:
        assert gamepad_to_keysym(ControllerButton.PADDLE1) is None

    def test_unmapped_leftstick_returns_none(self) -> None:
        assert gamepad_to_keysym(ControllerButton.LEFTSTICK) is None

    def test_unmapped_rightstick_returns_none(self) -> None:
        assert gamepad_to_keysym(ControllerButton.RIGHTSTICK) is None

    def test_unmapped_misc1_returns_none(self) -> None:
        assert gamepad_to_keysym(ControllerButton.MISC1) is None

    def test_unmapped_invalid_returns_none(self) -> None:
        assert gamepad_to_keysym(ControllerButton.INVALID) is None


class TestDpadButtonToKeysym:
    """dpad_button_to_keysym() wrapper."""

    def test_dpad_up_returns_up(self) -> None:
        assert dpad_button_to_keysym(ControllerButton.DPAD_UP) is KeySym.UP

    def test_dpad_down_returns_down(self) -> None:
        assert dpad_button_to_keysym(ControllerButton.DPAD_DOWN) is KeySym.DOWN

    def test_a_button_returns_none(self) -> None:
        # Non-D-Pad button should return None.
        assert dpad_button_to_keysym(ControllerButton.A) is None

    def test_back_returns_none(self) -> None:
        assert dpad_button_to_keysym(ControllerButton.BACK) is None


class TestIsDpadButton:
    """is_dpad_button() classification."""

    def test_dpad_up_is_dpad(self) -> None:
        assert is_dpad_button(ControllerButton.DPAD_UP) is True

    def test_dpad_down_is_dpad(self) -> None:
        assert is_dpad_button(ControllerButton.DPAD_DOWN) is True

    def test_dpad_left_is_dpad(self) -> None:
        assert is_dpad_button(ControllerButton.DPAD_LEFT) is True

    def test_dpad_right_is_dpad(self) -> None:
        assert is_dpad_button(ControllerButton.DPAD_RIGHT) is True

    def test_a_is_not_dpad(self) -> None:
        assert is_dpad_button(ControllerButton.A) is False

    def test_b_is_not_dpad(self) -> None:
        assert is_dpad_button(ControllerButton.B) is False

    def test_shoulder_is_not_dpad(self) -> None:
        assert is_dpad_button(ControllerButton.LEFTSHOULDER) is False


class TestAxisToNavigationKeysym:
    """axis_to_navigation_keysym() with deadzone edge cases."""

    def test_leftx_positive_returns_right(self) -> None:
        # value = 32767 (full positive)
        assert axis_to_navigation_keysym(ControllerAxis.LEFTX, 32767) is KeySym.RIGHT

    def test_leftx_negative_returns_left(self) -> None:
        # value = -32768 (full negative)
        assert axis_to_navigation_keysym(ControllerAxis.LEFTX, -32768) is KeySym.LEFT

    def test_lefty_positive_returns_down(self) -> None:
        # SDL GameController convention: positive Y = down
        assert axis_to_navigation_keysym(ControllerAxis.LEFTY, 32767) is KeySym.DOWN

    def test_lefty_negative_returns_up(self) -> None:
        assert axis_to_navigation_keysym(ControllerAxis.LEFTY, -32768) is KeySym.UP

    def test_rightx_positive_returns_right(self) -> None:
        assert axis_to_navigation_keysym(ControllerAxis.RIGHTX, 32767) is KeySym.RIGHT

    def test_righty_negative_returns_up(self) -> None:
        assert axis_to_navigation_keysym(ControllerAxis.RIGHTY, -32768) is KeySym.UP

    def test_leftx_within_deadzone_returns_none(self) -> None:
        # value = 0 (centered) -> magnitude 0 < deadzone 0.5
        assert axis_to_navigation_keysym(ControllerAxis.LEFTX, 0) is None

    def test_leftx_below_deadzone_returns_none(self) -> None:
        # value = 16000 -> normalized = 16000/32767 = 0.488 < 0.5 (just below deadzone)
        assert axis_to_navigation_keysym(ControllerAxis.LEFTX, 16000) is None

    def test_leftx_at_deadzone_returns_direction(self) -> None:
        # value = 16384 -> normalized = 0.5001 >= 0.5 (just above)
        result = axis_to_navigation_keysym(ControllerAxis.LEFTX, 16384)
        assert result is KeySym.RIGHT

    def test_leftx_above_deadzone_returns_direction(self) -> None:
        # value = 20000 -> normalized = 0.61 > 0.5
        result = axis_to_navigation_keysym(ControllerAxis.LEFTX, 20000)
        assert result is KeySym.RIGHT

    def test_leftx_negative_at_deadzone_returns_left(self) -> None:
        # value = -16384 -> magnitude just above deadzone
        result = axis_to_navigation_keysym(ControllerAxis.LEFTX, -16384)
        assert result is KeySym.LEFT

    def test_trigger_axis_returns_none(self) -> None:
        # Triggers are not navigation axes.
        assert axis_to_navigation_keysym(ControllerAxis.TRIGGERLEFT, 32767) is None
        assert axis_to_navigation_keysym(ControllerAxis.TRIGGERRIGHT, 32767) is None


class TestTriggerToSkillIndex:
    """trigger_to_skill_index() with threshold edge cases."""

    def test_left_trigger_above_threshold_returns_zero(self) -> None:
        # value = 32767 -> normalized = 1.0 >= 0.5
        assert trigger_to_skill_index(ControllerAxis.TRIGGERLEFT, 32767) == 0

    def test_right_trigger_above_threshold_returns_one(self) -> None:
        # value = 32767 -> normalized = 1.0 >= 0.5
        assert trigger_to_skill_index(ControllerAxis.TRIGGERRIGHT, 32767) == 1

    def test_left_trigger_below_threshold_returns_none(self) -> None:
        # value = 16000 -> normalized = 0.488 < 0.5
        assert trigger_to_skill_index(ControllerAxis.TRIGGERLEFT, 16000) is None

    def test_right_trigger_below_threshold_returns_none(self) -> None:
        # value = 0 (released)
        assert trigger_to_skill_index(ControllerAxis.TRIGGERRIGHT, 0) is None

    def test_left_trigger_at_threshold_returns_zero(self) -> None:
        # value = 16384 -> normalized = 0.5001 >= 0.5
        assert trigger_to_skill_index(ControllerAxis.TRIGGERLEFT, 16384) == 0

    def test_right_trigger_at_threshold_returns_one(self) -> None:
        # value = 16384 -> normalized = 0.5001 >= 0.5
        assert trigger_to_skill_index(ControllerAxis.TRIGGERRIGHT, 16384) == 1

    def test_left_axis_returns_none(self) -> None:
        # LEFTX is not a trigger
        assert trigger_to_skill_index(ControllerAxis.LEFTX, 32767) is None

    def test_right_axis_returns_none(self) -> None:
        # RIGHTX is not a trigger
        assert trigger_to_skill_index(ControllerAxis.RIGHTX, 32767) is None


class TestSanitizeControllerName:
    """sanitize_controller_name() with various inputs."""

    def test_normal_ascii_unchanged(self) -> None:
        assert sanitize_controller_name("Xbox Wireless Controller") == "Xbox Wireless Controller"

    def test_empty_string_returns_default(self) -> None:
        assert sanitize_controller_name("") == "Controller"

    def test_none_returns_default(self) -> None:
        assert sanitize_controller_name(None) == "Controller"

    def test_non_ascii_stripped(self) -> None:
        # "控制器ABC" -> "ABC" (Chinese chars stripped)
        assert sanitize_controller_name("控制器ABC") == "ABC"

    def test_truncates_long_strings(self) -> None:
        long_name = "a" * 50
        assert sanitize_controller_name(long_name) == "a" * 32

    def test_null_bytes_stripped(self) -> None:
        assert sanitize_controller_name("PlayStation\x00Controller") == "PlayStationController"

    def test_special_chars_preserved(self) -> None:
        assert sanitize_controller_name("Steam Controller (Test)") == "Steam Controller (Test)"

    def test_whitespace_trimmed(self) -> None:
        assert sanitize_controller_name("  Xbox  ") == "Xbox"

    def test_all_non_ascii_returns_default(self) -> None:
        assert sanitize_controller_name("控制器游戏机") == "Controller"

    def test_custom_max_length(self) -> None:
        assert sanitize_controller_name("abcdefghij", max_length=5) == "abcde"


class TestConstants:
    """Verify tuning constants are reasonable."""

    def test_deadzone_in_valid_range(self) -> None:
        assert 0.0 < GAMEPAD_DEADZONE < 1.0
        # Tier 1 default: 0.5 (aggressive but works for Xbox/PS5).
        assert GAMEPAD_DEADZONE == 0.5

    def test_repeat_initial_ms_reasonable(self) -> None:
        # 400ms is a standard initial repeat delay.
        assert 200 <= GAMEPAD_REPEAT_INITIAL_MS <= 800

    def test_repeat_interval_ms_reasonable(self) -> None:
        # 100ms is a standard repeat interval.
        assert 30 <= GAMEPAD_REPEAT_INTERVAL_MS <= 300

    def test_trigger_threshold_in_valid_range(self) -> None:
        assert 0.0 < GAMEPAD_TRIGGER_THRESHOLD < 1.0
        assert GAMEPAD_TRIGGER_THRESHOLD == 0.5

    def test_repeat_initial_greater_than_interval(self) -> None:
        # Initial delay must be longer than subsequent interval.
        assert GAMEPAD_REPEAT_INITIAL_MS > GAMEPAD_REPEAT_INTERVAL_MS
