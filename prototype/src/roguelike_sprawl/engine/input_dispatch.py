"""Input event dispatch (Phase D-2 deep4).

Extracted from app.py:_handle_input() — replaces the 30-branch if/elif
chain with a dict-based input dispatch table. Mirrors the structure of
screen_dispatch.py (which handles render dispatch).

Each ScreenKind maps to a callable (event, state, prog_registry,
ice_registry) -> bool (False = quit game).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from .state import AppState, ScreenKind

if TYPE_CHECKING:
    import tcod.event

    from ..combat.registry import IceRegistry, ProgramRegistry

import tcod.event

# Input handler signature: (event, state, prog, ice) -> bool
InputFn = Callable[..., object]


def _build_input_dispatch() -> dict[ScreenKind, InputFn]:
    """Build input dispatch table (lazy import)."""
    from . import (
        chapter_view,
        combat_view,
        debrief_view,
        dungeon_view,
        event_view,
        hacking_view,
        help_view,
        jack_out_view,
        npc_view,
        reward_view,
        salvation_view,
        save_load_view,
        settings_view,
        story_cinematic,
    )
    from . import (
        cyberspace_browser as cb_screen,
    )
    from . import (
        death as death_screen,
    )
    from . import (
        hub as hub_screen,
    )
    from . import (
        menu as menu_screen,
    )
    from . import story_view as story_screen

    def _gn_screen(
        event: tcod.event.Event,
        state: AppState,
        prog: ProgramRegistry | None,
        ice: IceRegistry | None,
    ) -> bool:
        action = menu_screen.handle_graphic_novel_input(event, state)
        if action == "menu":
            state.screen = ScreenKind.MENU
            return True
        if action == "next":
            _advance_graphic_novel_scene(state, forward=True)
            return True
        if action == "skip":
            _advance_graphic_novel_scene(state, forward=True, full_skip=True)
            return True
        if action == "pause":
            state.gn_paused = not state.gn_paused
            return True
        return True

    def _gn_ending(
        event: tcod.event.Event,
        state: AppState,
        prog: ProgramRegistry | None,
        ice: IceRegistry | None,
    ) -> bool:
        import tcod.event as _tcevent

        if isinstance(event, _tcevent.KeyDown):
            if event.sym in (_tcevent.KeySym.ESCAPE, _tcevent.KeySym.Q):
                state.screen = ScreenKind.MENU
                return True
        return True

    def _cyberspace_map(
        event: tcod.event.Event,
        state: AppState,
        prog: ProgramRegistry | None,
        ice: IceRegistry | None,
    ) -> bool:
        import tcod.event as _tcevent

        if isinstance(event, _tcevent.KeyDown):
            if event.sym in (_tcevent.KeySym.ESCAPE, _tcevent.KeySym.Q):
                state.screen = ScreenKind.MENU
                return True
        return True

    def _arc_phase(
        event: tcod.event.Event,
        state: AppState,
        prog: ProgramRegistry | None,
        ice: IceRegistry | None,
    ) -> bool:
        import tcod.event as _tcevent

        from .arc_phase import advance_arc_phase

        if isinstance(event, _tcevent.KeyDown):
            if event.sym in (_tcevent.KeySym.ESCAPE, _tcevent.KeySym.Q):
                state.screen = ScreenKind.MENU
                return True
            if event.sym in (
                _tcevent.KeySym.SPACE,
                _tcevent.KeySym.RETURN,
                _tcevent.KeySym.RIGHT,
            ):
                advance_arc_phase(state)
                return True
            if event.sym in (_tcevent.KeySym.S,):
                state.phase_elapsed_ms = float("inf")
                state.phase_typed_chars = 9999
                advance_arc_phase(state)
                return True
        return True

    def _chapter(
        event: tcod.event.Event,
        state: AppState,
        prog: ProgramRegistry | None,
        ice: IceRegistry | None,
    ) -> bool:
        chapter_view.handle_chapter_input(event, state)
        return True

    def _event(
        event: tcod.event.Event,
        state: AppState,
        prog: ProgramRegistry | None,
        ice: IceRegistry | None,
    ) -> bool:
        if state.active_event is not None:
            return event_view.handle_event_input(event, state, state.active_event)
        return True

    def _npc(
        event: tcod.event.Event,
        state: AppState,
        prog: ProgramRegistry | None,
        ice: IceRegistry | None,
    ) -> bool:
        if state.npc_state is not None:
            npc_view.handle_npc_input(event, state, state.npc_state)
        return True

    def _cinematic(
        event: tcod.event.Event,
        state: AppState,
        prog: ProgramRegistry | None,
        ice: IceRegistry | None,
    ) -> bool:
        if state.cinematic_state is not None:
            return story_cinematic.handle_cinematic_input(event, state, state.cinematic_state)
        return True

    return {
        ScreenKind.MENU: menu_screen.handle_menu_input,
        ScreenKind.GRAPHIC_NOVEL_MENU: menu_screen.handle_graphic_novel_menu_input,
        ScreenKind.GRAPHIC_NOVEL: _gn_screen,
        ScreenKind.GRAPHIC_NOVEL_ENDING_MENU: _gn_ending,
        ScreenKind.SAVED_PROGRESS: menu_screen.handle_saved_progress_input,
        ScreenKind.HUB: hub_screen.handle_hub_input,
        ScreenKind.CHAPTER: _chapter,
        ScreenKind.CHARACTER_SELECT: menu_screen.handle_character_select_input,
        ScreenKind.DECK_SELECT: menu_screen.handle_deck_select_input,
        ScreenKind.ENDING: menu_screen.handle_ending_input,
        ScreenKind.SAVE_SLOT_SELECT: save_load_view.handle_save_load_input,
        ScreenKind.EVENT: _event,
        ScreenKind.STORY: story_screen.handle_story_input,
        ScreenKind.ARC_PHASE: _arc_phase,
        ScreenKind.CYBERSPACE_BROWSER: cb_screen.handle_browser_input,
        ScreenKind.CYBERSPACE_MAP: _cyberspace_map,
        ScreenKind.NPC: _npc,
        ScreenKind.HACK: hacking_view.handle_hack_input,
        ScreenKind.MATRIX: lambda e, s, p, i: dungeon_view.handle_dungeon_input(e, s, p, i),
        ScreenKind.COMBAT: lambda e, s, p, i: (
            combat_view.handle_combat_input(e, s, s.combat_state)
            if s.combat_state is not None
            else True
        ),
        ScreenKind.CINEMATIC: _cinematic,
        ScreenKind.DEATH: death_screen.handle_death_input,
        ScreenKind.DEATH_SUMMARY: death_screen.handle_death_summary_input,
        ScreenKind.HALL_OF_DEAD: death_screen.handle_hall_of_dead_input,
        ScreenKind.JACK_OUT: jack_out_view.handle_jack_out_input,
        ScreenKind.REWARD: reward_view.handle_reward_input,
        ScreenKind.DEBRIEF: debrief_view.handle_debrief_input,
        ScreenKind.SAVE_LOAD: save_load_view.handle_save_load_input,
        ScreenKind.HELP: help_view.handle_help_input,
        ScreenKind.SETTINGS: settings_view.handle_settings_input,
        ScreenKind.ENDINGS_BROWSER: menu_screen.handle_endings_browser_input,
        ScreenKind.TELEMETRY_STATS: menu_screen.handle_telemetry_stats_input,
        ScreenKind.SALVATION_INTRO: salvation_view.handle_salvation_intro_input,
        ScreenKind.SALVATION_EPILOGUE: salvation_view.handle_salvation_epilogue_input,
        ScreenKind.SALVATION_ENDING: salvation_view.handle_salvation_ending_input,
    }


def _advance_graphic_novel_scene(
    state: AppState, forward: bool = True, full_skip: bool = False
) -> None:
    """Shared GN advance logic (extracted from inline _handle_input)."""
    scenes = state.gn_scenes
    if not scenes:
        state.screen = ScreenKind.MENU
        return
    if not (0 <= state.gn_scene_index < len(scenes)):
        state.screen = ScreenKind.MENU
        return
    scene = scenes[state.gn_scene_index]
    if not scene.dialogue:
        state.screen = ScreenKind.MENU
        return
    if not full_skip:
        # Step to next dialogue
        if state.gn_dialogue_index < len(scene.dialogue) - 1:
            state.gn_dialogue_index += 1
            state.gn_elapsed_ms = 0.0
            return
    # Full skip or end of dialogue → next scene
    if state.gn_scene_index < len(scenes) - 1:
        state.gn_scene_index += 1
        state.gn_dialogue_index = 0
        state.gn_elapsed_ms = 0.0
    else:
        state.screen = ScreenKind.MENU


_DISPATCH: dict[ScreenKind, InputFn] | None = None


def handle_current_screen_input(
    event: object,
    state: AppState,
    prog_registry: ProgramRegistry | None = None,
    ice_registry: IceRegistry | None = None,
) -> bool:
    """Phase D-2 deep4: dispatch input to current screen's handler.

    Replaces the 30-branch if/elif chain in app.py:_handle_input().
    Lazy-builds the dispatch table on first call.
    """
    global _DISPATCH
    if _DISPATCH is None:
        _DISPATCH = _build_input_dispatch()
    fn = _DISPATCH.get(state.screen)
    if fn is None:
        return True
    result = fn(event, state, prog_registry, ice_registry)
    return bool(result) if result is not None else True
