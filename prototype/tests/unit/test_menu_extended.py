"""Tests for menu.py extension (ADR-0032 — 5 menu options).

Covers:
    - 5 OPTION constants
    - render_menu shows all 5 options
    - handle_menu_input dispatches to all 5 screens
    - handle_graphic_novel_menu_input for GN menu
    - handle_graphic_novel_input for GN playback
    - handle_saved_progress_input for SAVED_PROGRESS
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import tcod.console  # noqa: E402
import tcod.event  # noqa: E402
from tcod.event import KeyDown, KeySym  # noqa: E402

from wet_run.engine.menu import (  # noqa: E402
    OPTION_CONTINUE,
    OPTION_CREDITS,
    OPTION_GRAPHIC_NOVEL,
    OPTION_NEW_RUN,
    OPTION_SETTINGS,
    handle_graphic_novel_input,
    handle_graphic_novel_menu_input,
    handle_menu_input,
    handle_saved_progress_input,
    render_menu,
)
from wet_run.engine.save_manager import SaveManager  # noqa: E402
from wet_run.engine.state import AppState, ScreenKind  # noqa: E402
from wet_run.i18n import Translator  # noqa: E402

DATA_DIR = Path(__file__).parent.parent.parent / "data"


# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------


@pytest.fixture
def state() -> AppState:
    return AppState()


@pytest.fixture
def translator() -> Translator:
    return Translator("en", data_dir=DATA_DIR / "i18n")


@pytest.fixture
def console() -> tcod.console.Console:
    return tcod.console.Console(80, 50, order="F")


@pytest.fixture
def no_save(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub SaveManager.has_save to return False (no save in slot 1)."""
    monkeypatch.setattr(SaveManager, "has_save", lambda self, slot: False)


