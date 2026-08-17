"""Tests for death.py extensions (ADR-0040).

Covers:
    - build_deceased_jockey_from_state
    - trigger_death adds to archive + counters
    - advance_to_death_summary
    - restart_with_new_jockey resets state
    - render_death_summary_screen, render_hall_of_dead_screen
    - handle_death_summary_input, handle_hall_of_dead_input
    - handle_death_summary_choice
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym, Modifier, Scancode

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.engine.death import (  # noqa: E402
    advance_to_death_summary,
    build_deceased_jockey_from_state,
    handle_death_summary_choice,
    handle_death_summary_input,
    handle_hall_of_dead_input,
    render_death_summary_screen,
    render_hall_of_dead_screen,
    restart_with_new_jockey,
    trigger_death,
)
from wet_run.engine.jockey_history import JockeyHistory  # noqa: E402
from wet_run.engine.state import AppState, ScreenKind  # noqa: E402


def _make_event(sym: KeySym) -> KeyDown:
    return KeyDown(sym=sym, scancode=Scancode.UP, mod=Modifier.NONE)


@pytest.fixture
def state() -> AppState:
    s = AppState()
    s.character_id = "veteran"
    s.player_grade = 3
    s.player_hp = 0
    s.player_max_hp = 100
    s.player_ppl = 12
    s.is_dead = True
    s.death_reason = "Combat"
    s.inventory = {"wisp_T2": 1, "loa_drum": 3}
    s.current_node_id = "data_cache_5"
    s.current_mission = type("M", (), {"id": "watchdog_patrol"})()
    s.completed_missions = {"mission_1", "mission_2"}
    s.mission_progress = {"extract_data": 2, "defeat": 1}
    s.demo_elapsed_s = 90 * 60  # 90 minutes
    return s


@pytest.fixture
def tmp_history_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Use tmp path for jockey history."""
    from wet_run.engine import death as death_mod

    path = tmp_path / "deceased.json"

    # Replace the singleton with a tmp one
    def _tmp_history() -> JockeyHistory:
        return JockeyHistory(save_path=path)

    monkeypatch.setattr(death_mod, "_get_history", _tmp_history)
    return path


# ----------------------------------------------------------------------------
# build_deceased_jockey_from_state
# ----------------------------------------------------------------------------


def test_build_from_state_minimal(state: AppState) -> None:
    jockey = build_deceased_jockey_from_state(state)
    assert jockey.character_id == "veteran"
    assert jockey.grade == 3
    assert jockey.died_at_node == "data_cache_5"
    assert jockey.missions_completed >= 1


def test_build_from_state_inventory(state: AppState) -> None:
    jockey = build_deceased_jockey_from_state(state)
    assert "wisp_T2" in jockey.inventory_snapshot
    assert "loa_drum" in jockey.inventory_snapshot


def test_build_from_state_playtime(state: AppState) -> None:
    jockey = build_deceased_jockey_from_state(state)
    assert jockey.playtime_minutes == 90


def test_build_from_state_custom_timestamp(state: AppState) -> None:
    jockey = build_deceased_jockey_from_state(state, timestamp_ms=12345)
    assert jockey.died_at_timestamp_ms == 12345


# ----------------------------------------------------------------------------
# trigger_death (extended for ADR-0040)
# ----------------------------------------------------------------------------


def test_trigger_death_archives_jockey(state: AppState, tmp_history_path: Path) -> None:
    before_count = JockeyHistory(save_path=tmp_history_path).count()
    trigger_death(state, reason="Combat")
    after = JockeyHistory(save_path=tmp_history_path)
    assert after.count() == before_count + 1
    most_recent = after.recent(1)[0]
    assert most_recent.character_id == "veteran"
    assert most_recent.grade == 3


def test_trigger_death_bumps_counters(state: AppState, tmp_history_path: Path) -> None:
    before_runs = state.total_runs
    before_deaths = state.total_deaths
    trigger_death(state, reason="Black ICE breach")
    assert state.total_runs == before_runs + 1
    assert state.total_deaths == before_deaths + 1
    assert state.death_cause == "Black ICE breach"


def test_trigger_death_sets_summary_id(state: AppState, tmp_history_path: Path) -> None:
    trigger_death(state)
    assert state.last_jockey_summary_id != ""
    assert len(state.last_jockey_summary_id) == 32


