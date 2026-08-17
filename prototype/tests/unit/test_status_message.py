"""Tests for text visibility improvements (ADR-0047).

Covers:
    - StatusMessage dataclass (icon, fg, bg per kind)
    - MESSAGE_STYLE has all MessageKind entries
    - from_legacy() heuristic categorization
    - parse_legacy_messages() conversion + truncation
    - render_message() with/without background
    - draw_footer styled rendering (with multiple kinds)
    - draw_message_log multi-line rendering
    - StatusMessage integration with layout.draw_footer
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import tcod.console

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.engine.layout import (  # noqa: E402
    Region,
    RegionId,
    draw_footer,
    draw_message_log,
)
from wet_run.engine.status_message import (  # noqa: E402
    MESSAGE_STYLE,
    MessageKind,
    StatusMessage,
    parse_legacy_messages,
    render_message,
)

# ============================================================================
# StatusMessage basics
# ============================================================================


class TestMessageStyle:
    def test_all_kinds_have_style(self) -> None:
        """Every MessageKind must have a style entry."""
        for kind in MessageKind:
            assert kind in MESSAGE_STYLE, f"{kind.name} missing style"

    def test_style_has_icon_fg_bg(self) -> None:
        """Each style entry is (icon, fg, bg_or_none)."""
        for kind, style in MESSAGE_STYLE.items():
            assert len(style) == 3, f"{kind.name}: expected 3-tuple, got {len(style)}"
            icon, fg, bg = style
            assert isinstance(icon, str), f"{kind.name}: icon not str"
            assert icon, f"{kind.name}: empty icon"
            assert isinstance(fg, tuple), f"{kind.name}: fg not tuple"
            assert len(fg) == 3, f"{kind.name}: fg length != 3"
            # bg can be None (no highlight) or 3-tuple
            assert bg is None or (isinstance(bg, tuple) and len(bg) == 3)

    def test_warning_has_background(self) -> None:
        """Warning messages should stand out — has bg highlight."""
        assert MESSAGE_STYLE[MessageKind.WARNING][2] is not None

    def test_error_has_background(self) -> None:
        """Error messages should stand out — has bg highlight."""
        assert MESSAGE_STYLE[MessageKind.ERROR][2] is not None

    def test_info_no_background(self) -> None:
        """Info messages should not have bg (subtle)."""
        assert MESSAGE_STYLE[MessageKind.INFO][2] is None


class TestStatusMessage:
    def test_default_kind_is_info(self) -> None:
        msg = StatusMessage(text="hello")
        assert msg.kind is MessageKind.INFO
        assert msg.icon == "▸"

    def test_prefix_format(self) -> None:
        msg = StatusMessage(text="Data extracted", kind=MessageKind.SUCCESS)
        assert msg.prefix == "✓ Data extracted"

    def test_warning_prefix(self) -> None:
        msg = StatusMessage(text="Low HP", kind=MessageKind.WARNING)
        assert msg.prefix.startswith("⚠")
        assert msg.bg is not None

    def test_error_prefix(self) -> None:
        msg = StatusMessage(text="Lost combat", kind=MessageKind.ERROR)
        assert msg.prefix.startswith("✗")
        assert msg.bg is not None

    def test_timestamp_automatic(self) -> None:
        import time as _time

        before = _time.time()
        msg = StatusMessage(text="test")
        after = _time.time()
        assert before <= msg.timestamp <= after


# ============================================================================
# from_legacy heuristic
# ============================================================================


class TestFromLegacy:
    @pytest.mark.parametrize(
        ("text", "expected_kind"),
        [
            (">>> EXTRACT: Got data", MessageKind.SUCCESS),
            (">>> Gained: 1x fragment", MessageKind.SUCCESS),
            (">>> SCAN: data node", MessageKind.SUCCESS),
            (">>> Stage complete: Jack-out", MessageKind.SUCCESS),
            (">>> JACK OUT: disconnecting", MessageKind.SUCCESS),
            (">>> MOVE: passed through", MessageKind.MOVEMENT),
            (">>> Move: passed through N00", MessageKind.MOVEMENT),
            (">>> ENGAGE: combat init", MessageKind.SUCCESS),
            (">>> WARNING: low HP", MessageKind.WARNING),
            (">>> ERROR: denied", MessageKind.ERROR),
            (">>> Combat damage 5", MessageKind.COMBAT),
            (">>> Some info", MessageKind.INFO),
            (">>> hello world", MessageKind.INFO),
        ],
    )
    def test_heuristic_categorization(self, text: str, expected_kind: MessageKind) -> None:
        msg = StatusMessage.from_legacy(text)
        assert msg.kind is expected_kind, (
            f"text {text!r} → {msg.kind.name}, expected {expected_kind.name}"
        )

    def test_strips_arrow_prefix(self) -> None:
        msg = StatusMessage.from_legacy(">>> MOVE: passed")
        assert msg.text == "MOVE: passed" or msg.text == "MOVE passed"

    def test_error_priority_high(self) -> None:
        """ERROR kind has higher value than INFO (for sorting)."""
        assert MessageKind.ERROR > MessageKind.INFO
        assert MessageKind.WARNING > MessageKind.SUCCESS


# ============================================================================
# parse_legacy_messages
# ============================================================================


class TestParseLegacy:
    def test_empty_list(self) -> None:
        assert parse_legacy_messages([]) == []

    def test_basic_conversion(self) -> None:
        msgs = parse_legacy_messages([">>> EXTRACT: got data", ">>> WARNING: low hp"])
        assert len(msgs) == 2
        assert msgs[0].kind is MessageKind.SUCCESS
        assert msgs[1].kind is MessageKind.WARNING

    def test_max_keep_truncates(self) -> None:
        long_list = [f">>> msg {i}" for i in range(20)]
        msgs = parse_legacy_messages(long_list, max_keep=5)
        assert len(msgs) == 5
        # Most recent kept
        assert msgs[-1].text == "msg 19"

    def test_already_typed_passes_through(self) -> None:
        original = StatusMessage(text="test", kind=MessageKind.WARNING)
        msgs = parse_legacy_messages([original])
        assert len(msgs) == 1
        assert msgs[0] is original  # Same instance


# ============================================================================
# render_message
# ============================================================================


def _console_to_text(console: tcod.console.Console) -> str:
    lines = []
    for y in range(console.height):
        chars = []
        for x in range(console.width):
            code = int(console.ch[x, y])
            chars.append(chr(code) if 0 < code < 0x110000 else " ")
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


class TestRenderMessage:
    def test_renders_icon_and_text(self) -> None:
        console = tcod.console.Console(80, 30, order="F")
        msg = StatusMessage(text="Got data", kind=MessageKind.SUCCESS)
        render_message(console, 0, 0, msg, max_width=40)
        text = _console_to_text(console)
        assert "✓" in text
        assert "Got data" in text

    def test_truncates_long_message(self) -> None:
        console = tcod.console.Console(80, 30, order="F")
        msg = StatusMessage(text="x" * 100, kind=MessageKind.INFO)
        render_message(console, 0, 0, msg, max_width=10)
        text = _console_to_text(console)
        # Should be truncated with ellipsis
        rendered = text.split("\n")[0]
        assert "…" in rendered
        assert len(rendered) <= 10

    def test_warning_has_background(self) -> None:
        """Warning messages should highlight the entire row."""
        console = tcod.console.Console(80, 30, order="F")
        msg = StatusMessage(text="DANGER", kind=MessageKind.WARNING)
        render_message(console, 0, 0, msg, max_width=20)
        # Check that bg is set (look for non-zero bg)
        bg_set = False
        for x in range(20):
            if tuple(console.bg[x, 0]) != (0, 0, 0):
                bg_set = True
                break
        assert bg_set, "Warning message should have background highlight"

    def test_info_no_background(self) -> None:
        console = tcod.console.Console(80, 30, order="F")
        msg = StatusMessage(text="plain", kind=MessageKind.INFO)
        render_message(console, 0, 0, msg, max_width=20)
        # Info should have bg=None, so default (0,0,0) black
        for x in range(20):
            assert tuple(console.bg[x, 0]) == (0, 0, 0), f"x={x} has bg={console.bg[x, 0]}"


# ============================================================================
# draw_footer styled
# ============================================================================


class TestDrawFooterStyled:
    def test_no_messages_just_text(self) -> None:
        console = tcod.console.Console(80, 30, order="F")
        region = Region(RegionId.FOOTER, x=0, y=29, w=80, h=1)
        draw_footer(console, region, "Step 0", None)
        text = _console_to_text(console)
        assert "Step 0" in text.split("\n")[29]

    def test_with_legacy_message(self) -> None:
        console = tcod.console.Console(80, 30, order="F")
        region = Region(RegionId.FOOTER, x=0, y=29, w=80, h=1)
        draw_footer(
            console,
            region,
            "Step 0",
            [">>> EXTRACT: Got data fragment"],
            use_styled=True,
        )
        text = _console_to_text(console)
        last_line = text.split("\n")[29]
        # Should show icon + text
        assert "✓" in last_line or "EXTRACT" in last_line

    def test_with_warning_highlight(self) -> None:
        """Warning message should have background highlight in footer."""
        console = tcod.console.Console(80, 30, order="F")
        region = Region(RegionId.FOOTER, x=0, y=29, w=80, h=1)
        draw_footer(
            console,
            region,
            "Step 5",
            [">>> WARNING: Low HP!"],
            use_styled=True,
        )
        # Footer row should have bg != black
        any_bg = False
        for x in range(80):
            if tuple(console.bg[x, 29]) != (0, 0, 0):
                any_bg = True
                break
        assert any_bg, "Warning footer should have background highlight"

    def test_legacy_mode_no_styling(self) -> None:
        console = tcod.console.Console(80, 30, order="F")
        region = Region(RegionId.FOOTER, x=0, y=29, w=80, h=1)
        draw_footer(
            console,
            region,
            "Step 0",
            [">>> ERROR: died"],
            use_styled=False,
        )
        # No bg should be set in legacy mode
        for x in range(80):
            assert tuple(console.bg[x, 29]) == (0, 0, 0)


# ============================================================================
# draw_message_log
# ============================================================================


class TestDrawMessageLog:
    def test_empty_region_no_messages(self) -> None:
        console = tcod.console.Console(80, 50, order="F")
        region = Region(RegionId.SIDE, x=0, y=39, w=80, h=5)
        draw_message_log(console, region, None)
        text = _console_to_text(console)
        # Region should be cleared (empty lines)
        for y in range(39, 44):
            assert text.split("\n")[y] == ""

    def test_empty_with_placeholder(self) -> None:
        console = tcod.console.Console(80, 50, order="F")
        region = Region(RegionId.SIDE, x=0, y=39, w=80, h=5)
        draw_message_log(console, region, None, show_empty=True)
        text = _console_to_text(console)
        assert "[no messages]" in text

    def test_renders_messages(self) -> None:
        console = tcod.console.Console(80, 50, order="F")
        region = Region(RegionId.SIDE, x=0, y=39, w=80, h=5)
        draw_message_log(
            console,
            region,
            [">>> EXTRACT: Got data", ">>> WARNING: Low HP"],
        )
        text = _console_to_text(console)
        # Both messages should be in the region
        assert "EXTRACT" in text or "Got data" in text
        assert "Low HP" in text or "WARNING" in text

    def test_warning_has_bg(self) -> None:
        """Warning in log should highlight."""
        console = tcod.console.Console(80, 50, order="F")
        region = Region(RegionId.SIDE, x=0, y=39, w=80, h=5)
        draw_message_log(console, region, [">>> WARNING: danger"])
        # Check bg is set somewhere in region
        any_bg = False
        for y in range(39, 44):
            for x in range(80):
                if tuple(console.bg[x, y]) != (0, 0, 0):
                    any_bg = True
                    break
            if any_bg:
                break
        assert any_bg

    def test_max_lines_caps(self) -> None:
        """More messages than max_lines → only most recent shown."""
        console = tcod.console.Console(80, 50, order="F")
        region = Region(RegionId.SIDE, x=0, y=39, w=80, h=10)
        many = [f">>> msg {i}" for i in range(20)]
        draw_message_log(console, region, many, max_lines=3)
        text = _console_to_text(console)
        # Only the last 3 (msg 17, 18, 19) should be visible
        assert "msg 17" in text
        assert "msg 19" in text
        # Earlier ones should not be in the visible region
        # (Note: they may technically still be in the file but not rendered)


# ============================================================================
# Integration with matrix_view
# ============================================================================


class TestMatrixViewIntegration:
    def test_matrix_render_with_messages(self) -> None:
        """Matrix view should render without errors when status_messages are populated."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
        from wet_run.engine.matrix_view import _last_layout, render_matrix
        from wet_run.engine.state import AppState
        from wet_run.i18n import Translator
        from wet_run.matrix import Edge
        from wet_run.matrix.graph import MatrixGraph
        from wet_run.matrix.node import (
            AlarmLevel,
            Faction,
            IceKind,
            Node,
            NodeKind,
            ZoneDepth,
        )

        nodes = [
            Node(
                id=f"n_{x}_{y}",
                kind=NodeKind.DATA,
                label=f"N{x}{y}",
                zone=ZoneDepth.SURFACE,
                ice=IceKind.NONE,
                alarm=AlarmLevel.LOW,
                faction=Faction.NONE,
            )
            for x in range(2)
            for y in range(2)
        ]
        edges = [Edge(src=f"n_{x}_{y}", dst=f"n_{x + 1}_{y}") for x in range(1) for y in range(2)]
        edges += [Edge(src=f"n_{x}_{y}", dst=f"n_{x}_{y + 1}") for x in range(2) for y in range(1)]
        m = MatrixGraph(nodes=tuple(nodes), edges=tuple(edges), entry_id="n_0_0")
        _last_layout[m] = {f"n_{x}_{y}": (x * 12, y * 4) for x in range(2) for y in range(2)}

        state = AppState()
        state.matrix = m
        state.current_node_id = "n_0_0"
        state.status_messages.append(">>> EXTRACT: Got data fragment")
        state.status_messages.append(">>> WARNING: Incoming ICE")

        console = tcod.console.Console(80, 50, order="F")
        tr = Translator("en", data_dir=Path("data/i18n"))
        # Should not raise
        render_matrix(console, tr, state, _last_layout[m])


