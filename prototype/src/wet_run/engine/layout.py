"""Screen layout shell (ADR-0020+).

A unified 80x50 layout that all screens share. Divides the screen
into named regions so the player always knows where to look.

Layout (80 cols × 50 rows):

  Row 0-1   TITLE + STATUS         (full width, 2 rows)
  Row 2     divider
  Row 3-37  MAIN AREA              (full width, 35 rows)
  Row 38    divider
  Row 39-43 SIDE PANEL             (full width, 5 rows)
  Row 44    divider
  Row 45-47 CONTROLS               (full width, 3 rows)
  Row 48    divider
  Row 49    FOOTER                 (full width, 1 row)

Each region has a clear purpose. The main area shows the active
content (map, combat, or story) depending on the current screen mode.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

import tcod.console

if TYPE_CHECKING:
    from .state import StatusMessageList

# Screen dimensions
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50


class RegionId(StrEnum):
    """Stable identifiers for screen regions."""

    TITLE = "title"
    STATUS = "status"
    MAIN = "main"
    SIDE = "side"
    CONTROLS = "controls"
    FOOTER = "footer"
    STATUS_PANEL = "status_panel"  # Persistent right-side panel


@dataclass(frozen=True, slots=True)
class Region:
    """A rectangular region of the screen."""

    id: RegionId
    x: int
    y: int
    w: int
    h: int

    @property
    def x2(self) -> int:
        """Right edge x-coordinate (inclusive)."""
        return self.x + self.w - 1

    @property
    def y2(self) -> int:
        """Bottom edge y-coordinate (inclusive)."""
        return self.y + self.h - 1

    def contains(self, x: int, y: int) -> bool:
        """Return True if the cell at (x, y) lies within this region.

        Boundaries are inclusive on both edges.

        Args:
            x: Column to test.
            y: Row to test.

        Returns:
            ``True`` when ``(x, y)`` is inside the rectangle.
        """
        return self.x <= x <= self.x2 and self.y <= y <= self.y2


def make_shell(width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> dict[RegionId, Region]:
    """Build the default shell layout for the given screen size.

    Returns a dict of RegionId -> Region.

    Layout (80 cols × 50 rows):
      - TITLE:     top, full width
      - MAIN:      left side (width - 30 cols)
      - STATUS_PANEL: right side, 28 cols (persistent)
      - SIDE:      bottom strip, full width
      - CONTROLS:  bottom, full width
      - FOOTER:    bottom line, full width
    """
    # Reserve 28 cols on the right for the persistent status panel
    status_panel_w = 28
    main_w = width - status_panel_w

    title = Region(RegionId.TITLE, x=0, y=0, w=width, h=2)
    main = Region(RegionId.MAIN, x=0, y=3, w=main_w, h=35)
    status_panel = Region(RegionId.STATUS_PANEL, x=main_w, y=3, w=status_panel_w, h=35)
    side = Region(RegionId.SIDE, x=0, y=39, w=width, h=5)
    controls = Region(RegionId.CONTROLS, x=0, y=45, w=width, h=3)
    footer = Region(RegionId.FOOTER, x=0, y=49, w=width, h=1)
    return {
        RegionId.TITLE: title,
        RegionId.MAIN: main,
        RegionId.STATUS_PANEL: status_panel,
        RegionId.SIDE: side,
        RegionId.CONTROLS: controls,
        RegionId.FOOTER: footer,
    }


def clear_region(console: tcod.console.Console, region: Region) -> None:
    """Clear a region by writing spaces."""
    for y in range(region.y, min(region.y2 + 1, console.height)):
        for x in range(region.x, min(region.x2 + 1, console.width)):
            console.print(x=x, y=y, string=" ", fg=(0, 0, 0))


def print_in_region(
    console: tcod.console.Console,
    region: Region,
    x: int,
    y: int,
    string: str,
    fg: tuple[int, int, int] = (200, 200, 200),
) -> None:
    """Print a string clipped to ``region``."""
    abs_x = region.x + x
    abs_y = region.y + y
    if not region.contains(abs_x, abs_y):
        return
    # Clip width
    max_w = region.x2 - abs_x + 1
    if max_w <= 0:
        return
    text = string[:max_w]
    console.print(x=abs_x, y=abs_y, string=text, fg=fg)


def draw_dividers(
    console: tcod.console.Console, shell: dict[RegionId, Region] | None = None
) -> None:
    """Draw horizontal dividers at the standard row positions.

    Also draws a vertical divider between MAIN and STATUS_PANEL if shell is provided.
    """
    fg = (96, 96, 96)
    for y in (2, 38, 44, 48):
        console.print(x=0, y=y, string="─" * SCREEN_WIDTH, fg=fg)

    # Vertical divider between MAIN and STATUS_PANEL
    if shell is not None and RegionId.STATUS_PANEL in shell:
        panel = shell[RegionId.STATUS_PANEL]
        divider_x = panel.x
        for y in range(panel.y, panel.y2 + 1):
            console.print(x=divider_x, y=y, string="│", fg=fg)


def draw_title(
    console: tcod.console.Console,
    region: Region,
    title: str,
    subtitle: str = "",
) -> None:
    """Render the title and optional subtitle in the TITLE region."""
    console.print(x=2, y=0, string=f"== {title} ==", fg=(255, 255, 255))
    if subtitle:
        console.print(x=2, y=1, string=subtitle, fg=(128, 128, 128))


def draw_controls(
    console: tcod.console.Console,
    region: Region,
    lines: list[str],
) -> None:
    """Render one or more lines of controls in the CONTROLS region."""
    for i, line in enumerate(lines):
        if i >= region.h:
            break
        console.print(
            x=2,
            y=region.y + i,
            string=line[: region.w - 4],
            fg=(128, 128, 128),
        )


def draw_side(
    console: tcod.console.Console,
    region: Region,
    label: str,
    lines: list[str],
) -> None:
    """Render a labeled side panel (SIDE region)."""
    console.print(
        x=2,
        y=region.y,
        string=f"[{label}]",
        fg=(180, 180, 180),
    )
    for i, line in enumerate(lines):
        if i + 1 >= region.h:
            break
        console.print(
            x=2,
            y=region.y + 1 + i,
            string=line[: region.w - 4],
            fg=(160, 160, 160),
        )


def draw_footer(
    console: tcod.console.Console,
    region: Region,
    text: str,
    status_messages: list[str] | StatusMessageList | None = None,
    *,
    use_styled: bool = True,
) -> None:
    """Render the FOOTER line with optional status messages.

    If ``use_styled`` is True (default), parse ``status_messages`` via
    :class:`StatusMessage.from_legacy` to extract icon + color, and render
    the most recent message with appropriate styling. Warning/Error messages
    get a background highlight.

    Otherwise fall back to plain gray text rendering.
    """
    if status_messages and len(status_messages) > 0:
        if use_styled:
            from .status_message import StatusMessage

            typed: list[StatusMessage] = []
            for s in status_messages:
                if isinstance(s, StatusMessage):
                    typed.append(s)
                else:
                    typed.append(StatusMessage.from_legacy(s))
            last_msg = typed[-1]
            max_msg_len = region.w - len(text) - 6
            prefix = last_msg.prefix
            if len(prefix) > max_msg_len:
                prefix = prefix[: max_msg_len - 1] + "…"
            console.print(x=2, y=region.y, string=text, fg=(180, 180, 180))
            div_x = 2 + len(text) + 1
            if div_x < region.w - 1:
                console.print(x=div_x, y=region.y, string="│", fg=(80, 80, 80))
            msg_x = div_x + 2
            if last_msg.bg is not None:
                for i in range(len(prefix)):
                    if msg_x + i >= region.w:
                        break
                    console.print(
                        x=msg_x + i,
                        y=region.y,
                        string=prefix[i],
                        fg=last_msg.fg,
                        bg=last_msg.bg,
                    )
            else:
                console.print(x=msg_x, y=region.y, string=prefix, fg=last_msg.fg)
        else:
            legacy_last = status_messages[-1]
            max_msg_len = region.w - len(text) - 6
            if len(legacy_last) > max_msg_len:
                legacy_last = legacy_last[: max_msg_len - 3] + "..."
            full_text = f"{text}  |  {legacy_last}"
            console.print(
                x=2,
                y=region.y,
                string=full_text[: region.w - 4],
                fg=(160, 160, 160),
            )
    else:
        console.print(x=2, y=region.y, string=text, fg=(180, 180, 180))


def draw_message_log(
    console: tcod.console.Console,
    region: Region,
    status_messages: list[str] | StatusMessageList | None,
    *,
    max_lines: int | None = None,
    show_empty: bool = False,
) -> None:
    """Render a multi-line message log in the given region.

    Most recent messages at the bottom (newest-last).
    Each message gets an icon and color via :class:`StatusMessage`.

    Args:
        console: tcod console.
        region: Region to render in.
        status_messages: Legacy `>>> text` strings or StatusMessage instances.
        max_lines: Cap on number of messages shown (default: region height).
        show_empty: If True, show "[no messages]" placeholder when empty.
    """
    from .status_message import StatusMessage

    # Clear the region first
    for y in range(region.y, region.y2 + 1):
        for x in range(region.x, region.w):
            console.print(x=x, y=y, string=" ")

    if not status_messages:
        if show_empty:
            msg = "[no messages]"
            x = region.x + (region.w - len(msg)) // 2
            console.print(x=x, y=region.y + region.h // 2, string=msg, fg=(96, 96, 96))
        return

    # Convert to typed messages
    typed: list[StatusMessage] = []
    for s in status_messages:
        if isinstance(s, StatusMessage):
            typed.append(s)
        else:
            typed.append(StatusMessage.from_legacy(s))

    # Cap to most recent
    n_lines = max_lines if max_lines is not None else region.h
    typed = typed[-n_lines:]

    # Render newest at bottom; pad with blanks at top if fewer than max_lines
    start_y = region.y2 - len(typed) + 1
    for i, sm in enumerate(typed):
        y = start_y + i
        if y < region.y:
            continue
        prefix = sm.prefix
        if len(prefix) > region.w - 2:
            prefix = prefix[: region.w - 3] + "…"
        if sm.bg is not None:
            for j, ch in enumerate(prefix):
                xx = region.x + 1 + j
                if xx >= region.x + region.w:
                    break
                console.print(x=xx, y=y, string=ch, fg=sm.fg, bg=sm.bg)
        else:
            console.print(x=region.x + 1, y=y, string=prefix, fg=sm.fg)