# ----------------------------------------------------------------------------
# advance_to_death_summary
# ----------------------------------------------------------------------------


def test_advance_to_death_summary_changes_screen(state: AppState) -> None:
    state.screen = ScreenKind.DEATH
    advance_to_death_summary(state)
    assert state.screen is ScreenKind.DEATH_SUMMARY


# ----------------------------------------------------------------------------
# restart_with_new_jockey
# ----------------------------------------------------------------------------


def test_restart_with_different_character(state: AppState) -> None:
    state.character_id = "veteran"
    state.player_grade = 3
    state.inventory = {"old_item": 1}
    state.completed_missions = {"old_mission"}
    restart_with_new_jockey(state, "novice")
    assert state.character_id == "novice"
    assert state.player_grade == 1
    assert state.inventory == {}
    assert state.completed_missions == set()
    assert state.is_dead is False


def test_restart_with_same_character_jacks_out(state: AppState) -> None:
    state.character_id = "veteran"
    state.screen = ScreenKind.DEATH
    restart_with_new_jockey(state, "veteran")
    assert state.screen is ScreenKind.HUB


def test_restart_clears_matrix(state: AppState) -> None:
    state.matrix = "fake_matrix"  # type: ignore[assignment]
    state.current_node_id = "node_5"
    state.exploration = "fake_exp"  # type: ignore[assignment]
    state.combat_state = "fake_combat"  # type: ignore[assignment]
    restart_with_new_jockey(state, "novice")
    assert state.matrix is None
    assert state.current_node_id is None
    assert state.exploration is None
    assert state.combat_state is None


def test_restart_resets_chapter_state(state: AppState) -> None:
    state.chapter_elapsed_ms = 5000.0
    state.chapter_typed_chars = 100
    state.chapter_id = "chapter_veteran"
    restart_with_new_jockey(state, "heretic")
    assert state.chapter_elapsed_ms == 0.0
    assert state.chapter_typed_chars == 0
    assert state.chapter_id == "chapter_heretic"


# ----------------------------------------------------------------------------
# Input handlers
# ----------------------------------------------------------------------------


def test_handle_death_summary_input_1() -> None:
    state = AppState(screen=ScreenKind.DEATH_SUMMARY, character_id="veteran")
    result = handle_death_summary_input(_make_event(KeySym.N1), state)
    assert result is True
    assert state.character_id in ("novice", "heretic")


def test_handle_death_summary_input_2() -> None:
    state = AppState(screen=ScreenKind.DEATH_SUMMARY, character_id="veteran", is_dead=True)
    result = handle_death_summary_input(_make_event(KeySym.N2), state)
    assert result is True
    assert state.screen == ScreenKind.HUB


def test_handle_death_summary_input_3() -> None:
    state = AppState(screen=ScreenKind.DEATH_SUMMARY)
    result = handle_death_summary_input(_make_event(KeySym.N3), state)
    assert result is True
    assert state.screen == ScreenKind.HALL_OF_DEAD


def test_handle_death_summary_input_4() -> None:
    state = AppState(screen=ScreenKind.DEATH_SUMMARY, is_dead=True)
    result = handle_death_summary_input(_make_event(KeySym.N4), state)
    assert result is True
    assert state.screen == ScreenKind.MENU
    assert state.is_dead is False


def test_handle_death_summary_input_escape() -> None:
    state = AppState(screen=ScreenKind.DEATH_SUMMARY, is_dead=True)
    result = handle_death_summary_input(_make_event(KeySym.ESCAPE), state)
    assert result is True
    assert state.screen == ScreenKind.MENU
    assert state.is_dead is False


def test_handle_death_summary_input_unknown() -> None:
    state = AppState(screen=ScreenKind.DEATH_SUMMARY)
    result = handle_death_summary_input(_make_event(KeySym.A), state)
    assert result is True
    assert state.screen == ScreenKind.DEATH_SUMMARY


def test_handle_hall_of_dead_input_up() -> None:
    state = AppState(screen=ScreenKind.HALL_OF_DEAD, hall_of_dead_selected=5)
    result = handle_hall_of_dead_input(_make_event(KeySym.UP), state)
    assert result is True
    assert state.hall_of_dead_selected == 4


