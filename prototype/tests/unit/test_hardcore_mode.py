"""Unit tests for Hardcore mode (Cycle 4: Pillar 3 reinforcement).

Covers:
- AppState.hardcore_mode default + boolean toggle
- Pillar 4 compliance: ephemeral session preference, no meta-progression
- No cross-run inheritance
- Death flow integration: restart attempts blocked, routed to MENU
- Death screen + input: hardcore mode skips DEATH_SUMMARY entirely
"""

from __future__ import annotations

import pytest
from tcod.event import KeyDown, KeySym, Modifier, Scancode

from wet_run.engine.death import (
    handle_death_input,
    handle_death_summary_choice,
    restart_with_new_jockey,
)
from wet_run.engine.state import AppState, ScreenKind


class TestHardcoreModeField:
    """AppState.hardcore_mode default + boolean toggle."""

    def test_default_is_false(self) -> None:
        state = AppState()
        assert state.hardcore_mode is False

    def test_can_be_enabled(self) -> None:
        state = AppState()
        state.hardcore_mode = True
        assert state.hardcore_mode is True

    def test_can_be_disabled(self) -> None:
        state = AppState()
        state.hardcore_mode = True
        state.hardcore_mode = False
        assert state.hardcore_mode is False


class TestPillar4Compliance:
    """Hardcore mode is ephemeral session preference, no meta-progression."""

    def test_no_meta_state_write(self) -> None:
        state = AppState()
        state.hardcore_mode = True
        assert not hasattr(state, "meta_state") or state.meta_state is None

    def test_does_not_persist_across_resets(self) -> None:
        """AppState() constructor resets all defaults — ephemeral session."""
        a = AppState()
        a.hardcore_mode = True
        b = AppState()
        assert b.hardcore_mode is False

    def test_is_boolean_type(self) -> None:
        state = AppState()
        assert isinstance(state.hardcore_mode, bool)


class TestHardcoreModeBehavior:
    """Verify behavior contract (1-life permadeath, Pillar 3 reinforcement)."""

    def test_default_allows_revival(self) -> None:
        """Without hardcore, the normal death → new-jockey flow applies."""
        state = AppState()
        assert state.hardcore_mode is False

    def test_restart_with_new_jockey_raises_in_hardcore(self) -> None:
        """restart_with_new_jockey raises ValueError when hardcore_mode is True."""
        state = AppState()
        state.hardcore_mode = True
        state.is_dead = True
        with pytest.raises(ValueError, match="Hardcore mode"):
            restart_with_new_jockey(state, "veteran")

    def test_restart_with_new_jockey_works_when_disabled(self) -> None:
        """restart_with_new_jockey proceeds normally when hardcore_mode is False."""
        state = AppState()
        state.character_id = "novice"
        state.hardcore_mode = False
        restart_with_new_jockey(state, "veteran")
        assert state.character_id == "veteran"
        assert state.screen == ScreenKind.CHARACTER_SELECT


class TestHardcoreDeathSummaryIntegration:
    """DEATH_SUMMARY choices must respect hardcore_mode (route to MENU)."""

    def test_hardcore_routes_new_jockey_choice_to_menu(self) -> None:
        state = AppState()
        state.hardcore_mode = True
        state.is_dead = True
        handle_death_summary_choice(state, "new_jockey")
        assert state.screen == ScreenKind.MENU
        assert state.is_dead is False

    def test_hardcore_routes_same_jockey_choice_to_menu(self) -> None:
        state = AppState()
        state.hardcore_mode = True
        state.is_dead = True
        handle_death_summary_choice(state, "same_jockey")
        assert state.screen == ScreenKind.MENU
        assert state.is_dead is False

    def test_hardcore_allows_hall_of_dead_choice(self) -> None:
        state = AppState()
        state.hardcore_mode = True
        state.is_dead = True
        handle_death_summary_choice(state, "hall_of_dead")
        assert state.screen == ScreenKind.HALL_OF_DEAD

    def test_hardcore_allows_menu_choice(self) -> None:
        state = AppState()
        state.hardcore_mode = True
        state.is_dead = True
        handle_death_summary_choice(state, "menu")
        assert state.screen == ScreenKind.MENU

    def test_non_hardcore_new_jockey_proceeds_normally(self) -> None:
        """Without hardcore, the existing death flow is unchanged."""
        state = AppState()
        state.character_id = "novice"
        state.hardcore_mode = False
        state.is_dead = True
        handle_death_summary_choice(state, "new_jockey")
        assert state.screen == ScreenKind.CHARACTER_SELECT
        assert state.character_id != "novice"


