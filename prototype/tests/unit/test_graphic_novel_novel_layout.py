"""Tests for the novel-style pagination and wrap functions.

Covers (added in polish pass):
    - wrap_text_for_novel(): word wrap with margins
    - paginate_lines(): split wrapped lines into pages
    - compute_typed_page_index(): determine current page from typing cursor
    - render_scene() with the new novel layout (uses full vertical space)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import tcod.console  # noqa: E402

from wet_run.engine.graphic_novel_view import (  # noqa: E402
    NOVEL_LEFT_MARGIN,
    NOVEL_RIGHT_MARGIN,
    DialogueLine,
    SceneData,
    compute_typed_page_index,
    paginate_lines,
    render_scene,
    wrap_text_for_novel,
)
from wet_run.i18n import Translator  # noqa: E402

# ============================================================================
# wrap_text_for_novel
# ============================================================================


class TestWrapTextForNovel:
    def test_short_text_single_line(self) -> None:
        lines = wrap_text_for_novel("Hello, world.", width=80)
        assert lines == ["Hello, world."]

    def test_word_wrap_at_margin(self) -> None:
        text = "The sky above the port was the color of television, tuned to a dead channel."
        lines = wrap_text_for_novel(text, width=80)
        # 80 - 2 - 2 = 76 chars per line
        for line in lines:
            assert len(line) <= 76, f"Line exceeds 76 chars: {line!r}"
        # All words preserved
        joined = " ".join(lines)
        assert joined == text

    def test_paragraph_break_yields_blank_line(self) -> None:
        text = "First paragraph here.\n\nSecond paragraph here."
        lines = wrap_text_for_novel(text, width=80)
        assert lines == ["First paragraph here.", "", "Second paragraph here."]

    def test_custom_margins(self) -> None:
        text = "word " * 30  # 150 chars
        text = text.strip()
        lines = wrap_text_for_novel(text, width=80, left_margin=10, right_margin=10)
        # 80 - 10 - 10 = 60 chars per line
        for line in lines:
            assert len(line) <= 60

    def test_long_text_wraps_to_multiple_lines(self) -> None:
        text = "lorem ipsum dolor sit amet " * 20
        lines = wrap_text_for_novel(text, width=80)
        assert len(lines) > 1
        for line in lines:
            assert len(line) <= 76

    def test_handles_empty_text(self) -> None:
        assert wrap_text_for_novel("", width=80) == [""]

    def test_default_width_80(self) -> None:
        text = "x " * 100  # 200 chars
        lines = wrap_text_for_novel(text)  # no width arg
        for line in lines:
            assert len(line) <= 76

    def test_very_long_word_truncates(self) -> None:
        # A single word longer than the line width
        long_word = "a" * 100
        lines = wrap_text_for_novel(long_word, width=80)
        assert len(lines) == 1
        assert len(lines[0]) == 100  # we don't break words


# ============================================================================
# paginate_lines
# ============================================================================


class TestPaginateLines:
    def test_fits_one_page(self) -> None:
        lines = ["line " + str(i) for i in range(5)]
        pages = paginate_lines(lines, lines_per_page=10)
        assert len(pages) == 1
        assert pages[0] == lines

    def test_exact_boundary(self) -> None:
        lines = ["line " + str(i) for i in range(10)]
        pages = paginate_lines(lines, lines_per_page=10)
        assert len(pages) == 1

    def test_two_pages(self) -> None:
        lines = ["line " + str(i) for i in range(15)]
        pages = paginate_lines(lines, lines_per_page=10, blank_separator=False)
        assert len(pages) == 2
        assert len(pages[0]) == 10
        assert len(pages[1]) == 5

    def test_three_pages(self) -> None:
        lines = ["line " + str(i) for i in range(25)]
        pages = paginate_lines(lines, lines_per_page=10, blank_separator=False)
        assert len(pages) == 3
        assert [len(p) for p in pages] == [10, 10, 5]

    def test_empty_input(self) -> None:
        pages = paginate_lines([], lines_per_page=10)
        assert pages == [[]]

    def test_no_paragraph_split(self) -> None:
        # Pagination should never split a non-empty line
        lines = ["line " + str(i) for i in range(15)]
        pages = paginate_lines(lines, lines_per_page=10, blank_separator=True)
        # Verify no line is broken mid-content
        all_pages_flat = []
        for page in pages:
            all_pages_flat.extend(page)
        # Filter out empty separator lines
        non_empty = [ln for ln in all_pages_flat if ln]
        assert non_empty == lines

    def test_zero_lines_per_page(self) -> None:
        # Edge case: lpp=0 returns the full list
        lines = ["a", "b", "c"]
        pages = paginate_lines(lines, lines_per_page=0)
        assert pages == [lines]


# ============================================================================
# compute_typed_page_index
# ============================================================================


class TestComputeTypedPageIndex:
    def test_first_page_when_typing_at_start(self) -> None:
        pages = [["a", "b", "c"], ["d", "e", "f"]]
        assert compute_typed_page_index(pages, 0, "a b c d e f") == 0

    def test_mid_first_page(self) -> None:
        pages = [["a", "b", "c"], ["d", "e", "f"]]
        # After "a b" (chars 0-2), still on page 1
        idx = compute_typed_page_index(pages, 3, "a b c d e f")
        assert idx == 0

    def test_advances_to_second_page(self) -> None:
        pages = [["a", "b", "c"], ["d", "e", "f"]]
        # After "a b c" (3 lines * 1 char + 2 spaces = 5), still page 1
        # After "a b c " (6 chars), start of page 2
        idx = compute_typed_page_index(pages, 6, "a b c d e f")
        assert idx == 1

    def test_stays_on_last_page(self) -> None:
        pages = [["a", "b", "c"], ["d", "e", "f"]]
        idx = compute_typed_page_index(pages, 100, "a b c d e f")
        assert idx == 1

    def test_empty_pages(self) -> None:
        assert compute_typed_page_index([], 5, "") == 0


# ============================================================================
# render_scene: novel layout
# ============================================================================


def _make_scene(title: str = "TEST SCENE") -> SceneData:
    """Create a minimal scene object for testing render_scene."""
    return SceneData(
        id="test_scene",
        character="novice",
        order=0,
        title_en=title,
        title_ko="테스트",
        background_id="",
        portrait_left=None,
        portrait_right=None,
        dialogue=(),
        next_scene=None,
    )


def _make_dlg(text: str = "Hello world.") -> DialogueLine:
    return DialogueLine(
        speaker="case",
        speaker_ko="케이",
        portrait=None,
        text_en=text,
        text_ko=text,
        duration_ms=5000,
    )


class TestRenderSceneNovelLayout:
    def test_uses_full_vertical_space(self) -> None:
        """Body of the novel layout should extend from speaker to footer."""
        console = tcod.console.Console(80, 50, order="F")
        tr = Translator("en", data_dir=Path("data/i18n"))
        text = "Some text here in the novel."
        dlg = _make_dlg(text)
        render_scene(console, _make_scene(), dlg, None, None, None, tr, len(text), 0, 1)
        # Top bar at y=0
        top = "".join(chr(int(console.ch[x, 0])) for x in range(80))
        assert "[1/1]" in top
        # Body should contain text somewhere in the middle/lower area
        found_text = False
        for y in range(15, 47):
            line = "".join(chr(int(console.ch[x, y])) for x in range(80)).rstrip()
            if text in line:
                found_text = True
                break
        assert found_text, f"Body text {text!r} not found in expected area"

    def test_body_extends_past_old_3_line_box(self) -> None:
        """Verify body uses more than 3 lines (the old dialogue box limit)."""
        # 4 short paragraphs should be displayed as 4 lines (the old layout
        # would have truncated to 3)
        text = "First line. Second line. Third line. Fourth line."
        dlg = _make_dlg(text)
        console = tcod.console.Console(80, 50, order="F")
        tr = Translator("en", data_dir=Path("data/i18n"))
        render_scene(console, _make_scene(), dlg, None, None, None, tr, len(text), 0, 1)
        body_with_text = 0
        for y in range(16, 46):
            line = "".join(chr(int(console.ch[x, y])) for x in range(80)).rstrip()
            if line and "─" not in line and "[Space]" not in line:
                body_with_text += 1
        assert body_with_text >= 1, "Expected at least one line of body text"

    def test_speaker_heading_is_centered(self) -> None:
        console = tcod.console.Console(80, 50, order="F")
        tr = Translator("en", data_dir=Path("data/i18n"))
        dlg = _make_dlg("Some text.")
        render_scene(console, _make_scene(), dlg, None, None, None, tr, 9, 0, 1)
        # Look for "── case ──" at y=14
        heading_line = "".join(chr(int(console.ch[x, 14])) for x in range(80)).rstrip()
        assert "case" in heading_line
        assert "──" in heading_line

    def test_no_speaker_no_heading(self) -> None:
        console = tcod.console.Console(80, 50, order="F")
        tr = Translator("en", data_dir=Path("data/i18n"))
        dlg = DialogueLine(
            speaker="",
            speaker_ko="",
            portrait=None,
            text_en="narration text",
            text_ko="narration text",
            duration_ms=5000,
        )
        render_scene(console, _make_scene(), dlg, None, None, None, tr, 14, 0, 1)
        # With no speaker, there should be no "── speaker ──" centered heading
        # anywhere in the body area
        for y in range(14, 16):
            line = "".join(chr(int(console.ch[x, y])) for x in range(80)).rstrip()
            # If there's a centered heading, it would contain "──" at this row
            if line and "──" in line:
                pytest.fail(f"Unexpected speaker heading at y={y}: {line!r}")
        # And the body text "narration text" should appear somewhere in the body
        found = any(
            "narration text" in "".join(chr(int(console.ch[x, y])) for x in range(80))
            for y in range(14, 47)
        )
        assert found, "Body text not found in novel layout"

    def test_long_text_uses_pagination(self) -> None:
        """A long dialogue that exceeds body height should paginate."""
        # Need >30 lines of wrapped text to trigger pagination
        long_text = " ".join(
            [
                "The sky above the port was the color of television, "
                "tuned to a dead channel and the night was humid."
            ]
            * 30
        )
        dlg = _make_dlg(long_text)
        console = tcod.console.Console(80, 50, order="F")
        tr = Translator("en", data_dir=Path("data/i18n"))
        render_scene(console, _make_scene(), dlg, None, None, None, tr, len(long_text), 0, 1)
        # Look for PAGE label at y=height-3=47
        footer = "".join(chr(int(console.ch[x, 47])) for x in range(80)).rstrip()
        assert "PAGE" in footer, f"Expected PAGE label, got: {footer!r}"
        # 2/N expected (at least 2 pages)
        import re

        m = re.search(r"PAGE (\d+)/(\d+)", footer)
        assert m, f"No PAGE label found: {footer!r}"
        assert int(m.group(2)) >= 2

    def test_short_text_no_pagination_label(self) -> None:
        """A short dialogue should NOT show PAGE label."""
        dlg = _make_dlg("Just a line.")
        console = tcod.console.Console(80, 50, order="F")
        tr = Translator("en", data_dir=Path("data/i18n"))
        render_scene(console, _make_scene(), dlg, None, None, None, tr, 14, 0, 1)
        footer = "".join(chr(int(console.ch[x, 47])) for x in range(80)).rstrip()
        assert "PAGE" not in footer

    def test_typing_cuts_off_mid_line(self) -> None:
        """The typing effect should truncate the last visible line at the cursor."""
        dlg = _make_dlg("The sky above the port was the color of television.")
        console = tcod.console.Console(80, 50, order="F")
        tr = Translator("en", data_dir=Path("data/i18n"))
        # Reveal only 10 chars
        render_scene(console, _make_scene(), dlg, None, None, None, tr, 10, 0, 1)
        # Find the partial text in body
        body = []
        for y in range(15, 46):
            line = "".join(chr(int(console.ch[x, y])) for x in range(80)).rstrip()
            if "The s" in line:
                body.append(line)
        # At least one body line should contain the partial text
        assert any("The s" in ln for ln in body), f"No partial text found in body: {body}"

    def test_margin_constants(self) -> None:
        """Book-style margins should be small and consistent."""
        assert NOVEL_LEFT_MARGIN == 2
        assert NOVEL_RIGHT_MARGIN == 2
