"""Tests for menu 6-option extension (ADR-0040).

Covers:
    - OPTION_HALL_OF_DEAD = 6
    - handle_menu_input N6 → HALL_OF_DEAD
    - render_menu shows 6 options
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym, Modifier, Scancode

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.engine.menu import (  # noqa: E402
    OPTION_CREDITS,
    OPTION_HALL_OF_DEAD,
    OPTION_NEW_RUN,
    handle_menu_input,
    render_menu,
)
from wet_run.engine.state import AppState, ScreenKind  # noqa: E402
from wet_run.i18n import Translator  # noqa: E402


@pytest.fixture
def state() -> AppState:
    return AppState()


@pytest.fixture
def translator() -> Translator:
    return Translator("ko", data_dir=Path(__file__).parent.parent.parent / "data" / "i18n")


def _event(sym: KeySym) -> KeyDown:
    return KeyDown(sym=sym, scancode=Scancode.UP, mod=Modifier.NONE)


def test_option_hall_of_dead_value() -> None:
    assert OPTION_HALL_OF_DEAD == 6
    assert OPTION_NEW_RUN == 1
    assert OPTION_CREDITS == 5


def test_handle_menu_n6_enters_hall_of_dead(state: AppState) -> None:
    """N6 → HALL_OF_DEAD screen (ADR-0040)."""
    state.screen = ScreenKind.MENU
    handle_menu_input(_event(KeySym.N6), state)
    assert state.screen is ScreenKind.HALL_OF_DEAD
    assert state.hall_of_dead_selected == 0


def test_render_menu_shows_hall_of_dead(state: AppState, translator: Translator) -> None:
    console = tcod.console.Console(80, 50, order="F")
    render_menu(console, translator, state)
    # Check that the Hall of Dead label is in the menu
    text_lines: list[str] = []
    for y in range(50):
        line = ""
        for x in range(80):
            code = int(console.ch[x, y])
            line += chr(code) if 0 < code < 0x110000 else " "
        text_lines.append(line.rstrip())
    text = "\n".join(text_lines)
    # The menu has option [6] Hall of Dead
    assert "Hall" in text or "죽은" in text or "[6]" in text
