"""Unit tests for ``engine/phase_view.py``.

``render_arc_phase`` is a tcod console painter — we can't easily
verify the pixels it draws, but the pure logic *around* the paint
(beat-type color lookup, beat progression math, text wrapping)
is what matters and what regresses.  These tests focus on those
pure functions and on a ``tcod.console.Console`` mock that captures
each ``print()`` call.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from wet_run.engine import phase_view
from wet_run.engine.chapter_cutscene import BeatData, PhaseData
from wet_run.i18n import Translator

# ---------------------------------------------------------------------------
# Helpers — a Console stub that records every print() call.
# ---------------------------------------------------------------------------


class _FakeConsole:
    def __init__(self, width: int = 80, height: int = 24) -> None:
        self.width = width
        self.height = height
        self.prints: list[dict] = []

    def clear(self) -> None:
        self.prints.append({"op": "clear"})

    def print(self, x: int, y: int, string: str = "", fg: tuple = (255, 255, 255)) -> None:
        self.prints.append({"op": "print", "x": x, "y": y, "string": string, "fg": fg})


def _beat(
    text_en: str = "Hello world.",
    text_ko: str = "안녕하세요.",
    beat_type: str = "interior_monologue",
) -> BeatData:
    return BeatData(beat_id="b0", type=beat_type, text_en=text_en, text_ko=text_ko)


def _phase(beats: list[BeatData], title_en: str = "Title", title_ko: str = "제목") -> PhaseData:
    return PhaseData(
        phase_id="p0",
        phase_index=0,
        title_en=title_en,
        title_ko=title_ko,
        description_en="",
        description_ko="",
        beats=tuple(beats),
    )


# ---------------------------------------------------------------------------
# BEAT_TYPE_COLORS
# ---------------------------------------------------------------------------


class TestBeatTypeColors:
    def test_all_four_known_beat_types_have_colors(self) -> None:
        for bt in ("interior_monologue", "action", "dialogue", "combat"):
            assert bt in phase_view.BEAT_TYPE_COLORS
            assert len(phase_view.BEAT_TYPE_COLORS[bt]) == 3  # (r, g, b)

    def test_unknown_beat_type_does_not_crash_render(self) -> None:
        """``render_arc_phase`` must default the color gracefully when a
        phase has a beat with an unknown type.  We verify it doesn't
        throw and prints at least one line."""
        console = _FakeConsole()
        phase = _phase([_beat(beat_type="totally-unknown")])
        t = Translator(lang="en")
        phase_view.render_arc_phase(console, phase, 0, 5, 100.0, 200.0, t)
        assert len(console.prints) > 0


# ---------------------------------------------------------------------------
# tick_arc_phase
# ---------------------------------------------------------------------------


class TestTickArcPhase:
    def test_advances_typed_chars_proportional_to_elapsed(self) -> None:
        phase = _phase([_beat("Hello world!")])  # 12 chars
        typed, advance = phase_view.tick_arc_phase(phase, 0, 300.0, 0, char_delay_ms=30)
        assert typed == 10  # 300/30 = 10
        assert advance is False

    def test_caps_at_beat_length(self) -> None:
        phase = _phase([_beat("Hi")])  # 2 chars
        typed, advance = phase_view.tick_arc_phase(phase, 0, 1000.0, 0, char_delay_ms=30)
        assert typed == 2
        assert advance is True

    def test_completes_beat_when_typed_reaches_length(self) -> None:
        phase = _phase([_beat("Hi")])  # 2 chars
        typed, advance = phase_view.tick_arc_phase(phase, 0, 60.0, 0, char_delay_ms=30)
        assert typed == 2
        assert advance is True

    def test_advances_to_next_beat_when_index_past_end(self) -> None:
        phase = _phase([_beat("a"), _beat("b")])
        # beat_index=1 (last beat), no more beats
        typed, advance = phase_view.tick_arc_phase(phase, 2, 100.0, 0, char_delay_ms=30)
        assert advance is True

    def test_zero_delay_means_immediate_complete(self) -> None:
        phase = _phase([_beat("Hello")])
        typed, advance = phase_view.tick_arc_phase(phase, 0, 0.0, 0, char_delay_ms=0)
        assert typed == 5
        assert advance is True

    def test_ignores_already_typed_chars(self) -> None:
        """The function does not subtract ``typed_chars`` — it computes
        fresh from ``beat_elapsed_ms``.  We verify the contract
        documented in the function: returns the new typed count for
        the *current* beat given elapsed time."""
        phase = _phase([_beat("Hello world!")])  # 12 chars
        # elapsed 600ms at 30ms/char = 20, capped at 12
        typed, _ = phase_view.tick_arc_phase(phase, 0, 600.0, 5, char_delay_ms=30)
        assert typed == 12


# ---------------------------------------------------------------------------
# render_arc_phase
# ---------------------------------------------------------------------------


class TestRenderArcPhase:
    def _translator(self, lang: str = "en") -> Translator:
        t = Translator(lang=lang)
        return t

    def test_uses_english_text_by_default(self) -> None:
        console = _FakeConsole()
        phase = _phase([_beat(text_en="EN-CONTENT", text_ko="KO내용")])
        phase_view.render_arc_phase(console, phase, 0, 100, 100.0, 100.0, self._translator("en"))
        flat = " ".join(p.get("string", "") for p in console.prints)
        assert "EN-CONTENT" in flat
        assert "KO내용" not in flat

    def test_uses_korean_text_when_lang_ko(self) -> None:
        console = _FakeConsole()
        phase = _phase([_beat(text_en="EN-CONTENT", text_ko="KO내용")])
        phase_view.render_arc_phase(console, phase, 0, 100, 100.0, 100.0, self._translator("ko"))
        flat = " ".join(p.get("string", "") for p in console.prints)
        assert "KO내용" in flat
        assert "EN-CONTENT" not in flat

    def test_completed_phase_shows_done(self) -> None:
        console = _FakeConsole()
        phase = _phase([_beat("a"), _beat("b")])
        # beat_index past end → "Phase complete."
        phase_view.render_arc_phase(console, phase, 5, 0, 0.0, 0.0, self._translator())
        flat = " ".join(p.get("string", "") for p in console.prints)
        assert "Phase complete" in flat

    def test_beat_progress_bar_reflects_typed_chars(self) -> None:
        console = _FakeConsole(width=40, height=10)
        phase = _phase([_beat("A" * 10)])  # 10 chars
        # typed=0 → no chars filled
        phase_view.render_arc_phase(console, phase, 0, 0, 0.0, 0.0, self._translator())
        flat = " ".join(p.get("string", "") for p in console.prints)
        # Beat 1/1: [N% of bar] format present
        assert "Beat 1/1" in flat
        assert "0%" in flat  # No chars typed → 0%

    def test_status_message_shown_when_provided(self) -> None:
        console = _FakeConsole()
        phase = _phase([_beat("hello")])
        state = MagicMock()
        state.status_messages = [">>> Mission won! VICTORY"]
        phase_view.render_arc_phase(
            console,
            phase,
            0,
            5,
            50.0,
            50.0,
            self._translator(),
            state=state,
        )
        flat = " ".join(p.get("string", "") for p in console.prints)
        assert "VICTORY" in flat

    def test_controls_hint_shown_when_no_status(self) -> None:
        console = _FakeConsole()
        phase = _phase([_beat("hi")])
        state = MagicMock()
        state.status_messages = []
        phase_view.render_arc_phase(
            console,
            phase,
            0,
            2,
            30.0,
            30.0,
            self._translator(),
            state=state,
        )
        flat = " ".join(p.get("string", "") for p in console.prints)
        assert "ENTER" in flat
        assert "Next Beat" in flat