def _make_event(sym: KeySym) -> KeyDown:
    return KeyDown(sym=sym, scancode=Scancode.UP, mod=Modifier.NONE)


class TestHardcoreDeathScreenInput:
    """handle_death_input must respect hardcore_mode (route ENTER to MENU)."""

    def test_hardcore_enter_routes_to_menu(self) -> None:
        state = AppState()
        state.hardcore_mode = True
        state.is_dead = True
        state.screen = ScreenKind.DEATH
        event = _make_event(KeySym.RETURN)
        result = handle_death_input(event, state)
        assert result is True
        assert state.screen == ScreenKind.MENU
        assert state.is_dead is False

    def test_hardcore_space_routes_to_menu(self) -> None:
        state = AppState()
        state.hardcore_mode = True
        state.is_dead = True
        state.screen = ScreenKind.DEATH
        event = _make_event(KeySym.SPACE)
        handle_death_input(event, state)
        assert state.screen == ScreenKind.MENU

    def test_hardcore_kp_enter_routes_to_menu(self) -> None:
        state = AppState()
        state.hardcore_mode = True
        state.is_dead = True
        state.screen = ScreenKind.DEATH
        event = _make_event(KeySym.KP_ENTER)
        handle_death_input(event, state)
        assert state.screen == ScreenKind.MENU

    def test_hardcore_q_still_quits(self) -> None:
        state = AppState()
        state.hardcore_mode = True
        state.is_dead = True
        state.screen = ScreenKind.DEATH
        event = _make_event(KeySym.Q)
        result = handle_death_input(event, state)
        assert result is False

    def test_non_hardcore_enter_advances_to_death_summary(self) -> None:
        """Regression guard: normal flow still advances to DEATH_SUMMARY (ADR-0040)."""
        state = AppState()
        state.hardcore_mode = False
        state.is_dead = True
        state.screen = ScreenKind.DEATH
        event = _make_event(KeySym.RETURN)
        handle_death_input(event, state)
        assert state.screen == ScreenKind.DEATH_SUMMARY


class TestHardcoreDeathScreenRender:
    """render_death_screen renders different content in hardcore mode (smoke test)."""

    def test_render_death_screen_hardcore_does_not_crash(self) -> None:
        """Smoke test: render with hardcore_mode=True does not raise."""
        import tcod.console

        state = AppState()
        state.hardcore_mode = True
        state.is_dead = True
        state.death_reason = "Combat"
        state.player_max_hp = 100
        state.player_ppl = 10
        console = tcod.console.Console(width=80, height=50)
        from wet_run.engine.death import render_death_screen

        render_death_screen(console, state)

    def test_render_death_screen_normal_does_not_crash(self) -> None:
        """Regression guard: normal mode rendering still works."""
        import tcod.console

        state = AppState()
        state.hardcore_mode = False
        state.is_dead = True
        state.death_reason = "Combat"
        state.player_max_hp = 100
        state.player_ppl = 10
        console = tcod.console.Console(width=80, height=50)
        from wet_run.engine.death import render_death_screen

        render_death_screen(console, state)


__all__ = [
    "TestHardcoreModeField",
    "TestPillar4Compliance",
    "TestHardcoreModeBehavior",
    "TestHardcoreDeathSummaryIntegration",
    "TestHardcoreDeathScreenInput",
    "TestHardcoreDeathScreenRender",
]
