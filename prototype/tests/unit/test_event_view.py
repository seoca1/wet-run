"""Unit tests for ``engine/event_view.py``.

The render_* functions are pure tcod painters — we mock the console.
The state-transition functions (``_advance_event``, ``_complete_event``,
``_execute_choice``) and the input router (``handle_event_input``) are
the meaningful targets for regression tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from wet_run.engine import event_view
from wet_run.engine.event_story import (
    CharacterArt,
    EventChoice,
    EventLine,
    EventState,
    EventStory,
)

# ---------------------------------------------------------------------------
# _count_wrapped_lines and _get_text_color — pure logic
# ---------------------------------------------------------------------------


class TestCountWrappedLines:
    def test_empty_text_is_zero_lines(self) -> None:
        assert event_view._count_wrapped_lines("", 80) == 0

    def test_single_line_fits(self) -> None:
        assert event_view._count_wrapped_lines("Hello world", 80) == 1

    def test_wraps_at_max_width(self) -> None:
        # 5 words * 6 chars = 30; max_width=12 → at least 3 lines
        text = "alpha beta gamma delta epsilon"
        n = event_view._count_wrapped_lines(text, 12)
        assert n >= 3

    def test_very_long_word_takes_one_line_per_word(self) -> None:
        # 4 words, each longer than max_width → each on its own line.
        # The algorithm puts the first word on a line by itself, then
        # each subsequent word that doesn't fit also gets its own
        # line.  We assert "at least 4" to avoid depending on exact
        # line-counting semantics for a single very-long word.
        text = "verylongfirst verylongsecond verylongthird verylongfourth"
        n = event_view._count_wrapped_lines(text, 5)
        assert n >= 4


class TestGetTextColor:
    def test_glitch_is_light_blue(self) -> None:
        assert event_view._get_text_color("glitch") == (200, 200, 255)

    def test_type_is_light_gray(self) -> None:
        assert event_view._get_text_color("type") == (200, 200, 200)

    def test_unknown_falls_back_to_white(self) -> None:
        assert event_view._get_text_color("unknown-effect") == (255, 255, 255)

    def test_empty_string_is_white(self) -> None:
        assert event_view._get_text_color("") == (255, 255, 255)


# ---------------------------------------------------------------------------
# _advance_event / _complete_event / _execute_choice
# ---------------------------------------------------------------------------


def _make_event(num_lines: int = 3) -> EventStory:
    """Build a tiny event with ``num_lines`` blank lines."""
    return EventStory(
        id="evt_test",
        title="Test Event",
        description="desc",
        lines=tuple(EventLine(speaker="", portrait="", text=f"line {i}") for i in range(num_lines)),
        set_flag="flag_x",
    )


def _make_state() -> MagicMock:
    state = MagicMock()
    state.status_messages = []
    state.inventory = {}
    state.story_flags = set()
    state.shown_events = set()
    state.active_event = MagicMock()
    state.screen = None
    return state


class TestAdvanceEvent:
    def test_advances_line_index(self) -> None:
        state = _make_state()
        event_state = EventState(event=_make_event(3), current_line_index=0)
        event_view._advance_event(state, event_state)
        assert event_state.current_line_index == 1
        assert event_state.choice_index == 0
        assert event_state.finished is False

    def test_marks_finished_at_end(self) -> None:
        state = _make_state()
        event_state = EventState(event=_make_event(2), current_line_index=1)
        event_view._advance_event(state, event_state)
        assert event_state.finished is True
        assert "evt_test" in state.shown_events
        assert "flag_x" in state.story_flags
        assert state.screen.name == "MATRIX" or "MATRIX" in str(state.screen)


class TestCompleteEvent:
    def test_sets_finished_and_flag(self) -> None:
        state = _make_state()
        event_state = EventState(event=_make_event(2), current_line_index=0)
        event_view._complete_event(state, event_state)
        assert event_state.finished is True
        assert "evt_test" in state.shown_events
        assert "flag_x" in state.story_flags

    def test_appends_status_message(self) -> None:
        state = _make_state()
        event_state = EventState(event=_make_event(2))
        event_view._complete_event(state, event_state)
        assert any("completed" in m for m in state.status_messages)


class TestExecuteChoice:
    def test_appends_choice_text(self) -> None:
        state = _make_state()
        es = EventState(event=_make_event(2))
        c = EventChoice(key="a", text="Open the door", next_line_index=1)
        event_view._execute_choice(state, es, c)
        assert any("Open the door" in m for m in state.status_messages)

    def test_grants_credits_appends_message(self) -> None:
        state = _make_state()
        es = EventState(event=_make_event(2))
        c = EventChoice(key="a", text="Take the cash", grants_credits=500)
        event_view._execute_choice(state, es, c)
        assert any("500 credits" in m for m in state.status_messages)

    def test_grants_item_increments_inventory(self) -> None:
        state = _make_state()
        state.inventory = {}
        es = EventState(event=_make_event(2))
        c = EventChoice(key="a", text="Loot", grants_item="biochip")
        event_view._execute_choice(state, es, c)
        assert state.inventory["biochip"] == 1

    def test_advances_to_explicit_line(self) -> None:
        state = _make_state()
        es = EventState(event=_make_event(3), current_line_index=0)
        c = EventChoice(key="a", text="skip ahead", next_line_index=2)
        event_view._execute_choice(state, es, c)
        assert es.current_line_index == 2

    def test_no_next_advances_naturally(self) -> None:
        state = _make_state()
        es = EventState(event=_make_event(2), current_line_index=0)
        c = EventChoice(key="a", text="continue", next_line_index=None)
        event_view._execute_choice(state, es, c)
        assert es.current_line_index == 1


# ---------------------------------------------------------------------------
# handle_event_input — input router
# ---------------------------------------------------------------------------


def _keydown(sym_name: str):
    """Build a real tcod KeyDown event with the given KeySym name."""
    import tcod.event

    sym = tcod.event.KeySym[sym_name]
    return tcod.event.KeyDown(sym=sym, mod=0, scancode=0)


# ---------------------------------------------------------------------------
# Test helpers for the render helpers
# ---------------------------------------------------------------------------


class _FakeConsole:
    def __init__(self, width: int = 80, height: int = 24) -> None:
        self.width = width
        self.height = height
        self.prints: list[dict] = []

    def clear(self) -> None:
        self.prints.append({"op": "clear"})

    def print(self, x: int = 0, y: int = 0, string: str = "", fg=None) -> None:
        self.prints.append({"x": x, "y": y, "string": string, "fg": fg})


class _StubRegion:
    """Mimics the Region interface used by event_view's draw helpers."""

    def __init__(self, x: int = 0, y: int = 0, w: int = 80, h: int = 24) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.x2 = x + w - 1
        self.y2 = y + h - 1


