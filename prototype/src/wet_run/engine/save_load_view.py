"""Save/Load slot browser — select a slot to load or delete.

Reached from the Hub menu. Shows 5 save slots with metadata
(mission, stage, credits, timestamp). Player can:
- ENTER: load selected slot
- DELETE/D: delete selected slot
- ESC: cancel and return to Hub

References:
    save_manager.SaveManager
    save_manager.SaveMetadata
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import tcod.console
import tcod.event

from . import config as _engine_config
from .save_manager import MAX_SLOTS, SaveError, SaveManager, SaveSlotEmptyError
from .state import AppState, ScreenKind

if TYPE_CHECKING:
    from ..i18n import Translator

# --- Selection state (per AppState) ---


def get_selected_slot(state: AppState) -> int:
    """Get currently selected slot (1..MAX_SLOTS)."""
    return max(1, min(MAX_SLOTS, getattr(state, "save_load_selected", 1)))


def set_selected_slot(state: AppState, slot: int) -> None:
    """Set the currently selected slot."""
    state.save_load_selected = max(1, min(MAX_SLOTS, slot))


# --- Screen transitions ---


def enter_save_load(state: AppState) -> None:
    """Transition into the Save/Load browser."""
    state.screen = ScreenKind.SAVE_LOAD
    state.save_load_selected = 1
    state.status_messages.append(">>> Save/Load — select a slot")
    state.status_messages.append(">>> [ENTER] Load  [DEL] Delete  [ESC] Cancel")


def load_selected_slot(state: AppState) -> None:
    """Load the currently selected slot into AppState.

    Returns to Hub on success. On error, stays on the screen with a message.
    """
    slot = get_selected_slot(state)
    manager = SaveManager()
    try:
        manager.restore_state(slot, state)
        state.screen = ScreenKind.HUB
        state.status_messages.append(f">>> Loaded slot {slot}")
    except SaveSlotEmptyError:
        state.status_messages.append(f">>> Slot {slot} is empty — cannot load")
    except SaveError as e:
        state.status_messages.append(f">>> Load failed: {e}")


def delete_selected_slot(state: AppState) -> None:
    """Delete the currently selected slot."""
    slot = get_selected_slot(state)
    manager = SaveManager()
    if manager.delete(slot):
        state.status_messages.append(f">>> Slot {slot} deleted")
    else:
        state.status_messages.append(f">>> Slot {slot} was already empty")


def cancel_save_load(state: AppState) -> None:
    """Return to Hub without changes."""
    state.screen = ScreenKind.HUB
    state.status_messages.append(">>> Save/Load cancelled")


# --- Rendering ---


def _format_saved_at(iso: str | None) -> str:
    """Format ISO timestamp for display (truncated for compactness)."""
    if not iso:
        return "—"
    # Strip microseconds, keep just YYYY-MM-DD HH:MM
    if "T" in iso:
        date_part, time_part = iso.split("T", 1)
        # Remove timezone suffix and microseconds
        time_part = time_part.split("+", 1)[0].split("Z", 1)[0]
        if "." in time_part:
            time_part = time_part.split(".", 1)[0]
        return f"{date_part} {time_part}"
    return iso[:16]


def _format_elapsed(seconds: int) -> str:
    """Format elapsed seconds as MM:SS or HH:MM:SS."""
    if seconds < 0:
        return "—"
    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m {s:02d}s"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m"


def render_save_load(console: tcod.console.Console, state: AppState, t: Translator) -> None:
    """Render the Save/Load browser."""
    SCREEN_WIDTH = _engine_config.SCREEN_WIDTH  # noqa: N806
    SCREEN_HEIGHT = _engine_config.SCREEN_HEIGHT  # noqa: N806

    console.clear(bg=(0, 0, 0))
    _draw_save_load_header(console, SCREEN_WIDTH)
    manager = SaveManager()
    slots = manager.list_slots()
    selected = get_selected_slot(state)
    _draw_save_load_slots(console, SCREEN_WIDTH, slots, selected, state)
    _draw_save_load_controls(console, SCREEN_WIDTH, SCREEN_HEIGHT)
    _draw_save_load_status(console, SCREEN_HEIGHT, state, t)


# ------------------------------------------------------------------
# render_save_load helpers
# ------------------------------------------------------------------


def _draw_save_load_header(console: Any, screen_width: int) -> None:
    """Title and subtitle rows at the top of the save/load browser."""
    title = "═══ SAVE / LOAD ═══"
    console.print(
        x=(screen_width - len(title)) // 2,
        y=2,
        string=title,
        fg=(100, 200, 255),
    )
    subtitle = "Select a slot to load or delete"
    console.print(
        x=(screen_width - len(subtitle)) // 2,
        y=3,
        string=subtitle,
        fg=(150, 150, 150),
    )


def _draw_save_load_slots(
    console: Any, screen_width: int, slots: Any, selected: int, state: Any
) -> None:
    """Render the per-slot rows.  Each slot is a 6-row tall box with
    a one-line status header plus the metadata summary."""
    start_y = 6
    slot_h = 6
    slot_w = 60
    slot_x = (screen_width - slot_w) // 2

    for i, meta in enumerate(slots):
        slot_y = start_y + i * slot_h
        is_selected = meta.slot == selected

        if is_selected:
            border_color = (255, 200, 100)
            text_color = (255, 255, 200)
        else:
            border_color = (80, 80, 100)
            text_color = (180, 180, 180)

        # Slot frame
        _draw_save_load_slot_frame(console, slot_x, slot_y, slot_w, slot_h, border_color)
        _draw_save_load_slot_content(
            console, slot_x, slot_y, slot_w, meta, is_selected, state, text_color
        )


def _draw_save_load_slot_frame(
    console: Any, slot_x: int, slot_y: int, slot_w: int, slot_h: int, border_color: Any
) -> None:
    """The rounded box outline for a single slot row."""
    top = "┌" + "─" * (slot_w - 2) + "┐"
    bottom = "└" + "─" * (slot_w - 2) + "┘"
    console.print(x=slot_x, y=slot_y, string=top, fg=border_color)
    for y in range(slot_y + 1, slot_y + slot_h - 1):
        console.print(
            x=slot_x,
            y=y,
            string="│" + " " * (slot_w - 2) + "│",
            fg=border_color,
        )
    console.print(
        x=slot_x,
        y=slot_y + slot_h - 1,
        string=bottom,
        fg=border_color,
    )


def _draw_save_load_slot_content(
    console: Any,
    slot_x: int,
    slot_y: int,
    slot_w: int,
    meta: Any,
    is_selected: bool,
    state: Any,
    text_color: Any,
) -> None:
    """Either an existing save (4 detail lines) or an empty placeholder."""
    if not meta.exists:
        cursor = "▶" if is_selected else " "
        line = f"{cursor} Slot {meta.slot}  (empty)"
        console.print(
            x=slot_x + 2,
            y=slot_y + 2,
            string=line,
            fg=(80, 80, 90),
        )
        return

    cursor = "▶" if is_selected else " "
    compat = "✓" if meta.is_compatible else "⚠"
    mission_str = meta.mission_id or "?"
    stage_str = meta.current_stage or "?"
    elapsed_str = _format_elapsed(meta.elapsed_seconds)
    saved_str = _format_saved_at(meta.saved_at)
    size_kb = meta.size_bytes / 1024.0

    line1 = f"{cursor} Slot {meta.slot}  [{compat}]  {mission_str}"
    line2 = f"    Stage: {stage_str:<14}  Credits: {meta.credits}"
    line3 = f"    Grade: {meta.player_grade or '?':<14}  Time:  {elapsed_str}"
    line4 = f"    Saved: {saved_str}  ({size_kb:.1f} KB)"

    console.print(x=slot_x + 2, y=slot_y + 1, string=line1, fg=text_color)
    console.print(x=slot_x + 2, y=slot_y + 2, string=line2, fg=text_color)
    console.print(x=slot_x + 2, y=slot_y + 3, string=line3, fg=text_color)
    console.print(x=slot_x + 2, y=slot_y + 4, string=line4, fg=(120, 120, 130))


def _draw_save_load_controls(console: Any, screen_width: int, screen_height: int) -> None:
    """Two-line control hint at the bottom of the screen."""
    controls_y = screen_height - 5
    lines = [
        "[↑/↓] Select  [1-5] Jump to slot",
        "[ENTER] Load  [DEL] Delete  [ESC] Cancel",
    ]
    for i, line in enumerate(lines):
        console.print(
            x=(screen_width - len(line)) // 2,
            y=controls_y + i,
            string=line,
            fg=(150, 150, 150),
        )


def _draw_save_load_status(
    console: Any, screen_height: int, state: AppState, t: Translator
) -> None:
    """The last 3 status messages, dimmed, along the very bottom."""
    del t  # Reserved for future i18n
    if not state.status_messages:
        return
    for i, msg in enumerate(state.status_messages[-3:]):
        console.print(
            x=2,
            y=screen_height - 3 + i,
            string=msg,
            fg=(120, 120, 120),
        )


def handle_save_load_input(event: tcod.event.Event, state: AppState) -> bool:
    """Handle input on the Save/Load screen. Returns False to quit."""
    if not isinstance(event, tcod.event.KeyDown):
        return True

    if event.sym is tcod.event.KeySym.Q:
        return False

    if event.sym is tcod.event.KeySym.ESCAPE:
        cancel_save_load(state)
        return True

    # Navigation
    if event.sym is tcod.event.KeySym.UP:
        current = get_selected_slot(state)
        set_selected_slot(state, current - 1 if current > 1 else MAX_SLOTS)
        return True

    if event.sym is tcod.event.KeySym.DOWN:
        current = get_selected_slot(state)
        set_selected_slot(state, current + 1 if current < MAX_SLOTS else 1)
        return True

    # Jump to slot number
    if event.sym in (
        tcod.event.KeySym.N1,
        tcod.event.KeySym.N2,
        tcod.event.KeySym.N3,
        tcod.event.KeySym.N4,
        tcod.event.KeySym.N5,
    ):
        slot = int(event.sym.name[1:])
        set_selected_slot(state, slot)
        return True

    # Load
    if event.sym in (
        tcod.event.KeySym.RETURN,
        tcod.event.KeySym.SPACE,
        tcod.event.KeySym.KP_ENTER,
    ):
        load_selected_slot(state)
        return True

    # Delete
    if event.sym in (
        tcod.event.KeySym.DELETE,
        tcod.event.KeySym.D,
    ):
        delete_selected_slot(state)
        return True

    return True
