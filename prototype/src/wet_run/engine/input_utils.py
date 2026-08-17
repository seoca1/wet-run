"""Input utilities: unified key handling."""

from __future__ import annotations

from tcod.event import KeySym


def is_confirm_key(sym: KeySym) -> bool:
    """Check if a key is ENTER, SPACE, or KP_ENTER (unified confirm)."""
    return sym in (KeySym.RETURN, KeySym.KP_ENTER, KeySym.SPACE)


def is_cancel_key(sym: KeySym) -> bool:
    """Check if a key is ESCAPE."""
    return sym is KeySym.ESCAPE


def is_navigation_key(sym: KeySym) -> bool:
    """Check if a key is a navigation key (arrow keys)."""
    return sym in (
        KeySym.UP,
        KeySym.DOWN,
        KeySym.LEFT,
        KeySym.RIGHT,
        KeySym.KP_8,
        KeySym.KP_2,
        KeySym.KP_4,
        KeySym.KP_6,
    )


def is_quit_key(sym: KeySym) -> bool:
    """Check if a key is Q (quit)."""
    return sym in (KeySym.Q, KeySym.KP_7)  # Q on keypad (rare)


# Aliases for clarity
CONFIRM_KEYS = (KeySym.RETURN, KeySym.KP_ENTER, KeySym.SPACE)
CANCEL_KEYS = (KeySym.ESCAPE,)
QUIT_KEYS = (KeySym.Q,)