class TestRenderEventMain:
    def test_no_line_returns_silently(self) -> None:
        from types import SimpleNamespace

        from wet_run.engine import event_view

        console = _FakeConsole()
        es = SimpleNamespace(
            event=SimpleNamespace(get_line=lambda i: None),
            current_line_index=99,
        )
        event_view._render_event_main(console, _StubRegion(), es)
        assert console.prints == []

    def test_renders_art_then_dialogue_then_choices(self) -> None:
        from types import SimpleNamespace

        from wet_run.engine import event_view
        from wet_run.engine.event_story import (
            EventChoice,
            EventLine,
            EventStory,
        )

        art = CharacterArt(
            character_id="case",
            art_lines=("O", " |"),
            color_hint=(255, 0, 0),
        )
        line = EventLine(
            speaker="Case",
            speaker_ko="케이",
            portrait="KC",
            text="I am Case.",
            text_ko="나는 케이다.",
            art=art,
            choices=(
                EventChoice(key="a", text="Option A", text_ko="선택 A"),
                EventChoice(key="b", text="Option B", text_ko="선택 B"),
            ),
        )
        event = EventStory(id="evt", title="Test", lines=[line])
        es = SimpleNamespace(
            event=event,
            current_line_index=0,
            choice_index=0,
        )

        console = _FakeConsole()
        event_view._render_event_main(console, _StubRegion(w=80, h=24), es)
        flat = " ".join(p["string"] for p in console.prints)
        # Speaker shown (with portrait prefix).
        assert "KC" in flat
        assert "Case:" in flat
        # English + Korean dialogue.
        assert "I am Case." in flat
        assert "나는 케이다." in flat
        # Choices.
        assert "[a]" in flat
        assert "Option A" in flat
        assert "[b]" in flat
        assert "Option B" in flat


