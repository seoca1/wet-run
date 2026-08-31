"""Dungeon-style matrix view: 2D grid rendering with rooms.

Renders the matrix as a top-down dungeon with rooms connected by corridors.
Uses cardinal direction movement (N/S/E/W).
"""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ..combat.palette import (
    CYAN_PURE,
    DAMAGE_FLASH_COLOR,
    DEFAULT_COLOR,
    GLITCH_COLOR,
    GRAY_MID_DARK,
    GRAY_MID_LIGHT,
    GREEN_PURE,
    ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
    TIER_GOLD,
)
from ..combat.registry import IceRegistry, ProgramRegistry
from ..i18n import Translator
from ..matrix import AlarmLevel, IceKind, MatrixGraph, Node, NodeKind, ZoneDepth
from ..matrix.dungeon_generator import RoomType
from . import action_menu, combat_view
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
from .npc_event import DIXIE_FLATLINE_EVENT, NPCState
from .state import AppState, ScreenKind
from .status_panel import render_status_panel

# Room glyphs
_ROOM_GLYPHS = {
    RoomType.ENTRY: "[]",
    RoomType.EXIT: ">>",
    RoomType.DATA: "D",
    RoomType.ICE: "!",
    RoomType.NPC: "?",
    RoomType.ROUTER: ".",
    RoomType.CORE: "C",
    RoomType.EMPTY: " ",
    RoomType.DEAD_END: "X",
}

_ROOM_NAMES = {
    RoomType.ENTRY: "Entry",
    RoomType.EXIT: "Exit",
    RoomType.DATA: "Data",
    RoomType.ICE: "ICE",
    RoomType.NPC: "NPC",
    RoomType.ROUTER: "Router",
    RoomType.CORE: "Core",
    RoomType.EMPTY: "Empty",
    RoomType.DEAD_END: "Dead End",
}

# Alarm-level → HP damage when entering a node.
_TRAP_DAMAGE: dict[str, int] = {
    AlarmLevel.LOW: 0,
    AlarmLevel.MEDIUM: 5,
    AlarmLevel.HIGH: 15,
    AlarmLevel.CRITICAL: 30,
}


def _maybe_trigger_trap(state: AppState, node: Node) -> None:
    """Apply trap damage if the node has elevated alarm."""
    damage = _TRAP_DAMAGE.get(node.alarm.value, 0)
    if damage > 0 and state.player_hp > 0:
        new_hp = max(1, state.player_hp - damage)
        state.player_hp = new_hp
        state.status_messages.append(f">>> TRAP: {node.alarm.value} alarm! -{damage} HP")


# Zone → random encounter probability per move.
_RANDOM_COMBAT_CHANCE: dict[str, float] = {
    ZoneDepth.SURFACE: 0.02,
    ZoneDepth.MID: 0.05,
    ZoneDepth.DEEP: 0.08,
    ZoneDepth.CORE: 0.12,
    ZoneDepth.TA: 0.20,
}

# Zone → preferred ICE kind for random encounters.
_RANDOM_ICE_BY_ZONE: dict[str, IceKind] = {
    ZoneDepth.SURFACE: IceKind.STANDARD,
    ZoneDepth.MID: IceKind.WATCHDOG,
    ZoneDepth.DEEP: IceKind.STANDARD,
    ZoneDepth.CORE: IceKind.BLACK,
    ZoneDepth.TA: IceKind.BLACK,
}


