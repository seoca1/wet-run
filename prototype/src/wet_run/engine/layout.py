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

from ..combat.palette import (
    DEFAULT_COLOR,
    GRAY_96,
    GRAY_160,
    GRAY_BLACK,
    GRAY_MID_DARK,
    GRAY_MID_LIGHT,
    HIT_FLASH_COLOR,
)

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


def compute_status_panel_width(total_width: int) -> int:
    """Compute adaptive status panel width (ADR-0198).

    Tiers (ADR-0198 §Adaptive status_panel_w):
        - >=100 cols: 32 (Wide / Ultra-wide — more room)
        - >=80 cols:  28 (Classic — current)
        - >=60 cols:  22 (Compact / Tablet — narrower, abbreviate labels)
        - <60 cols:    18 (Phone — icon-only mode)

    Status panel content abbreviates per tier via separate rendering
    logic in screen handlers (not in this layout module).
    """
    if total_width >= 100:
        return 32
    if total_width >= 80:
        return 28
    if total_width >= 60:
        return 22
    return 18


def make_shell(width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> dict[RegionId, Region]:
    """Build the default shell layout for the given screen size (ADR-0198).

    Returns a dict of RegionId -> Region.

    Adaptive layout scales all region heights proportionally to the total
    height while keeping the 2/35/5/3/1 row allocation for 50-row defaults.
    Status panel width adapts to total width via compute_status_panel_width().

    Default layout (80 cols × 50 rows):
      - TITLE:     row 0-1 (h=2)
      - MAIN:      row 3-37 (h=35)
      - STATUS_PANEL: row 3-37, right side (h=35, w=compute_status_panel_width)
      - SIDE:      row 39-43 (h=5)
      - CONTROLS:  row 45-47 (h=3)
      - FOOTER:    row 49 (h=1)
    """
    status_panel_w = compute_status_panel_width(width)
    main_w = width - status_panel_w

    # Proportional height allocation for non-50-row presets.
    # Baseline (50 rows): title=2, main=35, side=5, controls=3, footer=1, dividers=4
    # Adjust main region height to fit smaller heights.
    if height >= 50:
        main_h = 35
        side_h = 5
        controls_h = 3
    elif height >= 40:
        main_h = 28
        side_h = 4
        controls_h = 2
    elif height >= 35:
        main_h = 24
        side_h = 3
        controls_h = 2
    else:
        main_h = max(20, height - 12)  # Reserve at least 12 rows for chrome
        side_h = 3
        controls_h = 2

    title = Region(RegionId.TITLE, x=0, y=0, w=width, h=2)
    main_y = 3
    main = Region(RegionId.MAIN, x=0, y=main_y, w=main_w, h=main_h)
    status_panel = Region(RegionId.STATUS_PANEL, x=main_w, y=main_y, w=status_panel_w, h=main_h)
    side_y = main_y + main_h + 1
    side = Region(RegionId.SIDE, x=0, y=side_y, w=width, h=side_h)
    controls_y = side_y + side_h + 1
    controls = Region(RegionId.CONTROLS, x=0, y=controls_y, w=width, h=controls_h)
    footer_y = min(controls_y + controls_h + 1, height - 1)
    footer_h = max(1, height - footer_y)
    footer = Region(RegionId.FOOTER, x=0, y=footer_y, w=width, h=footer_h)
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
            console.print(x=x, y=y, string=" ", fg=GRAY_BLACK)


def print_in_region(
    console: tcod.console.Console,
    region: Region,
    x: int,
    y: int,
    string: str,
    fg: tuple[int, int, int] = DEFAULT_COLOR,
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

    Adapter for ADR-0198: derives divider Y positions from the shell regions
    when provided, falling back to the classic 50-row defaults otherwise.
    """
    fg = GRAY_96
    if shell is not None:
        title = shell.get(RegionId.TITLE)
        side = shell.get(RegionId.SIDE)
        controls = shell.get(RegionId.CONTROLS)
        footer = shell.get(RegionId.FOOTER)
        divider_ys = set()
        if title is not None:
            divider_ys.add(title.y2 + 1)  # below title
        if side is not None:
            divider_ys.add(side.y - 1)  # above side
        if controls is not None:
            divider_ys.add(controls.y - 1)  # above controls
        if footer is not None:
            divider_ys.add(footer.y - 1)  # above footer
        width = title.w if title is not None else console.width
    else:
        divider_ys = {2, 38, 44, 48}
        width = SCREEN_WIDTH

    for y in divider_ys:
        if 0 <= y < console.height:
            console.print(x=0, y=y, string="─" * width, fg=fg)

    # Vertical divider between MAIN and STATUS_PANEL
    if shell is not None and RegionId.STATUS_PANEL in shell:
        panel = shell[RegionId.STATUS_PANEL]
        divider_x = panel.x
        for y in range(panel.y, min(panel.y2 + 1, console.height)):
            console.print(x=divider_x, y=y, string="│", fg=fg)


def draw_title(
    console: tcod.console.Console,
    region: Region,
    title: str,
    subtitle: str = "",
) -> None:
    """Render the title and optional subtitle in the TITLE region."""
    console.print(x=2, y=0, string=f"== {title} ==", fg=HIT_FLASH_COLOR)
    if subtitle:
        console.print(x=2, y=1, string=subtitle, fg=GRAY_MID_LIGHT)


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
            fg=GRAY_MID_LIGHT,
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
            fg=GRAY_160,
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
                console.print(x=div_x, y=region.y, string="│", fg=GRAY_MID_DARK)
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
                fg=GRAY_160,
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
            console.print(x=x, y=region.y + region.h // 2, string=msg, fg=GRAY_96)
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