def test_handle_hall_of_dead_input_down() -> None:
    state = AppState(screen=ScreenKind.HALL_OF_DEAD, hall_of_dead_selected=5)
    result = handle_hall_of_dead_input(_make_event(KeySym.DOWN), state)
    assert result is True
    assert state.hall_of_dead_selected == 6


def test_handle_hall_of_dead_input_escape() -> None:
    state = AppState(screen=ScreenKind.HALL_OF_DEAD, hall_of_dead_selected=5)
    result = handle_hall_of_dead_input(_make_event(KeySym.ESCAPE), state)
    assert result is True
    assert state.screen == ScreenKind.DEATH_SUMMARY


def test_handle_hall_of_dead_input_enter() -> None:
    state = AppState(screen=ScreenKind.HALL_OF_DEAD, hall_of_dead_selected=5)
    result = handle_hall_of_dead_input(_make_event(KeySym.RETURN), state)
    assert result is True


# ----------------------------------------------------------------------------
# handle_death_summary_choice
# ----------------------------------------------------------------------------


def test_choice_new_jockey(state: AppState, tmp_history_path: Path) -> None:
    state.character_id = "veteran"
    state.screen = ScreenKind.DEATH_SUMMARY
    handle_death_summary_choice(state, "new_jockey")
    # Should pick a different character
    assert state.character_id in ("novice", "heretic")
    assert state.screen in (ScreenKind.CHARACTER_SELECT, ScreenKind.HUB)


def test_choice_same_jockey(state: AppState) -> None:
    state.character_id = "veteran"
    state.screen = ScreenKind.DEATH_SUMMARY
    handle_death_summary_choice(state, "same_jockey")
    assert state.screen is ScreenKind.HUB
    assert state.is_dead is False


def test_choice_hall_of_dead(state: AppState) -> None:
    state.screen = ScreenKind.DEATH_SUMMARY
    handle_death_summary_choice(state, "hall_of_dead")
    assert state.screen is ScreenKind.HALL_OF_DEAD


def test_choice_menu(state: AppState) -> None:
    state.screen = ScreenKind.DEATH_SUMMARY
    state.is_dead = True
    handle_death_summary_choice(state, "menu")
    assert state.screen is ScreenKind.MENU
    assert state.is_dead is False


# ----------------------------------------------------------------------------
# Renderers (smoke tests)
# ----------------------------------------------------------------------------


def test_render_death_summary_smoke(state: AppState, tmp_history_path: Path) -> None:
    """Should not crash."""
    trigger_death(state)
    state.screen = ScreenKind.DEATH_SUMMARY
    console = tcod.console.Console(80, 30, order="F")
    render_death_summary_screen(console, state, width=80, height=30)
    text_lines = []
    for y in range(30):
        line = ""
        for x in range(80):
            code = int(console.ch[x, y])
            line += chr(code) if 0 < code < 0x110000 else " "
        text_lines.append(line.rstrip())
    # Should show the jockey's name or summary
    assert any("케이" in line or "Veteran" in line for line in text_lines if line)


def test_render_hall_of_dead_smoke(state: AppState, tmp_history_path: Path) -> None:
    """Should not crash with empty or populated archive."""
    console = tcod.console.Console(80, 30, order="F")
    render_hall_of_dead_screen(console, state, width=80, height=30)
    # Add a jockey
    trigger_death(state)
    state.last_jockey_summary_id = ""  # reset
    render_hall_of_dead_screen(console, state, width=80, height=30)
    text_lines = []
    for y in range(30):
        line = ""
        for x in range(80):
            code = int(console.ch[x, y])
            line += chr(code) if 0 < code < 0x110000 else " "
        text_lines.append(line.rstrip())
    text = "\n".join(text_lines)
    assert "HALL OF DEAD" in text


# ----------------------------------------------------------------------------
# Module API
# ----------------------------------------------------------------------------


def test_module_exports() -> None:
    """Public API surface."""
    assert callable(build_deceased_jockey_from_state)
    assert callable(trigger_death)
    assert callable(advance_to_death_summary)
    assert callable(restart_with_new_jockey)
    assert callable(render_death_summary_screen)
    assert callable(render_hall_of_dead_screen)
    assert callable(handle_death_summary_input)
    assert callable(handle_hall_of_dead_input)
    assert callable(handle_death_summary_choice)