def _maybe_trigger_random_combat(
    state: AppState,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> bool:
    """Roll for a random combat encounter after movement.

    Returns True if combat was triggered (caller should skip action menu).
    """
    if state.player_hp <= 0:
        return False
    node = (
        state.matrix.get(state.current_node_id)
        if (state.matrix and state.current_node_id is not None)
        else None
    )
    if node is None:
        return False
    if node.kind is NodeKind.ICE or node.kind is NodeKind.ENTRY or node.kind is NodeKind.EXIT:
        return False
    chance = _RANDOM_COMBAT_CHANCE.get(node.zone.value, 0.02)
    import random as _random

    if _random.random() > chance:
        return False
    ice_kind = _RANDOM_ICE_BY_ZONE.get(node.zone.value, IceKind.STANDARD)
    ice_node = Node(
        id=f"random_{node.zone.value}",
        kind=NodeKind.ICE,
        label=f"Patrol ICE ({node.zone.value})",
        zone=node.zone,
        ice=ice_kind,
        alarm=AlarmLevel.LOW,
        faction=node.faction,
    )
    state.status_messages.append(f">>> Random patrol encounter: {ice_node.label}")
    cs = combat_view.start_combat(state, ice_node, prog_registry, ice_registry)
    state.combat_state = cs
    state.screen = ScreenKind.COMBAT
    state.message = ""
    return True


def render_dungeon_matrix(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    prog_registry: ProgramRegistry | None = None,
    ice_registry: IceRegistry | None = None,
) -> None:
    """Render the matrix screen as a 2D dungeon grid."""
    matrix = state.matrix
    if matrix is None or state.current_node_id is None:
        return

    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]
    panel_r = shell[RegionId.STATUS_PANEL]

    # Clear and draw dividers
    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console, shell)

    # Persistent status panel
    render_status_panel(console, state, panel_r)

    # Title
    current_node = matrix.get(state.current_node_id)
    if current_node:
        title = f"DUNGEON — {current_node.label} [{current_node.kind.value.upper()}]"
        subtitle = "Use ↑↓←→ to move through connected rooms"
    else:
        title = "DUNGEON"
        subtitle = "Navigating..."
    draw_title(console, title_r, title=title, subtitle=subtitle)

    # Main area: render dungeon
    _render_dungeon_grid(console, main_r, state, matrix)

    # Action menu overlay
    if state.action_menu_open and current_node:
        menu_w = 50
        menu_h = 12
        menu_x = main_r.x + (main_r.w - menu_w) // 2
        menu_y = main_r.y + (main_r.h - menu_h) // 2
        menu_region = Region(
            id=RegionId.MAIN,
            x=menu_x,
            y=menu_y,
            w=menu_w,
            h=menu_h,
        )
        action_menu.render_action_menu(console, t, state, current_node, menu_region)

    # Controls
    draw_controls(
        console,
        ctrl_r,
        lines=[
            "↑↓←→ Move  |  PgUp/← Backtrack  |  SPACE Action menu  |  ESC Leave",
            "Q Quit",
        ],
    )

    # Footer
    draw_footer(
        console,
        foot_r,
        text=f"Step {state.demo_step}  T+{state.demo_elapsed_s:.1f}s",
        status_messages=state.status_messages,
    )


def _render_dungeon_grid(
    console: tcod.console.Console,
    main: Region,
    state: AppState,
    matrix: MatrixGraph,
) -> None:
    """Render the 2D dungeon grid."""
    # Build room map: node_id -> (x, y) based on id format
    room_map: dict[str, tuple[int, int]] = {}

    # Try to extract grid positions from node IDs (if dungeon generator format)
    # Otherwise, fall back to auto-layout
    max_x = 0
    max_y = 0

    for node in matrix.nodes:
        # Check if this is a dungeon-generated node
        # For now, just use the layout based on connected components
        pos = _get_room_position(node.id, matrix)
        if pos is not None:
            room_map[node.id] = pos
            max_x = max(max_x, pos[0])
            max_y = max(max_y, pos[1])

    if not room_map:
        # Fallback: linear layout
        _render_linear_fallback(console, main, state, matrix)
        return

    # Calculate cell size
    cell_w = 10
    cell_h = 5
    grid_x = main.x + 2
    grid_y = main.y + 2

    # Scrollable camera: center viewport on current room, clamp to grid bounds
    current_pos = (
        _get_room_position(state.current_node_id, matrix) if state.current_node_id else None
    )
    if current_pos is not None:
        visible_rows = (main.h - 4) // cell_h  # rows visible in viewport
        grid_height = max_y + 1
        scroll_y = current_pos[1] - visible_rows // 2
        scroll_y = max(0, min(scroll_y, max(0, grid_height - visible_rows)))
    else:
        scroll_y = 0
    scroll_x = 0  # horizontal scroll not needed for narrow grid

    # Draw each room (skip if outside scroll viewport)
    for node in matrix.nodes:
        if node.id not in room_map:
            continue
        rx, ry = room_map[node.id]
        cell_x = grid_x + (rx - scroll_x) * cell_w
        cell_y = grid_y + (ry - scroll_y) * cell_h

        is_current = node.id == state.current_node_id

        # Determine room type (visual)
        if node.kind is NodeKind.ENTRY:
            room_type = RoomType.ENTRY
        elif node.kind is NodeKind.EXIT:
            room_type = RoomType.EXIT
        elif node.kind is NodeKind.DATA:
            room_type = RoomType.DATA
        elif node.kind is NodeKind.ICE:
            room_type = RoomType.ICE
        elif node.kind is NodeKind.CONSTRUCT:
            room_type = RoomType.NPC
        else:
            room_type = RoomType.ROUTER

        _draw_room_cell(
            console,
            main,
            cell_x,
            cell_y,
            cell_w,
            cell_h,
            node,
            room_type,
            is_current,
        )

    # Draw connections (corridors)
    for edge in matrix.edges:
        if edge.src in room_map and edge.dst in room_map:
            sx, sy = room_map[edge.src]
            dx, dy = room_map[edge.dst]
            _draw_corridor(
                console,
                main,
                grid_x + (sx - scroll_x) * cell_w,
                grid_y + (sy - scroll_y) * cell_h,
                grid_x + (dx - scroll_x) * cell_w,
                grid_y + (dy - scroll_y) * cell_h,
                cell_w,
                cell_h,
            )


