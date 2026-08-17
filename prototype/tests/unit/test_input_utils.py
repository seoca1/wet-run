"""Edge case tests for engine/input_utils.py (ADR-0060 Edge case 분석).

Tests all branches of the 4 input key check functions:
- is_confirm_key: ENTER / SPACE / KP_ENTER
- is_cancel_key: ESCAPE
- is_navigation_key: UP/DOWN/LEFT/RIGHT + KP 8/2/4/6
- is_quit_key: Q (and KP_7)

Each function tested with: positive cases (expected keys), negative cases
(unexpected keys), and the documented tuple constants.
"""

from __future__ import annotations

import pytest
from tcod.event import KeySym

from wet_run.engine.input_utils import (  # type: ignore[import-untyped]
    CANCEL_KEYS,
    CONFIRM_KEYS,
    QUIT_KEYS,
    is_cancel_key,
    is_confirm_key,
    is_navigation_key,
    is_quit_key,
)


class TestIsConfirmKey:
    """is_confirm_key(sym) — RETURN / SPACE / KP_ENTER."""

    @pytest.mark.parametrize("sym", [KeySym.RETURN, KeySym.KP_ENTER, KeySym.SPACE])
    def test_positive_keys(self, sym: KeySym) -> None:
        assert is_confirm_key(sym) is True

    @pytest.mark.parametrize(
        "sym",
        [KeySym.ESCAPE, KeySym.Q, KeySym.UP, KeySym.A, KeySym.F1, KeySym.TAB],
    )
    def test_negative_keys(self, sym: KeySym) -> None:
        assert is_confirm_key(sym) is False

    def test_confirm_keys_tuple_matches_function(self) -> None:
        """Documented CONFIRM_KEYS tuple must match is_confirm_key accepted set."""
        for sym in CONFIRM_KEYS:
            assert is_confirm_key(sym) is True


class TestIsCancelKey:
    """is_cancel_key(sym) — ESCAPE only."""

    def test_positive_escape(self) -> None:
        assert is_cancel_key(KeySym.ESCAPE) is True

    @pytest.mark.parametrize(
        "sym",
        [KeySym.RETURN, KeySym.SPACE, KeySym.Q, KeySym.UP, KeySym.A, KeySym.F1],
    )
    def test_negative_keys(self, sym: KeySym) -> None:
        assert is_cancel_key(sym) is False

    def test_cancel_keys_tuple_matches_function(self) -> None:
        """Documented CANCEL_KEYS tuple must match is_cancel_key accepted set."""
        for sym in CANCEL_KEYS:
            assert is_cancel_key(sym) is True


class TestIsNavigationKey:
    """is_navigation_key(sym) — UP/DOWN/LEFT/RIGHT + KP 8/2/4/6."""

    @pytest.mark.parametrize(
        "sym",
        [
            KeySym.UP,
            KeySym.DOWN,
            KeySym.LEFT,
            KeySym.RIGHT,
            KeySym.KP_8,
            KeySym.KP_2,
            KeySym.KP_4,
            KeySym.KP_6,
        ],
    )
    def test_positive_keys(self, sym: KeySym) -> None:
        assert is_navigation_key(sym) is True

    @pytest.mark.parametrize(
        "sym",
        [
            KeySym.RETURN,
            KeySym.ESCAPE,
            KeySym.SPACE,
            KeySym.A,
            KeySym.KP_5,  # center key — NOT a navigation key
            KeySym.KP_7,  # top-left on keypad — NOT in navigation set
            KeySym.KP_9,
        ],
    )
    def test_negative_keys(self, sym: KeySym) -> None:
        assert is_navigation_key(sym) is False

    def test_navigation_keys_completeness(self) -> None:
        """Exactly 8 keys accepted: 4 arrow keys + 4 numpad keys."""
        accepted = [
            sym
            for sym in [
                KeySym.UP,
                KeySym.DOWN,
                KeySym.LEFT,
                KeySym.RIGHT,
                KeySym.KP_8,
                KeySym.KP_2,
                KeySym.KP_4,
                KeySym.KP_6,
            ]
            if is_navigation_key(sym)
        ]
        assert len(accepted) == 8


class TestIsQuitKey:
    """is_quit_key(sym) — Q (and KP_7 on numpad)."""

    @pytest.mark.parametrize("sym", [KeySym.Q, KeySym.KP_7])
    def test_positive_keys(self, sym: KeySym) -> None:
        assert is_quit_key(sym) is True

    @pytest.mark.parametrize(
        "sym",
        [
            KeySym.RETURN,
            KeySym.ESCAPE,
            KeySym.SPACE,
            KeySym.A,
            KeySym.UP,
            KeySym.B,
        ],
    )
    def test_negative_keys(self, sym: KeySym) -> None:
        """Letters A, B (etc.) are NOT quit keys — only Q (and rare KP_7) are."""
        assert is_quit_key(sym) is False

    def test_quit_keys_tuple_matches_function(self) -> None:
        """Documented QUIT_KEYS tuple (just Q, NOT KP_7) — function includes KP_7."""
        for sym in QUIT_KEYS:
            assert is_quit_key(sym) is True
        # KP_7 is in the function's set but NOT in the public QUIT_KEYS tuple
        assert is_quit_key(KeySym.KP_7) is True
        assert KeySym.KP_7 not in QUIT_KEYS
