"""Hacking minigame: System Probe (Phase 6+).

A timing-based keypress minigame. A probe indicator oscillates across
a bar with DANGER/CAUTION/SAFE/CAUTION/DANGER zones. Player
presses ENTER when the indicator is in the SAFE zone for maximum reward.
"""

from __future__ import annotations

from dataclasses import dataclass

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ..audio import safe_play
from ..combat.palette import (
    DEFAULT_COLOR,
    GRAY_DARK,
    HIT_FLASH_COLOR,
    ICE_GLOW,
    ICE_RED_DARK,
    WARM_DARK,
)
from ..i18n import Translator
from .input_utils import is_confirm_key
from .layout import (
    Region,
    RegionId,
    clear_region,
    draw_controls,
    draw_dividers,
    draw_footer,
    draw_title,
    make_shell,
)
from .state import AppState, ScreenKind
from .status_panel import render_status_panel

# Zones across the probe bar (index 0–19, 20 positions)
_HACK_ZONES: list[tuple[str, tuple[int, int, int]]] = [
    ("DANGER", ICE_RED_DARK),
    ("DANGER", ICE_RED_DARK),
    ("DANGER", ICE_RED_DARK),
    ("CAUTION", WARM_DARK),
    ("CAUTION", WARM_DARK),
    ("CAUTION", WARM_DARK),
    ("SAFE", ICE_GLOW),
    ("SAFE", ICE_GLOW),
    ("SAFE", ICE_GLOW),
    ("SAFE", ICE_GLOW),
    ("SAFE", ICE_GLOW),
    ("CAUTION", WARM_DARK),
    ("CAUTION", WARM_DARK),
    ("CAUTION", WARM_DARK),
    ("DANGER", ICE_RED_DARK),
    ("DANGER", ICE_RED_DARK),
    ("DANGER", ICE_RED_DARK),
    ("DANGER", ICE_RED_DARK),
    ("DANGER", ICE_RED_DARK),
    ("DANGER", ICE_RED_DARK),
]
assert len(_HACK_ZONES) == 20

_HACK_BAR_LEN = 20

# Oscillation speed (positions per second at base grade 1)
_HACK_BASE_SPEED = 6.0

_RESULT_LABELS: dict[str, str] = {
    "perfect": "PERFECT — 3x Data Fragments",
    "good": "GOOD — 2x Data Fragments",
    "partial": "PARTIAL — 1x Data Fragment",
    "fail": "FAIL — No reward",
}
_RESULT_COLORS: dict[str, tuple[int, int, int]] = {
    "perfect": ICE_GLOW,
    "good": (60, 180, 220),
    "partial": WARM_DARK,
    "fail": ICE_RED_DARK,
}
_RESULT_MESSAGES: dict[str, list[str]] = {
    "perfect": [
        ">> Probe locked. Data extraction protocol engaged.",
        ">> Encrypted cache located. 3x Data Fragments acquired.",
    ],
    "good": [
        ">> Partial breach. Some data recovered.",
        ">> 2x Data Fragments acquired.",
    ],
    "partial": [
        ">> System counter-measures slowed the probe.",
        ">> 1x Data Fragment acquired.",
    ],
    "fail": [
        ">> Access denied. System ejected the probe.",
        ">> Trace risk elevated. No data recovered.",
    ],
}


@dataclass
class HackingState:
    """Live state for the system probe minigame."""

    indicator_pos: float
    indicator_dir: int
    outcome: str | None = None
    locked_pos: int = 0


def render_hack(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
) -> None:
    """Render the hacking minigame screen."""
    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]
    panel_r = shell[RegionId.STATUS_PANEL]

    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console, shell)

    hack_state = getattr(state, "hack_state", None)
    node_label = getattr(state, "hack_node_label", "Unknown System")

    draw_title(
        console,
        title_r,
        title=f"SYSTEM PROBE — {node_label}",
        subtitle="Hit ENTER in the SAFE zone for maximum yield",
    )

    render_status_panel(console, state, panel_r)

    _draw_probe_bar(console, main_r, hack_state)
    _draw_result_text(console, main_r, hack_state)

    draw_controls(
        console,
        ctrl_r,
        lines=["ENTER  Execute Probe    ESC  Abort"],
    )

    draw_footer(
        console,
        foot_r,
        text=f"Step {state.demo_step}  T+{state.demo_elapsed_s:.1f}s",
        status_messages=state.status_messages,
    )


def _draw_probe_bar(
    console: tcod.console.Console,
    main: Region,
    hack_state: HackingState | None,
) -> None:
    """Draw the oscillating probe bar."""
    if hack_state is None:
        return

    bar_x = main.x + 4
    bar_y = main.y + 3

    indicator_pos = int(hack_state.indicator_pos)
    outcome = hack_state.outcome

    console.print(x=bar_x, y=bar_y, string="[PROBE]", fg=(180, 180, 180))

    bar_start_x = bar_x + 8
    for i in range(_HACK_BAR_LEN):
        zone_label, zone_color = _HACK_ZONES[i]
        if outcome is not None:
            if i == hack_state.locked_pos:
                ch = "●"
                fg = zone_color
            elif i == indicator_pos:
                ch = "▼"
                fg = HIT_FLASH_COLOR
            else:
                ch = "─"
                fg = GRAY_DARK
        else:
            if i == indicator_pos:
                ch = "▼"
                fg = HIT_FLASH_COLOR
            else:
                ch = "─"
                fg = zone_color
        console.print(x=bar_start_x + i, y=bar_y, string=ch, fg=fg)

    zone_label, zone_color = _HACK_ZONES[indicator_pos]
    console.print(x=bar_x, y=bar_y + 1, string=f"Zone: {zone_label}", fg=zone_color)

    if outcome is not None:
        result_label = _RESULT_LABELS.get(outcome, outcome)
        result_color = _RESULT_COLORS.get(outcome, DEFAULT_COLOR)
        console.print(x=bar_x, y=bar_y + 2, string=f"Result: {result_label}", fg=result_color)