def _draw_room_cell(
    console: tcod.console.Console,
    main: Region,
    x: int,
    y: int,
    w: int,
    h: int,
    node: Node,
    room_type: RoomType,
    is_current: bool,
) -> None:
    """Draw a single room cell."""
    # Border
    if is_current:
        fg_border = CYAN_PURE  # Cyan for current
    elif room_type is RoomType.ICE:
        fg_border = DAMAGE_FLASH_COLOR  # Red for ICE
    elif room_type is RoomType.DATA:
        fg_border = TIER_GOLD  # Gold for data
    elif room_type is RoomType.NPC:
        fg_border = GLITCH_COLOR  # Magenta for NPC
    elif room_type is RoomType.EXIT:
        fg_border = GREEN_PURE  # Green for exit
    else:
        fg_border = GRAY_MID_LIGHT  # Gray

    # Top/bottom borders
    for xi in range(x, x + w):
        if main.contains(xi, y):
            console.print(x=xi, y=y, string="-", fg=fg_border)
        if main.contains(xi, y + h - 1):
            console.print(x=xi, y=y + h - 1, string="-", fg=fg_border)

    # Left/right borders
    for yi in range(y, y + h):
        if main.contains(x, yi):
            console.print(x=x, y=yi, string="|", fg=fg_border)
        if main.contains(x + w - 1, yi):
            console.print(x=x + w - 1, y=yi, string="|", fg=fg_border)

    # Corners
    for cx, cy, char in [
        (x, y, "+"),
        (x + w - 1, y, "+"),
        (x, y + h - 1, "+"),
        (x + w - 1, y + h - 1, "+"),
    ]:
        if main.contains(cx, cy):
            console.print(x=cx, y=cy, string=char, fg=fg_border)

    # Content
    if main.contains(x + 1, y + 1):
        # Room glyph
        glyph_map = {
            RoomType.ENTRY: "▶",
            RoomType.EXIT: "■",
            RoomType.DATA: "$",
            RoomType.ICE: "!",
            RoomType.NPC: "?",
            RoomType.ROUTER: "·",
            RoomType.CORE: "◎",
            RoomType.EMPTY: " ",
        }
        glyph = glyph_map.get(room_type, "?")

        # Current marker
        marker = "▶" if is_current else " "
        console.print(
            x=x + 1,
            y=y + 1,
            string=f"{marker}{glyph}",
            fg=ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR if is_current else DEFAULT_COLOR,
        )

        # Label
        label = node.label[: w - 3]
        if main.contains(x + 1, y + 2):
            console.print(
                x=x + 1,
                y=y + 2,
                string=label,
                fg=ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR if is_current else DEFAULT_COLOR,
            )


def _draw_corridor(
    console: tcod.console.Console,
    main: Region,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    cell_w: int,
    cell_h: int,
) -> None:
    """Draw a corridor between two room centers."""
    # Calculate centers
    c1x = x1 + cell_w // 2
    c1y = y1 + cell_h // 2
    c2x = x2 + cell_w // 2
    c2y = y2 + cell_h // 2

    fg = GRAY_MID_DARK

    # Draw L-shaped path
    # Horizontal segment
    x_min = min(c1x, c2x)
    x_max = max(c1x, c2x)
    for xi in range(x_min, x_max + 1):
        if main.contains(xi, c1y):
            console.print(x=xi, y=c1y, string="─", fg=fg)

    # Vertical segment
    y_min = min(c1y, c2y)
    y_max = max(c1y, c2y)
    for yi in range(y_min, y_max + 1):
        if main.contains(c2x, yi):
            console.print(x=c2x, y=yi, string="│", fg=fg)

    # Corner
    if c1x != c2x and c1y != c2y:
        corner_char = "┘" if c1x < c2x and c1y < c2y else "└"
        if main.contains(c2x, c1y):
            console.print(x=c2x, y=c1y, string=corner_char, fg=fg)


