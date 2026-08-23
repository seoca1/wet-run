"""Achievement toast overlay render (T2.3).

Pops one notification from ``state.achievement_state.notification_queue``
per render call (when the previous toast expires), and draws a small
box near the top of the right-side STATUS_PANEL region. Toast lifetime
is ``TOAST_DURATION_MS`` (3 seconds); multi-unlock bursts are queued.

No-op when ``state.achievement_state`` is unset (test paths).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.console

if TYPE_CHECKING:
    from ..engine.layout import Region
    from ..engine.state import AppState
    from ..i18n import Translator

TOAST_DURATION_MS = 3000
TOAST_HEIGHT = 4
TOAST_BG = (20, 30, 50)
TOAST_BORDER = (255, 215, 0)
TOAST_TEXT = (240, 240, 240)


def draw_achievement_toast(
    console: tcod.console.Console,
    panel_r: Region,
    t: Translator,
    state: AppState,
) -> None:
    """Render the current achievement toast (top-right of STATUS_PANEL)."""
    import time

    ach_state = getattr(state, "achievement_state", None)
    if ach_state is None:
        return

    now_ms = int(time.time() * 1000)
    toast = state.toast_achievement
    if toast is None or (now_ms - state.toast_started_ms) >= TOAST_DURATION_MS:
        next_ach = ach_state.consume_notification()
        if next_ach is None:
            state.toast_achievement = None
            return
        state.toast_achievement = next_ach
        state.toast_started_ms = now_ms
        toast = next_ach

    lines = [
        t("achievement.toast_title"),
        f"{toast.icon}  {toast.name}",
    ]
    if toast.reward_credits > 0:
        lines.append(t("achievement.toast_reward", credits=toast.reward_credits))
    else:
        lines.append("")

    box_x = panel_r.x + 1
    box_y = panel_r.y + 1
    box_w = panel_r.w - 2
    box_h = min(TOAST_HEIGHT, panel_r.h - 2)
    if box_w < 4 or box_h < 2:
        return

    border = "+" + "-" * (box_w - 2) + "+"
    console.print(x=box_x, y=box_y, string=border, fg=TOAST_BORDER)
    for row in range(1, box_h - 1):
        console.print(
            x=box_x,
            y=box_y + row,
            string="|" + " " * (box_w - 2) + "|",
            fg=TOAST_BORDER,
            bg=TOAST_BG,
        )
    console.print(
        x=box_x,
        y=box_y + box_h - 1,
        string="+" + "-" * (box_w - 2) + "+",
        fg=TOAST_BORDER,
    )

    for i, line in enumerate(lines[: box_h - 2]):
        clipped = line[: box_w - 4]
        console.print(
            x=box_x + 2,
            y=box_y + 1 + i,
            string=clipped,
            fg=TOAST_TEXT,
            bg=TOAST_BG,
        )
