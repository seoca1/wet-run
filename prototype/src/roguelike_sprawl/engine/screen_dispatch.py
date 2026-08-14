"""Screen render dispatch table (Phase D-2 deep2).

Replaces the ~30-branch if/elif chain in app.py:_render() with a
dict-based dispatch. Each ScreenKind maps to a callable that takes
(console, t, state) and optional registries.

The dispatch table is built lazily on first call to avoid importing
heavy modules at app.py load time.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import tcod.console

from ..combat.registry import IceRegistry, ProgramRegistry
from .state import AppState, ScreenKind

if TYPE_CHECKING:
    from ..i18n import Translator


# Per-screen render signature: (console, t, state, **optional) -> None
RenderFn = Callable[..., None]


def _build_dispatch() -> dict[ScreenKind, RenderFn]:
    """Build the screen→render dispatch table (lazy import)."""
    from . import (
        chapter_view,
        config,
        cyberspace_browser,
        debrief_view,
        dungeon_view,
        event_view,
        graphic_novel_view,
        hacking_view,
        help_view,
        jack_out_view,
        npc_view,
        phase_view,
        reward_view,
        salvation_view,
        save_load_view,
        save_progress,
        settings_view,
        story_cinematic,
    )
    from . import death as death_screen
    from . import (
        hub as hub_screen,
    )
    from . import (
        menu as menu_screen,
    )
    from . import story_view as story_screen
    from .graphic_novel_view import render_graphic_novel_screen

    def _arc_phase(console: tcod.console.Console, t: Translator, state: AppState) -> None:
        """Render the ARC_PHASE screen — the inner beats/phases of a chapter.

        Defensive fallbacks render error messages for missing arc, exhausted
        chapter list, or exhausted phase list before delegating to
        ``phase_view.render_arc_phase``.
        """
        if state.current_arc is None:
            console.clear(bg=(0, 0, 0))
            console.print(x=2, y=2, string="=== NO ARC DATA ===", fg=(255, 0, 0))
            console.print(x=2, y=4, string="Play through CHAPTER first.", fg=(128, 128, 128))
            return
        arc = state.current_arc
        if state.current_chapter_index >= len(arc.chapters):
            console.clear(bg=(0, 0, 0))
            console.print(x=2, y=2, string="All arcs complete.", fg=(180, 180, 100))
            return
        chapter = arc.chapters[state.current_chapter_index]
        if state.current_phase_index >= len(chapter.phases):
            console.clear(bg=(0, 0, 0))
            console.print(x=2, y=2, string="Arc complete.", fg=(180, 180, 100))
            return
        phase = chapter.phases[state.current_phase_index]
        phase_view.render_arc_phase(
            console,
            phase,
            state.current_beat_index,
            state.phase_typed_chars,
            0.0,
            state.phase_elapsed_ms,
            t,
        )

    def _cyberspace_map(console: tcod.console.Console, t: Translator, state: AppState) -> None:
        """Render the CYBERSPACE_MAP screen — top-down node graph.

        Defensive fallback renders an error if ``state.world_map`` is missing,
        otherwise delegates to ``cyberspace_map_view.render_cyberspace_map``.
        """
        if not hasattr(state, "world_map") or state.world_map is None:
            console.clear(bg=(0, 0, 0))
            console.print(x=2, y=2, string="=== NO WORLD DATA ===", fg=(255, 0, 0))
            console.print(
                x=2, y=4, string="Start a mission from the Hub first.", fg=(128, 128, 128)
            )
            return
        from . import cyberspace_map_view

        cyberspace_map_view.render_cyberspace_map(console, state)

    def _graphic_novel_menu(console: tcod.console.Console, t: Translator, state: AppState) -> None:
        """Render the GRAPHIC_NOVEL_MENU screen — prologue/character pick list."""
        has_save = getattr(state, "has_save", False)
        graphic_novel_view.render_graphic_novel_menu(console, t, state.gn_menu_selected, has_save)

    def _graphic_novel_ending(
        console: tcod.console.Console, t: Translator, state: AppState
    ) -> None:
        """Render the GRAPHIC_NOVEL_ENDING_MENU screen — post-story ending picker."""
        graphic_novel_view.render_graphic_novel_ending_menu(
            console, t, state.gn_mode, state.menu_selected_index
        )

    def _gn_screen(console: tcod.console.Console, t: Translator, state: AppState) -> None:
        """Render the active GRAPHIC_NOVEL screen — auto-playing story scenes."""
        render_graphic_novel_screen(console, state, t)

    def _hub(console: tcod.console.Console, t: Translator, state: AppState) -> None:
        """Render the HUB screen — Sprawl city central menu between missions."""
        hub_screen.render_hub(console, t, state)

    def _npc(console: tcod.console.Console, t: Translator, state: AppState) -> None:
        """Render the NPC dialog screen, or an error if ``state.npc_state`` is missing."""
        if state.npc_state is not None:
            npc_view.render_npc(console, t, state, state.npc_state)
        else:
            console.clear(bg=(0, 0, 0))
            console.print(x=2, y=2, string="=== NO NPC STATE ===", fg=(255, 0, 0))

    def _event(console: tcod.console.Console, t: Translator, state: AppState) -> None:
        """Render the EVENT screen (story event dialog) or an error if no event is active."""
        if state.active_event is not None:
            event_view.render_event_story(console, t, state, state.active_event)
        else:
            console.clear(bg=(0, 0, 0))
            console.print(x=2, y=2, string="=== NO ACTIVE EVENT ===", fg=(255, 0, 0))

    def _story(console: tcod.console.Console, t: Translator, state: AppState) -> None:
        """Render the STORY screen — aftermath or story registry from story_aftermath_id."""
        registry = story_screen.StoryRegistry.load(config.DATA_DIR)
        story_screen.render_story(console, state, registry, state.story_aftermath_id)

    def _chapter(console: tcod.console.Console, t: Translator, state: AppState) -> None:
        """Render the CHAPTER screen (typed-reveal cinematic) or error if chapter_data is None."""
        if state.chapter_data:
            chapter_view.render_chapter(
                console,
                state.chapter_data,
                t,
                state.chapter_typed_chars,
                state.chapter_elapsed_ms,
            )
        else:
            console.clear(bg=(0, 0, 0))
            console.print(x=2, y=2, string="=== NO CHAPTER DATA ===", fg=(255, 0, 0))

    def _saved_progress(console: tcod.console.Console, t: Translator, state: AppState) -> None:
        """Render the SAVED_PROGRESS screen — last save summary with i18n title/options."""
        save_dir = config.DATA_DIR / "saves"
        summary = save_progress.get_progress_summary(save_dir=save_dir)
        console.clear()
        width = console.width
        title = "당신의 자키" if t.lang == "ko" else "Your Jockey"
        console.print(0, 0, "═" * width)
        console.print((width - len(title)) // 2, 0, f" {title} ")
        console.print(0, 1, "─" * width)
        if not summary.has_save:
            msg = "아직 자키가 없습니다" if t.lang == "ko" else "No save file yet"
            console.print((width - len(msg)) // 2, 8, msg)
            hint = "[1] NEW RUN  [2] 다른 캐릭터  [3] 메인메뉴"
            console.print((width - len(hint)) // 2, 14, hint)
        else:
            lines = save_progress.render_summary_lines(summary, t_lang=t.lang)
            y = 3
            for line in lines:
                console.print(4, y, line)
                y += 1
            y += 1
            console.print(4, y, "─" * 40)
            y += 1
            if t.lang == "ko":
                opts = [
                    "[1] 다른 캐릭터 스토리 보기",
                    "[2] 게임플레이 계속 (HUB)",
                    "[3] 메인메뉴",
                ]
            else:
                opts = [
                    "[1] Other character stories",
                    "[2] Continue gameplay (HUB)",
                    "[3] Main menu",
                ]
            for i, opt in enumerate(opts):
                console.print(4, y + i * 2, opt)

    def _matrix(
        console: tcod.console.Console,
        t: Translator,
        state: AppState,
        prog_registry: ProgramRegistry | None = None,
        ice_registry: IceRegistry | None = None,
    ) -> None:
        """Render the MATRIX screen — dungeon/matrix node grid with program/ICE registries."""
        dungeon_view.render_dungeon_matrix(console, t, state, prog_registry, ice_registry)

    def _combat(console: tcod.console.Console, t: Translator, state: AppState) -> None:
        """Render the COMBAT screen (RT-MS) or error if combat_state is missing."""
        if state.combat_state is not None:
            from . import combat_view

            combat_view.render_combat(console, t, state, state.combat_state)
        else:
            console.clear(bg=(0, 0, 0))
            console.print(x=2, y=2, string="=== COMBAT ERROR ===", fg=(255, 0, 0))
            console.print(x=2, y=4, string="No combat state loaded", fg=(128, 128, 128))

    def _cinematic(console: tcod.console.Console, t: Translator, state: AppState) -> None:
        """Render the CINEMATIC screen (story_cinematic) or error if cinematic_state is missing."""
        if state.cinematic_state is not None:
            elapsed_ms = int(state.demo_elapsed_s * 1000)
            story_cinematic.render_cinematic(console, t, state, state.cinematic_state, elapsed_ms)
        else:
            console.clear(bg=(0, 0, 0))
            console.print(x=2, y=2, string="=== CINEMATIC ERROR ===", fg=(255, 0, 0))
            console.print(x=2, y=4, string="No cinematic state loaded", fg=(128, 128, 128))

    return {
        ScreenKind.MENU: menu_screen.render_menu,
        ScreenKind.GRAPHIC_NOVEL_MENU: _graphic_novel_menu,
        ScreenKind.GRAPHIC_NOVEL: _gn_screen,
        ScreenKind.SAVED_PROGRESS: _saved_progress,
        ScreenKind.HUB: _hub,
        ScreenKind.NPC: _npc,
        ScreenKind.HACK: hacking_view.render_hack,
        ScreenKind.ENDING: menu_screen.render_ending,
        ScreenKind.GRAPHIC_NOVEL_ENDING_MENU: _graphic_novel_ending,
        ScreenKind.SAVE_SLOT_SELECT: save_load_view.render_save_load,
        ScreenKind.EVENT: _event,
        ScreenKind.STORY: _story,
        ScreenKind.ARC_PHASE: _arc_phase,
        ScreenKind.CYBERSPACE_BROWSER: cyberspace_browser.render_cyberspace_browser,
        ScreenKind.CYBERSPACE_MAP: _cyberspace_map,
        ScreenKind.CHARACTER_SELECT: menu_screen.render_character_select,
        ScreenKind.DECK_SELECT: menu_screen.render_deck_select,
        ScreenKind.CHAPTER: _chapter,
        ScreenKind.MATRIX: _matrix,
        ScreenKind.COMBAT: _combat,
        ScreenKind.CINEMATIC: _cinematic,
        ScreenKind.DEATH: death_screen.render_death_screen,
        ScreenKind.DEATH_SUMMARY: death_screen.render_death_summary_screen,
        ScreenKind.HALL_OF_DEAD: death_screen.render_hall_of_dead_screen,
        ScreenKind.JACK_OUT: jack_out_view.render_jack_out,
        ScreenKind.REWARD: reward_view.render_reward,
        ScreenKind.DEBRIEF: debrief_view.render_debrief,
        ScreenKind.SAVE_LOAD: save_load_view.render_save_load,
        ScreenKind.HELP: help_view.render_help,
        ScreenKind.SETTINGS: settings_view.render_settings,
        ScreenKind.ENDINGS_BROWSER: menu_screen.render_endings_browser,
        ScreenKind.TELEMETRY_STATS: menu_screen.render_telemetry_summary,
        ScreenKind.SALVATION_INTRO: salvation_view.render_salvation_intro,
        ScreenKind.SALVATION_EPILOGUE: salvation_view.render_salvation_epilogue,
        ScreenKind.SALVATION_ENDING: salvation_view.render_salvation_ending,
    }


_DISPATCH: dict[ScreenKind, RenderFn] | None = None


def render_current_screen(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    prog_registry: ProgramRegistry | None = None,
    ice_registry: IceRegistry | None = None,
) -> None:
    """Phase D-2 deep2: dispatch to current screen's render function.

    Replaces the if/elif chain in app.py:_render() with a dict lookup.
    Lazy-builds the dispatch table on first call.
    """
    global _DISPATCH
    if _DISPATCH is None:
        _DISPATCH = _build_dispatch()
    fn = _DISPATCH.get(state.screen)
    if fn is None:
        console.clear(bg=(0, 0, 0))
        console.print(x=2, y=2, string=f"=== NO RENDERER: {state.screen} ===", fg=(255, 0, 0))
        return
    # Pass extra kwargs only to handlers that accept them (MATRIX, COMBAT)
    if state.screen in (ScreenKind.MATRIX,):
        fn(console, t, state, prog_registry=prog_registry, ice_registry=ice_registry)
    else:
        fn(console, t, state)