def _render_linear_fallback(
    console: tcod.console.Console,
    main: Region,
    state: AppState,
    matrix: MatrixGraph,
) -> None:
    """Fallback rendering if no room positions are available."""
    console.print(
        x=main.x + 2,
        y=main.y + 2,
        string="(dungeon layout unavailable)",
        fg=GRAY_MID_LIGHT,
    )


def _get_room_position(node_id: str, matrix: MatrixGraph) -> tuple[int, int] | None:
    """Get the (x, y) grid position for a room.

    Uses the Node's own x,y if set (non-zero or DungeonGenerator layout),
    otherwise falls back to BFS from entry.
    """
    node = matrix.get(node_id)
    if node is not None:
        if node.x != 0 or node.y != 0:
            return (node.x, node.y)
        if node.x == 0 and node.y == 0 and node_id == matrix.entry_id:
            return (0, 0)
    # Fallback: BFS from entry
    entry = matrix.get(matrix.entry_id)
    if entry is None:
        return None
    visited: dict[str, tuple[int, int]] = {matrix.entry_id: (0, 0)}
    queue = [matrix.entry_id]
    while queue:
        current_id = queue.pop(0)
        cx, cy = visited[current_id]
        for neighbor in matrix.neighbors(current_id):
            if neighbor.id in visited:
                continue
            candidates = [
                (cx + 1, cy),
                (cx, cy - 1),
                (cx, cy + 1),
                (cx - 1, cy),
            ]
            placed = False
            for nx, ny in candidates:
                if not any(pos == (nx, ny) for pos in visited.values()):
                    visited[neighbor.id] = (nx, ny)
                    queue.append(neighbor.id)
                    placed = True
                    break
            if not placed:
                visited[neighbor.id] = (cx + 1, cy)
    return visited.get(node_id)


# ============================================================================
# Input handling
# ============================================================================


def handle_dungeon_input(
    event: tcod.event.Event,
    state: AppState,
    prog_registry: ProgramRegistry | None = None,
    ice_registry: IceRegistry | None = None,
) -> bool:
    """Handle input on the dungeon matrix screen."""
    if not isinstance(event, KeyDown):
        return True

    if state.action_menu_open:
        if state.matrix is not None and state.current_node_id is not None:
            current_node = state.matrix.get(state.current_node_id)
            if current_node is not None and prog_registry is not None and ice_registry is not None:
                continue_running, close_menu = action_menu.handle_action_menu_input(
                    event, state, current_node, prog_registry, ice_registry
                )
                if close_menu:
                    state.action_menu_open = False
                return continue_running
        state.action_menu_open = False
        return True

    if event.sym is KeySym.Q:
        return False
    if event.sym is KeySym.ESCAPE:
        # Leave matrix
        state.screen = ScreenKind.HUB
        state.status_messages.append(">>> Jacked out of matrix")
        return True
    if is_confirm_key(event.sym):
        # Open action menu (ENTER or SPACE)
        if state.matrix and state.current_node_id:
            node = state.matrix.get(state.current_node_id)
            if node:
                # Check if NPC
                if node.kind is NodeKind.CONSTRUCT and node.id == "npc_dixie":
                    # Start NPC encounter
                    state.npc_state = NPCState(event=DIXIE_FLATLINE_EVENT)
                    state.screen = ScreenKind.NPC
                    state.status_messages.append(">>> Started NPC encounter: Dixie Flatline")
                    return True
                # Normal action menu
                state.status_messages.append(f">>> Action menu opened for {node.label}")
                state.action_menu_open = True
        return True

    # Dedicated backtrack key (PageUp) — go to previous room in path
    if event.sym is KeySym.PAGEUP:
        _handle_backtrack(state, prog_registry, ice_registry)
        return True

    # Cardinal direction movement
    if event.sym in (KeySym.UP, KeySym.DOWN, KeySym.LEFT, KeySym.RIGHT):
        _handle_cardinal_movement(state, event.sym, prog_registry, ice_registry)
        return True

    return True