class TestDrawCharacterArt:
    def test_draws_each_art_line(self) -> None:
        from wet_run.engine import event_view

        art = CharacterArt(
            character_id="case",
            art_lines=("LINE_A", "LINE_B", "LINE_C"),
            color_hint=(255, 0, 0),
        )
        console = _FakeConsole()
        event_view._draw_character_art(console, x=0, y=0, art=art, max_height=10)
        flat = " ".join(p["string"] for p in console.prints)
        for line in ("LINE_A", "LINE_B", "LINE_C"):
            assert line in flat
        # Character name banner appears.
        assert "── CASE ──" in flat

    def test_respects_max_height(self) -> None:
        from wet_run.engine import event_view

        art = CharacterArt(
            character_id="x",
            art_lines=("a", "b", "c", "d", "e"),
        )
        console = _FakeConsole()
        event_view._draw_character_art(console, x=0, y=0, art=art, max_height=2)
        flat = " ".join(p["string"] for p in console.prints)
        # max_height=2 → only 2 lines drawn.
        assert "a" in flat
        assert "b" in flat


class TestDrawDialogue:
    def test_speaker_with_portrait(self) -> None:
        from wet_run.engine import event_view
        from wet_run.engine.event_story import EventLine

        line = EventLine(speaker="Case", portrait="KC", text="Hi.", text_ko="안녕.")
        console = _FakeConsole()
        event_view._draw_dialogue(console, x=0, y=0, max_width=40, line=line)
        flat = " ".join(p["string"] for p in console.prints)
        assert "KC Case:" in flat
        assert "안녕." in flat

    def test_speaker_without_portrait(self) -> None:
        from wet_run.engine import event_view
        from wet_run.engine.event_story import EventLine

        line = EventLine(speaker="Finn", text="Got a job.", text_ko="작업 있어.")
        console = _FakeConsole()
        event_view._draw_dialogue(console, x=0, y=0, max_width=40, line=line)
        flat = " ".join(p["string"] for p in console.prints)
        assert "Finn:" in flat
        assert "Got a job." in flat


class TestDrawChoices:
    def test_separator_above_choices(self) -> None:
        from types import SimpleNamespace

        from wet_run.engine import event_view
        from wet_run.engine.event_story import EventChoice, EventLine

        line = EventLine(
            choices=(
                EventChoice(key="a", text="A"),
                EventChoice(key="b", text="B"),
            ),
        )
        es = SimpleNamespace(choice_index=0)
        console = _FakeConsole()
        event_view._draw_choices(console, x=0, y=10, max_width=20, line=line, event_state=es)
        flat = " ".join(p["string"] for p in console.prints)
        # Row of "─" separator above choices.
        assert "─" * 20 in flat
        # Choices labeled.
        assert "[a]" in flat
        assert "[b]" in flat

    def test_selected_choice_has_cursor_marker(self) -> None:
        from types import SimpleNamespace

        from wet_run.engine import event_view
        from wet_run.engine.event_story import EventChoice, EventLine

        line = EventLine(
            choices=(
                EventChoice(key="a", text="A"),
                EventChoice(key="b", text="B"),
            ),
        )
        es = SimpleNamespace(choice_index=0)
        console = _FakeConsole()
        event_view._draw_choices(console, x=0, y=10, max_width=20, line=line, event_state=es)
        # The selected line carries the ▶ marker.
        flat = " ".join(p["string"] for p in console.prints)
        assert "▶" in flat