def _draw_result_text(
    console: tcod.console.Console,
    main: Region,
    hack_state: HackingState | None,
) -> None:
    """Draw the outcome message after probe execution."""
    if hack_state is None or hack_state.outcome is None:
        return

    bar_x = main.x + 4
    bar_y = main.y + 5
    lines = _RESULT_MESSAGES.get(hack_state.outcome, [])
    color = _RESULT_COLORS.get(hack_state.outcome, DEFAULT_COLOR)
    for i, line in enumerate(lines):
        console.print(x=bar_x, y=bar_y + i, string=line, fg=color)


def handle_hack_input(
    event: tcod.event.Event,
    state: AppState,
) -> bool:
    """Handle input on the hacking minigame screen.

    Returns True if handled (no further dispatch needed).
    """
    if not isinstance(event, KeyDown):
        return True

    hack_state = getattr(state, "hack_state", None)
    if hack_state is None:
        return True

    if event.sym is KeySym.ESCAPE:
        safe_play("ui/menu_cancel")
        state.status_messages.append(">>> HACK: Probe aborted.")
        _apply_hack_reward(state, "fail")
        state.screen = ScreenKind.MATRIX
        _clear_hack_state(state)
        return True

    if is_confirm_key(event.sym):
        if hack_state.outcome is None:
            safe_play("combat/skill_physical")
            _execute_probe(hack_state)
            _apply_hack_reward(state, hack_state.outcome)
        else:
            state.screen = ScreenKind.MATRIX
            _clear_hack_state(state)
        return True

    return True


def _execute_probe(hack_state: HackingState) -> None:
    """Evaluate the probe timing and set outcome."""
    pos = int(hack_state.indicator_pos)
    pos = max(0, min(_HACK_BAR_LEN - 1, pos))
    zone_label, _ = _HACK_ZONES[pos]

    if zone_label == "SAFE":
        hack_state.outcome = "perfect"
    elif zone_label == "CAUTION":
        hack_state.outcome = "good"
    elif hack_state.indicator_dir > 0:
        hack_state.outcome = "partial"
    else:
        hack_state.outcome = "fail"
    hack_state.locked_pos = pos


def _apply_hack_reward(state: AppState, outcome: str | None) -> None:
    """Apply rewards or penalties based on hack outcome."""
    if not hasattr(state, "inventory") or state.inventory is None:
        state.inventory = {}

    if outcome == "perfect":
        fragments = 3
    elif outcome == "good":
        fragments = 2
    elif outcome == "partial":
        fragments = 1
    else:
        fragments = 0

    if fragments > 0:
        state.inventory["data_fragment"] = state.inventory.get("data_fragment", 0) + fragments
        state.status_messages.append(f">>> Gained: {fragments}x Data Fragment (probe)")
    else:
        state.status_messages.append(">>> No Data Fragments acquired.")


def _clear_hack_state(state: AppState) -> None:
    """Remove the hack attributes from the state to return to Matrix.

    Uses :func:`hasattr` per attribute so the call is a no-op when the
    state never entered the hack screen (e.g. an event was cancelled
    before ``start_hack`` ran). Both attributes are removed together
    so the next :func:`start_hack` always sees a clean slate and
    ``getattr(state, "hack_state", None)`` returns ``None`` from the
    matrix dispatcher.
    """
    for attr in ("hack_state", "hack_node_label"):
        if hasattr(state, attr):
            delattr(state, attr)


def step_hack(state: AppState, dt_s: float) -> None:
    """Advance the probe indicator by dt_s seconds.

    Called each frame while the hacking minigame is active.
    Oscillation speed scales with the player's grade (higher = faster).
    """
    hack_state = getattr(state, "hack_state", None)
    if hack_state is None or hack_state.outcome is not None:
        return

    grade = getattr(state.player_loadout, "grade", 1)
    speed = _HACK_BASE_SPEED + (grade - 1) * 1.5

    hack_state.indicator_pos += hack_state.indicator_dir * speed * dt_s

    pos = hack_state.indicator_pos
    if pos >= _HACK_BAR_LEN - 1:
        hack_state.indicator_pos = float(_HACK_BAR_LEN - 1)
        hack_state.indicator_dir = -1
    elif pos <= 0:
        hack_state.indicator_pos = 0.0
        hack_state.indicator_dir = 1
    # GA-015 fix: defensive clamp (race-condition guard). The conditional
    # above handles the bounce, but a transient out-of-range value can
    # still slip through between frames when _HACK_ZONES[indicator_pos]
    # is read. clamp() ensures the indexer never sees an out-of-range
    # float — even when the float-arithmetic rounding pushes pos just
    # past _HACK_BAR_LEN - 1 or just below 0.
    hack_state.indicator_pos = max(0.0, min(float(_HACK_BAR_LEN - 1), pos))


def start_hack(state: AppState, node_label: str) -> None:
    """Enter the hacking minigame for a SYSTEM node."""
    state.hack_state = HackingState(
        indicator_pos=0.0,
        indicator_dir=1,
        outcome=None,
        locked_pos=0,
    )
    state.hack_node_label = node_label
    state.screen = ScreenKind.HACK
    state.status_messages.append(f">>> HACK: Initiating probe on {node_label}...")
