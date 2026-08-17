"""Tests for engine.arc_phase — beat/phase/chapter transitions.

Coverage target for src/wet_run/engine/arc_phase.py.
"""

from __future__ import annotations

from wet_run.engine.arc_phase import advance_arc_phase
from wet_run.engine.chapter_cutscene import (
    ArcData,
    BeatData,
    ChapterData,
    PhaseData,
)
from wet_run.engine.state import AppState, ScreenKind


def _beat(beat_id: str = "b1", text_en: str = "Hello.", text_ko: str = "안녕.") -> BeatData:
    return BeatData(beat_id=beat_id, type="dialogue", text_en=text_en, text_ko=text_ko)


def _phase(phase_id: str, beats: tuple[BeatData, ...]) -> PhaseData:
    return PhaseData(
        phase_id=phase_id,
        phase_index=0,
        title_en=phase_id,
        title_ko=phase_id,
        description_en="",
        description_ko="",
        beats=beats,
    )


def _chapter(chapter_id: str, phases: tuple[PhaseData, ...]) -> ChapterData:
    return ChapterData(
        chapter_number=1,
        chapter_id=chapter_id,
        title_en=chapter_id,
        title_ko=chapter_id,
        description_en="",
        description_ko="",
        cutscene_start=None,
        cutscene_mid=None,
        cutscene_end=None,
        phases=phases,
        ending_type="continue",
        next_chapter_id=None,
        is_playable=True,
    )


def _arc(chapters: tuple[ChapterData, ...]) -> ArcData:
    return ArcData(
        character="case",
        arc_id="arc-1",
        title_en="Arc 1",
        title_ko="아크 1",
        description_en="",
        description_ko="",
        chapters=chapters,
    )


# ----------------------------------------------------------------------------
# No arc / end-of-arc cases
# ----------------------------------------------------------------------------


class TestAdvanceArcEdgeCases:
    def test_none_arc_returns_to_menu(self):
        state = AppState()
        state.current_arc = None
        state.screen = ScreenKind.ARC_PHASE
        advance_arc_phase(state)
        assert state.screen == ScreenKind.MENU

    def test_chapter_index_past_end_returns_to_menu(self):
        chapter = _chapter("ch1", (_phase("p1", (_beat(),)),))
        arc = _arc((chapter,))
        state = AppState()
        state.current_arc = arc
        state.current_chapter_index = 5  # past len(chapters) = 1
        state.current_phase_index = 0
        advance_arc_phase(state)
        assert state.screen == ScreenKind.MENU


# ----------------------------------------------------------------------------
# Chapter transitions
# ----------------------------------------------------------------------------


class TestChapterTransitions:
    def test_phase_index_past_end_advances_chapter(self):
        phase1 = _phase("p1", (_beat(),))
        phase2 = _phase("p2", (_beat(),))
        chapter1 = _chapter("ch1", (phase1, phase2))
        chapter2 = _chapter("ch2", (_phase("p1", (_beat(),)),))
        arc = _arc((chapter1, chapter2))

        state = AppState()
        state.current_arc = arc
        state.current_chapter_index = 0
        state.current_phase_index = 5  # past len(chapter1.phases) = 2
        state.current_phase_elapsed_ms = 100.0
        state.phase_typed_chars = 10
        state.screen = ScreenKind.ARC_PHASE

        advance_arc_phase(state)

        assert state.current_chapter_index == 1
        assert state.current_phase_index == 0
        assert state.current_beat_index == 0
        assert state.phase_elapsed_ms == 0.0
        assert state.phase_typed_chars == 0

    def test_phase_index_past_end_within_chapter_does_not_advance_chapter(self):
        phase1 = _phase("p1", (_beat(),))
        phase2 = _phase("p2", (_beat(),))
        chapter1 = _chapter("ch1", (phase1, phase2))
        arc = _arc((chapter1,))

        state = AppState()
        state.current_arc = arc
        state.current_chapter_index = 0
        state.current_phase_index = 5
        state.screen = ScreenKind.ARC_PHASE

        # Phase index past end of chapter 1's phases → advance to next phase/chapter
        # chapter 1 has 2 phases, index 5 is past end, but chapter 1 itself is the last
        advance_arc_phase(state)

        # Per the code: it advances chapter first (since past end of phases),
        # then checks if past end of chapters → returns to MENU
        assert state.screen == ScreenKind.MENU


# ----------------------------------------------------------------------------
# Phase transitions
# ----------------------------------------------------------------------------


class TestPhaseTransitions:
    def test_beat_index_past_end_advances_phase(self):
        beat1 = _beat()
        beat2 = _beat("b2")
        phase1 = _phase("p1", (beat1, beat2))
        phase2 = _phase("p2", (_beat(),))
        chapter = _chapter("ch1", (phase1, phase2))
        arc = _arc((chapter,))

        state = AppState()
        state.current_arc = arc
        state.current_chapter_index = 0
        state.current_phase_index = 0
        state.current_beat_index = 5  # past len(phase1.beats) = 2
        state.phase_elapsed_ms = 200.0
        state.phase_typed_chars = 15
        state.screen = ScreenKind.ARC_PHASE

        advance_arc_phase(state)

        assert state.current_phase_index == 1
        assert state.current_beat_index == 0
        assert state.phase_elapsed_ms == 0.0
        assert state.phase_typed_chars == 0
        # Still in ARC_PHASE since chapter/chapter count not exceeded
        assert state.screen == ScreenKind.ARC_PHASE


# ----------------------------------------------------------------------------
# Beat advancement
# ----------------------------------------------------------------------------


class TestBeatAdvancement:
    def test_normal_advance_to_next_beat(self):
        beat1 = _beat("b1")
        beat2 = _beat("b2")
        beat3 = _beat("b3")
        phase = _phase("p1", (beat1, beat2, beat3))
        chapter = _chapter("ch1", (phase,))
        arc = _arc((chapter,))

        state = AppState()
        state.current_arc = arc
        state.current_chapter_index = 0
        state.current_phase_index = 0
        state.current_beat_index = 0
        state.phase_typed_chars = 8  # Nonzero to verify reset
        state.screen = ScreenKind.ARC_PHASE

        advance_arc_phase(state)

        assert state.current_beat_index == 1
        assert state.phase_typed_chars == 0  # Reset on beat advance

    def test_multiple_beats_advance(self):
        phase = _phase("p1", (_beat("b1"), _beat("b2"), _beat("b3")))
        chapter = _chapter("ch1", (phase,))
        arc = _arc((chapter,))

        state = AppState()
        state.current_arc = arc
        state.current_chapter_index = 0
        state.current_phase_index = 0
        state.current_beat_index = 0

        advance_arc_phase(state)
        assert state.current_beat_index == 1

        advance_arc_phase(state)
        assert state.current_beat_index == 2
