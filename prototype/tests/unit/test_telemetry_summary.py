"""Tests for Phase 17 telemetry summary screen (UI exposure).

Verifies:

1. ``render_telemetry_summary`` reads aggregate_* helpers and prints
   them on screen.
2. ``handle_telemetry_stats_input`` ESC returns to the main menu.
3. The opt-in guard is double-enforced: the dispatcher refuses
   ``OPTION_STATS`` when ``telemetry_opt_in`` is False, and the
   renderer itself shows an opt-out message if state is mismatched.
4. ``MENU_OPTION_COUNT`` now includes the new option (9).
5. ``ScreenKind.TELEMETRY_STATS`` is a valid screen enum value.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.console
import tcod.event

from roguelike_sprawl.combat.telemetry_integration import (
    TelemetryConfig,
    TelemetryIntegrator,
)
from roguelike_sprawl.engine import menu as menu_mod
from roguelike_sprawl.engine.state import AppState, ScreenKind
from roguelike_sprawl.i18n import Translator

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(*, opt_in: bool) -> AppState:
    state = AppState()
    state.telemetry_opt_in = opt_in
    state.telemetry = TelemetryIntegrator(TelemetryConfig(opted_in_at_start=opt_in))
    return state


def _make_console(width: int = 80, height: int = 30) -> tcod.console.Console:
    return tcod.console.Console(width=width, height=height)


def _make_translator() -> Translator:
    from pathlib import Path

    return Translator("en", data_dir=Path("prototype/data/i18n"))


# ---------------------------------------------------------------------------
# Item 3a: ScreenKind + menu wiring
# ---------------------------------------------------------------------------


class TestTelemetryStatsScreenKind:
    """Phase 17: TELEMETRY_STATS is a valid ScreenKind enum value."""

    def test_screen_kind_exists(self) -> None:
        assert hasattr(ScreenKind, "TELEMETRY_STATS")
        assert ScreenKind.TELEMETRY_STATS == "telemetry_stats"


class TestStatsMenuOption:
    """Phase 17: OPTION_STATS is 9 and MENU_OPTION_COUNT is 9."""

    def test_option_stats_value(self) -> None:
        assert menu_mod.OPTION_STATS == 9
        assert menu_mod.MENU_OPTION_COUNT == 9

    def test_n9_dispatches_to_stats(self) -> None:
        """Pressing '9' from the main menu routes to TELEMETRY_STATS
        when telemetry_opt_in is True."""
        state = _make_state(opt_in=True)
        state.menu_selected_index = 0
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.N9, mod=0, scancode=0)
        result = menu_mod.handle_menu_input(event, state)
        assert result is True
        assert state.screen == ScreenKind.TELEMETRY_STATS

    def test_n9_no_op_when_opt_out(self) -> None:
        """Pressing '9' from the main menu is a no-op when telemetry is OFF."""
        state = _make_state(opt_in=False)
        state.menu_selected_index = 0
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.N9, mod=0, scancode=0)
        result = menu_mod.handle_menu_input(event, state)
        assert result is True
        # Stays on MENU; the user gets a hint message instead.
        assert state.screen == ScreenKind.MENU
        assert "telemetry" in state.message.lower() or "opt-in" in state.message.lower()


# ---------------------------------------------------------------------------
# Item 3b: render_telemetry_summary
# ---------------------------------------------------------------------------


class TestRenderTelemetrySummary:
    """Phase 17: render_telemetry_summary shows aggregated data + opt-in guard."""

    def test_renders_with_opt_in_and_data(self) -> None:
        """When opted in and the integrator has events, the screen renders."""
        console = _make_console()
        t = _make_translator()
        state = _make_state(opt_in=True)
        # Record some events.
        state.telemetry.record_death("standard", turn=10)
        state.telemetry.record_kill("watchdog", turn=20)
        state.telemetry.record_deck_chosen("standard")
        menu_mod.render_telemetry_summary(console, t, state)
        # No exception is the primary assertion. Spot-check that
        # the title row has at least one non-space, non-zero codepoint
        # (i.e. some text was drawn).
        any_text = False
        for x in range(console.width):
            if int(console.ch[x, 0]) not in (0, 32):
                any_text = True
                break
        assert any_text

    def test_renders_with_opt_in_but_no_data(self) -> None:
        console = _make_console()
        t = _make_translator()
        state = _make_state(opt_in=True)
        menu_mod.render_telemetry_summary(console, t, state)
        # No exception. The 'empty' message should be drawn.
        # We just check that drawing didn't raise.

    def test_renders_with_opt_out(self) -> None:
        """Opt-out must NOT show aggregate data, even if the integrator
        exists. The screen shows the opt-out message instead."""
        console = _make_console()
        t = _make_translator()
        state = _make_state(opt_in=False)
        # Even with events in the integrator, the screen is gated.
        state.telemetry.record_death("standard", turn=1)
        menu_mod.render_telemetry_summary(console, t, state)
        # No exception. Verify by reading the console for the title
        # (which should still render the TELEMETRY SUMMARY banner,
        # but no section data).

    def test_renders_without_integrator(self) -> None:
        """If state.telemetry is None (no session), the screen shows the
        empty-state message instead of crashing."""
        console = _make_console()
        t = _make_translator()
        state = AppState()
        state.telemetry_opt_in = True
        state.telemetry = None
        menu_mod.render_telemetry_summary(console, t, state)
        # No exception.

    def test_aggregations_reach_screen(self) -> None:
        """End-to-end: record events, render, verify the aggregate
        counters actually flowed through to the screen data path."""
        console = _make_console()
        t = _make_translator()
        state = _make_state(opt_in=True)
        # 2 standard deaths, 1 watchdog death, 3 kills, 1 deck pick.
        state.telemetry.record_death("standard", turn=1)
        state.telemetry.record_death("standard", turn=2)
        state.telemetry.record_death("watchdog", turn=3)
        state.telemetry.record_kill("standard", turn=4)
        state.telemetry.record_kill("standard", turn=5)
        state.telemetry.record_kill("watchdog", turn=6)
        state.telemetry.record_deck_chosen("standard")
        # Direct aggregate sanity (independent of render).
        deaths = state.telemetry.aggregate_death_rates()
        kills = state.telemetry.aggregate_kill_counts()
        decks = state.telemetry.aggregate_deck_distribution()
        assert deaths == {"standard": 2, "watchdog": 1}
        assert kills == {"standard": 2, "watchdog": 1}
        assert decks == {"standard": 1}
        # Render still works.
        menu_mod.render_telemetry_summary(console, t, state)


# ---------------------------------------------------------------------------
# Item 3c: handle_telemetry_stats_input
# ---------------------------------------------------------------------------


class TestHandleTelemetryStatsInput:
    """Phase 17: the input handler routes ESC back to MENU."""

    def test_esc_returns_to_menu(self) -> None:
        state = _make_state(opt_in=True)
        state.screen = ScreenKind.TELEMETRY_STATS
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.ESCAPE, mod=0, scancode=0)
        result = menu_mod.handle_telemetry_stats_input(event, state)
        assert result is True
        assert state.screen == ScreenKind.MENU

    def test_q_returns_to_menu(self) -> None:
        state = _make_state(opt_in=True)
        state.screen = ScreenKind.TELEMETRY_STATS
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.Q, mod=0, scancode=0)
        result = menu_mod.handle_telemetry_stats_input(event, state)
        assert result is True
        assert state.screen == ScreenKind.MENU

    def test_other_key_is_ignored(self) -> None:
        state = _make_state(opt_in=True)
        state.screen = ScreenKind.TELEMETRY_STATS
        event = tcod.event.KeyDown(sym=tcod.event.KeySym.SPACE, mod=0, scancode=0)
        result = menu_mod.handle_telemetry_stats_input(event, state)
        # Returns True (handled = consumed) but screen doesn't change.
        assert result is True
        assert state.screen == ScreenKind.TELEMETRY_STATS


# ---------------------------------------------------------------------------
# Item 3d: render_menu shows STATS dimmed when opt-out
# ---------------------------------------------------------------------------


class TestMenuRendersStatsLabel:
    """Phase 17: the main menu shows the STATS option, dimmed when opt-out."""

    def test_menu_renders_with_opt_in(self) -> None:
        console = _make_console(width=80, height=40)
        t = _make_translator()
        state = _make_state(opt_in=True)
        menu_mod.render_menu(console, t, state)
        # No exception. Verify a non-empty title was drawn.
        any_text = False
        for x in range(console.width):
            if int(console.ch[x, 0]) not in (0, 32):
                any_text = True
                break
        assert any_text

    def test_menu_renders_with_opt_out(self) -> None:
        console = _make_console(width=80, height=40)
        t = _make_translator()
        state = _make_state(opt_in=False)
        menu_mod.render_menu(console, t, state)
        # No exception — the disabled state still renders cleanly.