def _handle_cardinal_movement(
    state: AppState,
    sym: KeySym,
    prog_registry: ProgramRegistry | None,
    ice_registry: IceRegistry | None,
) -> None:
    """Handle arrow-key / vi-style hjkl movement through matrix nodes.

    Advances the runner to the chosen cardinal neighbor and delegates
    entry-handling (traps, random combat, room entry) to the appropriate
    subtree. Looks up programs/ICE via registries for any triggered events."""
    matrix = state.matrix
    if matrix is None or state.current_node_id is None:
        return

    current_id = state.current_node_id
    neighbors = matrix.neighbors(current_id)
    state.movement_step_count += 1
    state.nodes_visited.add(current_id)

    direction_name = {
        KeySym.UP: "NORTH",
        KeySym.DOWN: "SOUTH",
        KeySym.LEFT: "WEST",
        KeySym.RIGHT: "EAST",
    }[sym]

    # Reverse / backtrack: previous room in path is always reachable
    if state.exploration is not None and state.exploration.path:
        if len(state.exploration.path) >= 2:
            prev_id = state.exploration.path[-2]
            prev_node = matrix.get(prev_id)
            if prev_node is not None:
                prev_pos = _get_room_position(prev_id, matrix)
                curr_pos = _get_room_position(current_id, matrix)
                if prev_pos is not None and curr_pos is not None:
                    dx = prev_pos[0] - curr_pos[0]
                    dy = prev_pos[1] - curr_pos[1]
                    reverse_dir: dict[KeySym, tuple[int, int]] = {
                        KeySym.UP: (0, -1),
                        KeySym.DOWN: (0, 1),
                        KeySym.LEFT: (-1, 0),
                        KeySym.RIGHT: (1, 0),
                    }
                    if reverse_dir.get(sym) == (dx, dy):
                        if state.exploration.path and state.exploration.path[-1] == current_id:
                            state.exploration.path.pop()
                        state.current_node_id = prev_id
                        state.exploration.visit(prev_id)
                        state.status_messages.append(
                            f">>> Backtrack {direction_name} to {prev_node.label} ({prev_node.kind.value})"
                        )
                        _maybe_trigger_trap(state, prev_node)
                        if ice_registry is not None and prog_registry is not None:
                            if _maybe_trigger_random_combat(state, prog_registry, ice_registry):
                                return
                        return

    if not neighbors:
        state.status_messages.append(f">>> No exits to the {direction_name}")
        return

    dir_vector: dict[KeySym, tuple[int, int]] = {
        KeySym.UP: (0, -1),
        KeySym.DOWN: (0, 1),
        KeySym.LEFT: (-1, 0),
        KeySym.RIGHT: (1, 0),
    }
    dx, dy = dir_vector[sym]
    current_pos = _get_room_position(current_id, matrix)

    best_node: Node | None = None
    best_dot = -1
    for neighbor in neighbors:
        n_pos = _get_room_position(neighbor.id, matrix)
        if n_pos is None or current_pos is None:
            continue
        ndx = n_pos[0] - current_pos[0]
        ndy = n_pos[1] - current_pos[1]
        dot = ndx * dx + ndy * dy
        if dot > 0 and dot > best_dot:
            best_dot = dot
            best_node = neighbor

    if best_node is not None:
        state.current_node_id = best_node.id
        if state.exploration is not None:
            state.exploration.visit(best_node.id)
        state.status_messages.append(
            f">>> Moved {direction_name} to {best_node.label} ({best_node.kind.value})"
        )
        _maybe_trigger_trap(state, best_node)
        if ice_registry is not None and prog_registry is not None:
            if _maybe_trigger_random_combat(state, prog_registry, ice_registry):
                return
    else:
        state.status_messages.append(f">>> No room to the {direction_name}")


def _handle_backtrack(
    state: AppState,
    prog_registry: ProgramRegistry | None,
    ice_registry: IceRegistry | None,
) -> None:
    """Pop one node off the exploration path and rewind current_node_id.

    Used when a runner chooses to retreat from deeper zones instead of pushing
    forward. Appends a status message if there is nothing to backtrack to."""
    if state.matrix is None or state.current_node_id is None:
        return
    if state.exploration is None or len(state.exploration.path) < 2:
        state.status_messages.append(">>> Nowhere to backtrack to")
        return
    prev_id = state.exploration.path[-2]
    prev_node = state.matrix.get(prev_id)
    if prev_node is None:
        return
    if state.exploration.path and state.exploration.path[-1] == state.current_node_id:
        state.exploration.path.pop()
    state.current_node_id = prev_id
    state.exploration.visit(prev_id)
    state.status_messages.append(f">>> Backtrack to {prev_node.label} ({prev_node.kind.value})")
    if hasattr(prev_node, "room_type") and prev_node.room_type is RoomType.DEAD_END:
        damage = 10
        # GA-009 fix: floor at 1 so repeated backtrack cannot leave the
        # player at 0 HP (which would block all subsequent actions until
        # the player dies via the death cycle). max(1, ...) keeps the
        # player alive with 1 HP so they can recover.
        state.player_hp = max(1, state.player_hp - damage)
        state.status_messages.append(f">>> Dead End! You stumble and take {damage} damage!")
    _maybe_trigger_trap(state, prev_node)
    if ice_registry is not None and prog_registry is not None:
        _maybe_trigger_random_combat(state, prog_registry, ice_registry)