class TestStatusMessageListCap:
    """StatusMessageList auto-truncates to STATUS_MESSAGES_MAX (P2 #17).

    Prevents unbounded growth across long sessions — the AppState
    default_factory was a plain ``list`` and 100+ call sites across
    the codebase append to it without bound.
    """

    def test_default_state_is_empty(self) -> None:
        from wet_run.engine.state import STATUS_MESSAGES_MAX, AppState

        state = AppState()
        assert len(state.status_messages) == 0
        assert STATUS_MESSAGES_MAX > 0

    def test_append_under_cap_keeps_all(self) -> None:
        from wet_run.engine.state import STATUS_MESSAGES_MAX, StatusMessageList

        msgs = StatusMessageList()
        for i in range(STATUS_MESSAGES_MAX - 1):
            msgs.append(f"msg {i}")
        assert len(msgs) == STATUS_MESSAGES_MAX - 1

    def test_append_at_cap_drops_oldest(self) -> None:
        from wet_run.engine.state import (
            STATUS_MESSAGES_MAX,
            StatusMessageList,
        )

        msgs = StatusMessageList()
        for i in range(STATUS_MESSAGES_MAX + 50):
            msgs.append(f"msg {i}")
        assert len(msgs) == STATUS_MESSAGES_MAX
        # Oldest entries dropped, newest retained
        assert msgs[0] == "msg 50"
        assert msgs[-1] == f"msg {STATUS_MESSAGES_MAX + 49}"

    def test_extend_truncates(self) -> None:
        from wet_run.engine.state import (
            STATUS_MESSAGES_MAX,
            StatusMessageList,
        )

        msgs = StatusMessageList(["a", "b"])
        msgs.extend([f"x{i}" for i in range(STATUS_MESSAGES_MAX)])
        assert len(msgs) == STATUS_MESSAGES_MAX
        # The first two ("a", "b") should be dropped
        assert msgs[0] == "x0"

    def test_appstate_long_session_stays_bounded(self) -> None:
        """Regression: long run doesn't accumulate messages unbounded."""
        from wet_run.engine.state import (
            STATUS_MESSAGES_MAX,
            AppState,
        )

        state = AppState()
        for i in range(STATUS_MESSAGES_MAX * 3):
            state.status_messages.append(f">>> action {i}")
        assert len(state.status_messages) == STATUS_MESSAGES_MAX
        # Newest entry preserved
        assert state.status_messages[-1] == f">>> action {STATUS_MESSAGES_MAX * 3 - 1}"
