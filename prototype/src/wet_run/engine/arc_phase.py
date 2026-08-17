"""ARC_PHASE state advancement.

Phase D-2: extracted from app.py to reduce main dispatcher size.
Handles beat/phase/chapter transitions in ARC_PHASE screen.
"""

from __future__ import annotations

from .state import AppState, ScreenKind


def advance_arc_phase(state: AppState) -> None:
    """Advance to the next beat, phase, or chapter in ARC_PHASE."""
    arc = state.current_arc
    if arc is None:
        state.screen = ScreenKind.MENU
        return

    if state.current_chapter_index >= len(arc.chapters):
        state.screen = ScreenKind.MENU
        return

    chapter = arc.chapters[state.current_chapter_index]
    if state.current_phase_index >= len(chapter.phases):
        state.current_chapter_index += 1
        state.current_phase_index = 0
        state.current_beat_index = 0
        state.phase_elapsed_ms = 0.0
        state.phase_typed_chars = 0
        if state.current_chapter_index >= len(arc.chapters):
            state.screen = ScreenKind.MENU
        return

    phase = chapter.phases[state.current_phase_index]
    if state.current_beat_index >= len(phase.beats):
        state.current_phase_index += 1
        state.current_beat_index = 0
        state.phase_elapsed_ms = 0.0
        state.phase_typed_chars = 0
        return

    state.current_beat_index += 1
    state.phase_typed_chars = 0
