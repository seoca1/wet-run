"""Main loop per-screen tick advancement (Phase D-2 deep3).

Extracted from app.py:_main_inner() so app.py stays focused on the
outer tcod event loop, while per-screen tick logic lives in a focused
module.

Each screen that needs frame-by-frame state advancement registers a
handler here. Screens that don't need it (e.g. MENU, HUB, SETTINGS) are
no-ops and don't appear in the dispatch table.
"""

from __future__ import annotations

from ..combat.performance_integration import PerfTracker, integrate_with_game_loop
from ..combat.registry import IceRegistry, ProgramRegistry
from ..combat.state import step_combat, tick_dixie_ally
from . import hacking_view
from .arc_phase import advance_arc_phase
from .auto_play_tempo import get_tempo_multiplier
from .combat_tick import maybe_boss_phase_transition
from .state import AppState, ScreenKind


def _advance_graphic_novel(state: AppState, delta_s: float) -> None:
    """Tick GN: dialogue timer, advance to next line/scene on completion."""
    if not state.gn_scenes:
        return
    tempo_mult = get_tempo_multiplier(state.tempo_mode)
    state.gn_elapsed_ms += delta_s * 1000 * tempo_mult
    if state.gn_paused:
        return
    scenes = state.gn_scenes
    if not (0 <= state.gn_scene_index < len(scenes)):
        return
    scene = scenes[state.gn_scene_index]
    if not (scene.dialogue and 0 <= state.gn_dialogue_index < len(scene.dialogue)):
        return
    dialogue = scene.dialogue[state.gn_dialogue_index]
    if state.gn_elapsed_ms < dialogue.duration_ms:
        return
    if state.gn_dialogue_index < len(scene.dialogue) - 1:
        state.gn_dialogue_index += 1
        state.gn_elapsed_ms = 0.0
    elif state.gn_scene_index < len(scenes) - 1:
        state.gn_scene_index += 1
        state.gn_dialogue_index = 0
        state.gn_elapsed_ms = 0.0
    else:
        state.screen = ScreenKind.MENU


def _advance_chapter(state: AppState, delta_s: float) -> None:
    """Tick CHAPTER: typing effect, transition to ARC_PHASE on completion."""
    if not state.chapter_data:
        return
    state.chapter_elapsed_ms += delta_s * 1000
    cd = state.chapter_data
    typed = int(state.chapter_elapsed_ms / cd.char_delay_ms)
    state.chapter_typed_chars = min(typed, len(cd.excerpt_en))
    if state.chapter_elapsed_ms < cd.duration_ms:
        return
    if state.current_arc is not None:
        state.current_chapter_index = 0
        state.current_phase_index = 0
        state.current_beat_index = 0
        state.phase_elapsed_ms = 0.0
        state.phase_typed_chars = 0
        state.screen = ScreenKind.ARC_PHASE
    else:
        state.screen = ScreenKind.HUB


def _advance_arc_phase_screen(state: AppState, delta_s: float) -> None:
    """Tick ARC_PHASE: beat typing, advance on completion."""
    if state.current_arc is None:
        return
    arc = state.current_arc
    if state.current_chapter_index >= len(arc.chapters):
        return
    chapter = arc.chapters[state.current_chapter_index]
    if state.current_phase_index >= len(chapter.phases):
        return
    phase = chapter.phases[state.current_phase_index]
    if not phase.beats:
        return
    if state.current_beat_index < len(phase.beats):
        state.phase_elapsed_ms += delta_s * 1000
        beat = phase.beats[state.current_beat_index]
        text = beat.text_en
        typed = int(state.phase_elapsed_ms / 30)
        state.phase_typed_chars = min(typed, len(text))
        typecomplete_ms = len(text) * 30
        if state.phase_elapsed_ms >= typecomplete_ms + 50:
            state.phase_elapsed_ms = 0.0
            state.phase_typed_chars = 0
            advance_arc_phase(state)
    else:
        # All beats done — accumulate elapsed time so SPACE advances
        state.phase_elapsed_ms += delta_s * 1000


def _advance_combat(
    state: AppState,
    delta_s: float,
    ice_registry: IceRegistry | None,
    program_registry: ProgramRegistry | None,
) -> None:
    """Tick COMBAT: step_combat + boss phase transition + Dixie ally (Pillar 5)."""
    if state.combat_state is None:
        return
    step_combat(state.combat_state)
    tick_dixie_ally(state.combat_state, state)
    maybe_boss_phase_transition(
        state,
        ice_registry=ice_registry,
        program_registry=program_registry,
    )


def _advance_hack(state: AppState, delta_s: float) -> None:
    """Tick HACK: System Probe minigame tick."""
    hacking_view.step_hack(state, delta_s)


# Dispatch table: ScreenKind -> tick function (state, delta_s) -> None
# (combat + boss phase transition need extra args; pass through)
def _combat_handler_with_args(
    state: AppState,
    delta_s: float,
    **_: object,
) -> None:
    """Combat handler signature includes registries."""
    pass  # not used directly; main_loop handles


def tick_current_screen(
    state: AppState,
    delta_s: float,
    ice_registry: IceRegistry | None = None,
    program_registry: ProgramRegistry | None = None,
) -> None:
    """Phase D-2 deep3: dispatch tick handler to current screen.

    Replaces the per-screen tick logic in _main_inner() (130 LOC) with
    a focused dispatch. Screens that don't need ticking are no-ops.
    """
    if state.perf_tracker is None:
        state.perf_tracker = PerfTracker()

    def _tick_logic() -> None:
        """Focused per-tick dispatch — defers to ``_do_tick_logic`` once.

        The closure exists so ``integrate_with_game_loop`` receives a
        single zero-arg callable for perf-tracker instrumentation,
        rather than the broader ``tick_current_screen`` signature
        (state + delta_s + registries). Screens that don't need
        ticking remain no-ops.
        """
        _do_tick_logic(state, delta_s, ice_registry, program_registry)

    assert state.perf_tracker is not None
    integrate_with_game_loop(state.perf_tracker, state.screen.value, _tick_logic)


def _do_tick_logic(
    state: AppState,
    delta_s: float,
    ice_registry: IceRegistry | None = None,
    program_registry: ProgramRegistry | None = None,
) -> None:
    """Actual tick logic, wrapped by performance tracker."""
    screen = state.screen
    if screen is ScreenKind.GRAPHIC_NOVEL:
        _advance_graphic_novel(state, delta_s)
    elif screen is ScreenKind.CHAPTER:
        _advance_chapter(state, delta_s)
    elif screen is ScreenKind.ARC_PHASE:
        _advance_arc_phase_screen(state, delta_s)
    elif screen is ScreenKind.COMBAT:
        _advance_combat(state, delta_s, ice_registry, program_registry)
    elif screen is ScreenKind.HACK:
        _advance_hack(state, delta_s)