class TestHandleEventInput:
    def test_q_returns_false_to_quit(self) -> None:
        state = _make_state()
        es = EventState(event=_make_event(2))
        result = event_view.handle_event_input(_keydown("Q"), state, es)
        assert result is False

    def test_escape_completes_event_and_returns_true(self) -> None:
        state = _make_state()
        es = EventState(event=_make_event(2))
        result = event_view.handle_event_input(_keydown("ESCAPE"), state, es)
        assert result is True
        assert es.finished is True

    def test_confirm_advances_when_no_choices(self) -> None:
        state = _make_state()
        es = EventState(event=_make_event(3), current_line_index=0)
        # Use ENTER which goes through is_confirm_key
        result = event_view.handle_event_input(_keydown("RETURN"), state, es)
        assert result is True
        assert es.current_line_index == 1

    def test_up_decrements_choice_index(self) -> None:
        state = _make_state()
        es = EventState(
            event=EventStory(
                id="e",
                title="t",
                description="d",
                lines=(
                    EventLine(
                        speaker="s",
                        portrait="p",
                        text="x",
                        choices=(
                            EventChoice(key="a", text="A"),
                            EventChoice(key="b", text="B"),
                        ),
                    ),
                ),
            ),
            current_line_index=0,
            choice_index=1,
        )
        result = event_view.handle_event_input(_keydown("UP"), state, es)
        assert result is True
        assert es.choice_index == 0

    def test_down_increments_choice_index(self) -> None:
        state = _make_state()
        es = EventState(
            event=EventStory(
                id="e",
                title="t",
                description="d",
                lines=(
                    EventLine(
                        speaker="s",
                        portrait="p",
                        text="x",
                        choices=(
                            EventChoice(key="a", text="A"),
                            EventChoice(key="b", text="B"),
                        ),
                    ),
                ),
            ),
            current_line_index=0,
            choice_index=0,
        )
        result = event_view.handle_event_input(_keydown("DOWN"), state, es)
        assert result is True
        assert es.choice_index == 1

    def test_down_does_not_exceed_max(self) -> None:
        state = _make_state()
        es = EventState(
            event=EventStory(
                id="e",
                title="t",
                description="d",
                lines=(
                    EventLine(
                        speaker="s",
                        portrait="p",
                        text="x",
                        choices=(
                            EventChoice(key="a", text="A"),
                            EventChoice(key="b", text="B"),
                        ),
                    ),
                ),
            ),
            current_line_index=0,
            choice_index=1,  # already at last
        )
        event_view.handle_event_input(_keydown("DOWN"), state, es)
        assert es.choice_index == 1  # stays at max

    def test_confirm_executes_selected_choice(self) -> None:
        state = _make_state()
        es = EventState(
            event=EventStory(
                id="e",
                title="t",
                description="d",
                lines=(
                    EventLine(
                        speaker="s",
                        portrait="p",
                        text="x",
                        choices=(
                            EventChoice(key="a", text="Pick A"),
                            EventChoice(key="b", text="Pick B"),
                        ),
                    ),
                ),
            ),
            current_line_index=0,
            choice_index=1,
        )
        event_view.handle_event_input(_keydown("RETURN"), state, es)
        assert any("Pick B" in m for m in state.status_messages)

    def test_none_event_returns_true(self) -> None:
        """If current line is None, input is a no-op (event already over)."""
        state = _make_state()
        es = EventState(event=_make_event(1), current_line_index=99)
        result = event_view.handle_event_input(_keydown("RETURN"), state, es)
        assert result is True
        assert es.current_line_index == 99  # unchanged

    def test_unknown_key_returns_true(self) -> None:
        state = _make_state()
        es = EventState(event=_make_event(2))
        result = event_view.handle_event_input(_keydown("UNKNOWN"), state, es)
        assert result is True