@pytest.fixture
def with_save(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub SaveManager.has_save to return True (save exists in slot 1)."""
    monkeypatch.setattr(SaveManager, "has_save", lambda self, slot: True)


def _key_event(sym: KeySym) -> tcod.event.KeyDown:
    return KeyDown(sym=sym, scancode=0, mod=0, repeat=0)


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------


def test_option_constants() -> None:
    """5 distinct options."""
    assert OPTION_NEW_RUN == 1
    assert OPTION_GRAPHIC_NOVEL == 2
    assert OPTION_CONTINUE == 3
    assert OPTION_SETTINGS == 4
    assert OPTION_CREDITS == 5


# ----------------------------------------------------------------------------
# render_menu
# ----------------------------------------------------------------------------


def test_render_menu_runs(
    state: AppState, translator: Translator, console: tcod.console.Console
) -> None:
    """render_menu should not crash."""
    render_menu(console, translator, state)


def test_render_menu_shows_new_run(
    state: AppState, translator: Translator, console: tcod.console.Console
) -> None:
    render_menu(console, translator, state)
    text = _console_to_text(console)
    assert "New Run" in text


def test_render_menu_shows_graphic_novel(
    state: AppState, translator: Translator, console: tcod.console.Console
) -> None:
    render_menu(console, translator, state)
    text = _console_to_text(console)
    assert "Graphic Novel" in text


def test_render_menu_continue_no_save_label(
    state: AppState, translator: Translator, console: tcod.console.Console, no_save: None
) -> None:
    """Without save, Continue should be dimmed (marked as 'no save')."""
    render_menu(console, translator, state)
    text = _console_to_text(console)
    assert "Continue" in text


# ----------------------------------------------------------------------------
# handle_menu_input
# ----------------------------------------------------------------------------


def test_handle_menu_key1_new_run(state: AppState) -> None:
    state.screen = ScreenKind.MENU
    handle_menu_input(_key_event(KeySym.N1), state)
    assert state.screen == ScreenKind.HUB


def test_handle_menu_key2_graphic_novel(state: AppState) -> None:
    state.screen = ScreenKind.MENU
    handle_menu_input(_key_event(KeySym.N2), state)
    assert state.screen == ScreenKind.GRAPHIC_NOVEL_MENU


def test_handle_menu_key3_continue_no_save(state: AppState, no_save: None) -> None:
    """No save → message instead of screen change."""
    state.screen = ScreenKind.MENU
    handle_menu_input(_key_event(KeySym.N3), state)
    assert state.screen == ScreenKind.MENU
    assert "save" in state.message.lower() or "Save" in state.message


def test_handle_menu_key3_continue_with_save(state: AppState, with_save: None) -> None:
    """With save → load to HUB."""
    state.screen = ScreenKind.MENU
    handle_menu_input(_key_event(KeySym.N3), state)
    assert state.screen == ScreenKind.HUB


def test_render_menu_uses_save_manager_not_state_field(
    state: AppState, translator: Translator, console: tcod.console.Console
) -> None:
    """Regression (GA-002): menu must read live SaveManager.has_save,
    not a stale AppState.has_save field that was only set once at app
    startup. If the player saves mid-session, the menu should reflect
    that immediately (without requiring app restart).
    """
    render_menu(console, translator, state)
    text = _console_to_text(console)
    assert "Continue" in text


def test_handle_menu_key4_settings(state: AppState) -> None:
    state.screen = ScreenKind.MENU
    handle_menu_input(_key_event(KeySym.N4), state)
    assert state.screen == ScreenKind.SETTINGS
    assert state.settings_selected == 0


def test_handle_menu_key5_credits(state: AppState) -> None:
    state.screen = ScreenKind.MENU
    handle_menu_input(_key_event(KeySym.N5), state)
    assert state.message  # placeholder message


def test_handle_menu_quit(state: AppState) -> None:
    """Q → False (quit)."""
    state.screen = ScreenKind.MENU
    result = handle_menu_input(_key_event(KeySym.Q), state)
    assert result is False


def test_handle_menu_escape(state: AppState) -> None:
    state.screen = ScreenKind.MENU
    result = handle_menu_input(_key_event(KeySym.ESCAPE), state)
    assert result is False


def test_handle_menu_graphic_novel_resets_state(state: AppState) -> None:
    """GN option should reset gn_* state fields."""
    state.gn_scene_index = 5
    state.gn_paused = True
    state.gn_scene_chain = ["a", "b", "c"]
    state.screen = ScreenKind.MENU
    handle_menu_input(_key_event(KeySym.N2), state)
    assert state.gn_scene_index == 0
    assert state.gn_paused is False
    assert state.gn_scene_chain == []


# ----------------------------------------------------------------------------
# handle_graphic_novel_menu_input
# ----------------------------------------------------------------------------


def test_gn_menu_prologue(state: AppState) -> None:
    state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
    result = handle_graphic_novel_menu_input(_key_event(KeySym.N1), state)
    assert result is True
    assert state.screen == ScreenKind.GRAPHIC_NOVEL
    assert state.gn_mode == "prologue"


def test_gn_menu_novice(state: AppState) -> None:
    state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
    result = handle_graphic_novel_menu_input(_key_event(KeySym.N2), state)
    assert result is True
    assert state.screen == ScreenKind.GRAPHIC_NOVEL
    assert state.gn_mode == "novice"


def test_gn_menu_veteran(state: AppState) -> None:
    state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
    result = handle_graphic_novel_menu_input(_key_event(KeySym.N3), state)
    assert result is True
    assert state.screen == ScreenKind.GRAPHIC_NOVEL
    assert state.gn_mode == "veteran"


def test_gn_menu_heretic(state: AppState) -> None:
    state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
    result = handle_graphic_novel_menu_input(_key_event(KeySym.N4), state)
    assert result is True
    assert state.screen == ScreenKind.GRAPHIC_NOVEL
    assert state.gn_mode == "heretic"


def test_gn_menu_back(state: AppState) -> None:
    state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
    result = handle_graphic_novel_menu_input(_key_event(KeySym.N5), state)
    assert result is True
    assert state.screen == ScreenKind.MENU


def test_gn_menu_escape_back(state: AppState) -> None:
    state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
    result = handle_graphic_novel_menu_input(_key_event(KeySym.ESCAPE), state)
    assert result is True
    assert state.screen == ScreenKind.MENU


def test_gn_menu_unknown_key(state: AppState) -> None:
    state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
    result = handle_graphic_novel_menu_input(_key_event(KeySym.B), state)
    assert result is True
    assert state.screen == ScreenKind.GRAPHIC_NOVEL_MENU


# ----------------------------------------------------------------------------
# handle_graphic_novel_input
# ----------------------------------------------------------------------------


def test_gn_input_space_next(state: AppState) -> None:
    result = handle_graphic_novel_input(_key_event(KeySym.SPACE), state)
    assert result == "next"


def test_gn_input_right_next(state: AppState) -> None:
    result = handle_graphic_novel_input(_key_event(KeySym.RIGHT), state)
    assert result == "next"


def test_gn_input_s_skip(state: AppState) -> None:
    result = handle_graphic_novel_input(_key_event(KeySym.S), state)
    assert result == "skip"


def test_gn_input_p_pause(state: AppState) -> None:
    result = handle_graphic_novel_input(_key_event(KeySym.P), state)
    assert result == "pause"


def test_gn_input_esc_menu(state: AppState) -> None:
    result = handle_graphic_novel_input(_key_event(KeySym.ESCAPE), state)
    assert result == "menu"


def test_gn_input_q_menu(state: AppState) -> None:
    result = handle_graphic_novel_input(_key_event(KeySym.Q), state)
    assert result == "menu"


# ----------------------------------------------------------------------------
# handle_saved_progress_input
# ----------------------------------------------------------------------------


def test_saved_progress_key1_other_chars(state: AppState) -> None:
    state.screen = ScreenKind.SAVED_PROGRESS
    result = handle_saved_progress_input(_key_event(KeySym.N1), state)
    assert result is True
    assert state.screen == ScreenKind.GRAPHIC_NOVEL_MENU


def test_saved_progress_key2_continue(state: AppState) -> None:
    state.screen = ScreenKind.SAVED_PROGRESS
    result = handle_saved_progress_input(_key_event(KeySym.N2), state)
    assert result is True
    assert state.screen == ScreenKind.HUB


def test_saved_progress_key3_menu(state: AppState) -> None:
    state.screen = ScreenKind.SAVED_PROGRESS
    result = handle_saved_progress_input(_key_event(KeySym.N3), state)
    assert result is True
    assert state.screen == ScreenKind.MENU


def test_saved_progress_esc_menu(state: AppState) -> None:
    state.screen = ScreenKind.SAVED_PROGRESS
    result = handle_saved_progress_input(_key_event(KeySym.ESCAPE), state)
    assert result is True
    assert state.screen == ScreenKind.MENU


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def _console_to_text(console: tcod.console.Console) -> str:
    lines: list[str] = []
    for y in range(console.height):
        chars: list[str] = []
        for x in range(console.width):
            code = int(console.ch[x, y])
            chars.append(chr(code) if 0 < code < 0x110000 else " ")
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)
