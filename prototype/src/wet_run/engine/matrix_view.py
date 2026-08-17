"""Matrix screen: render the node graph and handle movement (ADR-0005).

Phase 5+ adds Fog of War / Exploration (ADR-0020):
  - current node: full info, highlighted
  - adjacent: kind only, outline box
  - discovered: full info (visited before)
  - unknown: `?` placeholder
  - minimap (side) + breadcrumb (side)

Phase 5+ adds Action Menu:
  - ENTER on a node: action menu popup
  - Actions depend on node kind (DATA/ICE/EXIT/ROUTER/etc.)

Uses the unified screen shell (engine.layout) for area separation:
  - Title: zone + status
  - Main: node graph with fog
  - Side: minimap + current info + path
  - Controls: input hints
  - Footer: step + time
"""

from __future__ import annotations

from typing import Any

import tcod.console

from ..combat.registry import IceRegistry, ProgramRegistry
from ..i18n import Translator
from ..matrix import (
    MatrixGraph,
    Node,
    NodeKind,
    Status,
    Visibility,
    node_zdr,
    status_color,
    zone_label,
)
from ..matrix.exploration import ExplorationState
from ..matrix.ppl import calculate_ppl
from ..matrix.zdr import node_status
from . import action_menu
from .layout import (
    Region,
    RegionId,
    clear_region,
    draw_controls,
    draw_dividers,
    draw_footer,
    draw_message_log,
    draw_side,
    draw_title,
    make_shell,
)
from .matrix_minimap import (
    _draw_breadcrumb,
    _draw_minimap,
    _draw_mobility_stats,
    _short_kind,
)
from .matrix_view_input import _adjacent_nodes_list, _last_layout  # noqa: F401
from .state import AppState
from .status_panel import render_status_panel

BOX_WIDTH = 12
BOX_HEIGHT = 4
BOX_INNER_W = BOX_WIDTH - 2

_KIND_LABEL: dict[NodeKind, str] = {
    NodeKind.ENTRY: "Entry",
    NodeKind.EXIT: "Exit",
    NodeKind.DATA: "Data",
    NodeKind.ICE: "ICE",
    NodeKind.SYSTEM: "System",
    NodeKind.ROUTER: "Router",
    NodeKind.CONSTRUCT: "Construct",
    NodeKind.CORE: "Core",
}

_STATUS_GLYPH: dict[Status, str] = {
    Status.SAFE: "+",
    Status.MATCH: "=",
    Status.TOUGH: "-",
    Status.DEADLY: "!",
    Status.FUTILE: "X",
}


def _status_glyph(status: Status) -> str:
    """Return a single-character glyph representing a :class:`Status`.

    Falls back to ``"?"`` when the status is unknown.

    Args:
        status: Combat/status flag.

    Returns:
        One-character string (e.g. "+", "!", "X").
    """
    return _STATUS_GLYPH.get(status, "?")


def _draw_box(
    console: tcod.console.Console,
    main: Region,
    col: int,
    row: int,
    label: str,
    zdr: int,
    status: Status,
    is_current: bool,
    direction_hints: dict[str, str] | None = None,
) -> None:
    """Draw one full-visibility node box.

    Args:
        console: tcod console.
        main: Main region.
        col: Column in main region.
        row: Row in main region.
        label: Node label.
        zdr: Zone Difficulty Rating.
        status: Status.
        is_current: Whether this is the player's current node.
        direction_hints: For current node — map of direction code to glyph shown
            on the box edge. Direction codes: "L", "R", "U", "D".
            E.g. {"L": "←", "U": "↑"} for neighbors on the left and up.
    """
    fg_box, border_chars, bg_label = _resolve_box_style(is_current)
    abs_x = main.x + col
    abs_y = main.y + row
    if not main.contains(abs_x, abs_y) or not main.contains(
        abs_x + BOX_WIDTH - 1, abs_y + BOX_HEIGHT - 1
    ):
        return

    _draw_box_frame(console, abs_x, abs_y, fg_box, border_chars)
    _draw_box_content(console, abs_x, abs_y, label, zdr, status, is_current, bg_label)
    if is_current:
        _draw_box_external_markers(console, main, abs_x, abs_y)
        if direction_hints:
            _draw_box_direction_hints(console, abs_x, abs_y, direction_hints, bg_label)


def _resolve_box_style(
    is_current: bool,
) -> tuple[tuple[int, int, int], dict[str, str], tuple[int, int, int]]:
    """Pick colors and border glyphs based on whether this is the
    current node.  Returns ``(fg_box, border_chars, bg_label)``."""
    if is_current:
        fg_box = (0, 255, 255)  # Bright cyan
        border_chars = {"corner": "#", "horiz": "=", "vert": "║"}
        bg_label = (0, 64, 64)  # Dark cyan
    else:
        fg_box = (200, 200, 200)  # Gray
        border_chars = {"corner": "+", "horiz": "-", "vert": "|"}
        bg_label = (0, 0, 0)  # Black
    return fg_box, border_chars, bg_label


def _draw_box_frame(
    console: tcod.console.Console,
    abs_x: int,
    abs_y: int,
    fg_box: tuple[int, int, int],
    border_chars: dict[str, str],
) -> None:
    """Draw the 4 corners, top/bottom, and left/right borders."""
    for cx, cy in [
        (abs_x, abs_y),
        (abs_x + BOX_WIDTH - 1, abs_y),
        (abs_x, abs_y + BOX_HEIGHT - 1),
        (abs_x + BOX_WIDTH - 1, abs_y + BOX_HEIGHT - 1),
    ]:
        console.print(x=cx, y=cy, string=border_chars["corner"], fg=fg_box)
    for cx in range(abs_x + 1, abs_x + BOX_WIDTH - 1):
        console.print(x=cx, y=abs_y, string=border_chars["horiz"], fg=fg_box)
        console.print(x=cx, y=abs_y + BOX_HEIGHT - 1, string=border_chars["horiz"], fg=fg_box)
    for cy in range(abs_y + 1, abs_y + BOX_HEIGHT - 1):
        console.print(x=abs_x, y=cy, string=border_chars["vert"], fg=fg_box)
        console.print(x=abs_x + BOX_WIDTH - 1, y=cy, string=border_chars["vert"], fg=fg_box)


def _draw_box_content(
    console: tcod.console.Console,
    abs_x: int,
    abs_y: int,
    label: str,
    zdr: int,
    status: Status,
    is_current: bool,
    bg_label: tuple[int, int, int],
) -> None:
    """Draw the inner label and ZDR line; fill the inside for the
    current node so the yellow text stands out."""
    glyph = _status_glyph(status)
    inner_label = label[: BOX_INNER_W - 2].center(BOX_INNER_W - 2)
    zdr_text = f"{glyph}ZDR:{zdr:<3}".center(BOX_INNER_W)
    fg_status = status_color(status)
    fg_label = (255, 255, 0) if is_current else (200, 200, 200)

    if is_current:
        # Fill inner area with background color.
        for r in range(abs_y + 1, abs_y + BOX_HEIGHT - 1):
            for c in range(abs_x + 1, abs_x + BOX_WIDTH - 1):
                console.print(x=c, y=r, string=" ", bg=bg_label)

    console.print(
        x=abs_x + 1,
        y=abs_y + 1,
        string=inner_label,
        fg=fg_label,
        bg=bg_label,
    )
    console.print(
        x=abs_x + 1,
        y=abs_y + 2,
        string=zdr_text,
        fg=fg_status,
        bg=bg_label,
    )


def _draw_box_external_markers(
    console: tcod.console.Console,
    main: Region,
    abs_x: int,
    abs_y: int,
) -> None:
    """Draw the bright-yellow "→ ← ↑ ↓" arrows + "[ YOU ]" label
    that visually mark the player's current node."""
    marker_color = (255, 255, 0)
    if abs_x > main.x:
        console.print(x=abs_x - 1, y=abs_y + 1, string=">", fg=marker_color)
    if abs_x + BOX_WIDTH < main.x2:
        console.print(x=abs_x + BOX_WIDTH, y=abs_y + 1, string="<", fg=marker_color)
    if abs_y > main.y:
        console.print(
            x=abs_x + BOX_WIDTH // 2,
            y=abs_y - 1,
            string="v",
            fg=marker_color,
        )
    if abs_y + BOX_HEIGHT < main.y2:
        console.print(
            x=abs_x + BOX_WIDTH // 2,
            y=abs_y + BOX_HEIGHT,
            string="^",
            fg=marker_color,
        )
    you_here = "[ YOU ]"
    if abs_y > main.y + 1:
        console.print(
            x=abs_x + (BOX_WIDTH - len(you_here)) // 2,
            y=abs_y - 1,
            string=you_here,
            fg=marker_color,
        )


def _draw_box_direction_hints(
    console: tcod.console.Console,
    abs_x: int,
    abs_y: int,
    direction_hints: dict[str, str],
    bg_label: tuple[int, int, int],
) -> None:
    """Overlay arrow glyphs on the border edges where a neighbor
    exists.  Lets the player see at a glance which arrow keys move
    them somewhere.
    """
    hint_color = (200, 255, 200)  # Light green
    cx = abs_x + BOX_WIDTH // 2
    cy = abs_y + BOX_HEIGHT // 2
    for code, glyph in direction_hints.items():
        if code == "L":
            console.print(x=abs_x, y=cy, string=glyph, fg=hint_color, bg=bg_label)
        elif code == "R":
            console.print(
                x=abs_x + BOX_WIDTH - 1,
                y=cy,
                string=glyph,
                fg=hint_color,
                bg=bg_label,
            )
        elif code == "U":
            console.print(x=cx, y=abs_y, string=glyph, fg=hint_color, bg=bg_label)
        elif code == "D":
            console.print(
                x=cx,
                y=abs_y + BOX_HEIGHT - 1,
                string=glyph,
                fg=hint_color,
                bg=bg_label,
            )


def _draw_box_fog(
    console: tcod.console.Console,
    main: Region,
    col: int,
    row: int,
    visibility: Visibility,
) -> None:
    """Render a fog-of-war node box."""
    abs_x = main.x + col
    abs_y = main.y + row
    if visibility is Visibility.UNKNOWN:
        console.print(x=abs_x + 4, y=abs_y + 1, string="?", fg=(64, 64, 64))
        return
    if visibility is Visibility.ADJACENT:
        dim = (120, 120, 120)
        if not main.contains(abs_x, abs_y):
            return
        for c in range(abs_x, abs_x + BOX_WIDTH):
            console.print(x=c, y=abs_y, string="-", fg=dim)
            console.print(x=c, y=abs_y + BOX_HEIGHT - 1, string="-", fg=dim)
        for r in range(abs_y + 1, abs_y + BOX_HEIGHT - 1):
            console.print(x=abs_x, y=r, string="|", fg=dim)
            console.print(x=abs_x + BOX_WIDTH - 1, y=r, string="|", fg=dim)
        console.print(
            x=abs_x + 1,
            y=abs_y + 1,
            string="?  ?".center(BOX_INNER_W),
            fg=(100, 100, 100),
        )
        console.print(
            x=abs_x + 1,
            y=abs_y + 2,
            string="(adjacent)".center(BOX_INNER_W),
            fg=(100, 100, 100),
        )


def _draw_edge_line(
    console: tcod.console.Console,
    main: Region,
    src: tuple[int, int],
    dst: tuple[int, int],
) -> None:
    """Draw an L-shaped connection (clipped to main region)."""
    sx, sy = src
    dx, dy = dst
    cnx, cny = main.x + sx + BOX_WIDTH, main.y + sy + 1
    tnx, tny = main.x + dx - 1, main.y + dy + 1
    line_color = (96, 96, 96)
    if cny == tny:
        if cnx < tnx:
            start, end = cnx + 1, tnx - 1
        else:
            start, end = tnx + 1, cnx - 1
        for c in range(start, end + 1):
            console.print(x=c, y=cny, string="-", fg=line_color)
        return
    corner_x, corner_y = tnx, cny
    if cnx < corner_x:
        for c in range(cnx + 1, corner_x):
            console.print(x=c, y=cny, string="-", fg=line_color)
    else:
        for c in range(corner_x + 1, cnx):
            console.print(x=c, y=cny, string="-", fg=line_color)
    corner_char = (
        "\u2514"
        if cnx < corner_x and tny < cny
        else "\u2518"
        if cnx > corner_x and tny < cny
        else "\u250c"
        if cnx < corner_x
        else "\u2510"
    )
    console.print(x=corner_x, y=corner_y, string=corner_char, fg=line_color)
    if tny < cny:
        for r in range(tny + 1, cny):
            console.print(x=tnx, y=r, string="|", fg=line_color)
    else:
        for r in range(cny + 1, tny):
            console.print(x=tnx, y=r, string="|", fg=line_color)


def _compute_direction_hints(
    matrix: MatrixGraph,
    state: AppState,
    layouts: dict[str, tuple[int, int]],
) -> dict[str, str]:
    """Return cardinal direction hints for the current node (ADR-0045).

    For each neighbor, compute the dominant axis and map to a single
    glyph. The dict has at most four keys (L / R / U / D).
    """
    direction_hints: dict[str, str] = {}
    if not state.current_node_id:
        return direction_hints
    cx, cy = layouts.get(state.current_node_id, (0, 0))
    for nbr in matrix.neighbors(state.current_node_id):
        np = layouts.get(nbr.id)
        if np is None:
            continue
        nx, ny = np
        dx, dy = nx - cx, ny - cy
        if dx < 0 and abs(dx) >= abs(dy):
            direction_hints.setdefault("L", "◄")
        elif dx > 0 and abs(dx) >= abs(dy):
            direction_hints.setdefault("R", "►")
        elif dy < 0 and abs(dy) > abs(dx):
            direction_hints.setdefault("U", "▲")
        elif dy > 0 and abs(dy) > abs(dx):
            direction_hints.setdefault("D", "▼")
    return direction_hints


def _render_matrix_edges(
    console: tcod.console.Console,
    main_r: Region,
    matrix: MatrixGraph,
    layouts: dict[str, tuple[int, int]],
    expl: ExplorationState | None,
    use_fog: bool,
) -> None:
    """Draw every visible edge, skipping fog-of-war unknowns."""
    for edge in matrix.edges:
        if use_fog and expl is not None:
            sv = expl.visibility(matrix, edge.src)
            dv = expl.visibility(matrix, edge.dst)
            if sv is Visibility.UNKNOWN or dv is Visibility.UNKNOWN:
                continue
        sp = layouts.get(edge.src)
        dp = layouts.get(edge.dst)
        if sp is None or dp is None:
            continue
        _draw_edge_line(console, main_r, sp, dp)


def _render_matrix_nodes(
    console: tcod.console.Console,
    main_r: Region,
    matrix: MatrixGraph,
    layouts: dict[str, tuple[int, int]],
    state: AppState,
    ppl: int,
    expl: ExplorationState | None,
    use_fog: bool,
    direction_hints: dict[str, str],
) -> None:
    """Draw every node as a box (or fog placeholder if unknown)."""
    for node in matrix.nodes:
        pos = layouts.get(node.id)
        if pos is None:
            continue
        if use_fog and expl is not None:
            vis = expl.visibility(matrix, node.id)
            if vis is Visibility.UNKNOWN:
                _draw_box_fog(console, main_r, pos[0], pos[1], Visibility.UNKNOWN)
                continue
            if vis is Visibility.ADJACENT:
                _draw_box_fog(console, main_r, pos[0], pos[1], Visibility.ADJACENT)
                continue
        _draw_box(
            console,
            main_r,
            pos[0],
            pos[1],
            _short_kind(node.kind),
            node_zdr(node),
            node_status(node, ppl),
            is_current=(node.id == state.current_node_id),
            direction_hints=direction_hints if node.id == state.current_node_id else None,
        )


def _render_matrix_side_panel(
    console: tcod.console.Console,
    side_r: Region,
    matrix: MatrixGraph,
    state: AppState,
    zone: Node | None,
    st: Status,
    expl: ExplorationState | None,
    use_fog: bool,
) -> None:
    """Draw the side panel: current-node status, neighbor list, and
    either a minimap+breadcrumb (no current zone) or a status panel.
    """
    if zone is not None:
        neighbors = (
            _adjacent_nodes_list(matrix, state.current_node_id)
            if matrix and state.current_node_id
            else []
        )
        state.matrix_nav_index = (
            max(0, min(state.matrix_nav_index, len(neighbors) - 1)) if neighbors else 0
        )
        side_lines = [
            "=== CURRENT NODE ===",
            f"Name: {zone.label}",
            f"Type: {_short_kind(zone.kind)}",
            f"ZDR: {node_zdr(zone)} | Status: {st.value.upper()}",
            "",
        ]
        if neighbors:
            side_lines.append("=== MOVE TO ===")
            for i, n in enumerate(neighbors):
                cursor = ">" if i == state.matrix_nav_index else " "
                side_lines.append(f"{cursor} {n.label} ({_short_kind(n.kind)})")
            side_lines.extend(
                [
                    "",
                    "[↑↓] Select  [Enter] Move",
                    "[SPACE] Action menu",
                ]
            )
        else:
            side_lines.extend(
                [
                    "=== WHAT TO DO ===",
                    "",
                    "[SPACE] Action menu",
                ]
            )
        side_lines.extend(
            [
                "→ ESC: Leave matrix",
                "",
                f"Visited: {len(expl.discovered) if expl else 0} nodes",
            ]
        )
        draw_side(console, side_r, label="STATUS", lines=side_lines)
    elif use_fog and expl is not None:
        _draw_minimap(console, matrix, expl, side_r)
        _draw_breadcrumb(console, matrix, expl, side_r)
        _draw_mobility_stats(console, state, side_r)


def _render_matrix_message_log(
    console: tcod.console.Console,
    side_r: Region,
    status_messages: Any,
) -> None:
    """Render the most recent 3 status messages in a thin overlay
    above the controls panel (ADR-0047).
    """
    if not status_messages:
        return
    log_region = Region(
        RegionId.SIDE,
        x=side_r.x,
        y=side_r.y2 - 2,
        w=side_r.w,
        h=3,
    )
    draw_message_log(
        console,
        log_region,
        status_messages[-3:],
        max_lines=3,
    )


def _render_matrix_controls(
    console: tcod.console.Console,
    ctrl_r: Region,
    zone: Node | None,
) -> None:
    """Draw the controls bar at the bottom of the matrix screen."""
    if zone is not None:
        action_hint = "SPACE: Action menu"
        if zone.kind is NodeKind.DATA:
            action_hint = "SPACE: Extract data (mission objective)"
        elif zone.kind is NodeKind.ICE:
            action_hint = "SPACE: Engage ICE (combat)"
        elif zone.kind is NodeKind.EXIT:
            action_hint = "SPACE: Jack out (exit matrix)"
        draw_controls(
            console,
            ctrl_r,
            lines=[
                f"↑/↓: Select  |  ←/→: Move spatially  |  Enter: Confirm  |  {action_hint}",
                "ESC: Leave matrix  |  Q: Quit",
            ],
        )
    else:
        draw_controls(
            console,
            ctrl_r,
            lines=[
                "[← → ↑ ↓] Move  [SPACE] Action  [ESC] Jack out",
                "[Q] Quit",
            ],
        )


def render_matrix(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    layouts: dict[str, tuple[int, int]],
    prog_registry: ProgramRegistry | None = None,
    ice_registry: IceRegistry | None = None,
) -> None:
    """Render the matrix screen with fog + shell (ADR-0020).

    If state.action_menu_open is True, render the action menu popup.
    """
    matrix = state.matrix
    if matrix is None or state.current_node_id is None:
        console.clear(bg=(0, 0, 0))
        console.print(x=2, y=2, string="(no matrix loaded)", fg=(255, 0, 0))
        return

    ppl = calculate_ppl(state.player_loadout)
    zone = matrix.get(state.current_node_id)
    zdr, st = _compute_zone_stats(zone, ppl)
    zone_str = zone_label(t, zone.zone) if zone is not None else "?"

    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    side_r = shell[RegionId.SIDE]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]
    panel_r = shell[RegionId.STATUS_PANEL]

    _init_matrix_shell(console, shell)
    render_status_panel(console, state, panel_r)
    _draw_matrix_title(console, title_r, zone, zdr, st, ppl, zone_str)
    _draw_matrix_main_content(console, main_r, matrix, layouts, state, ppl, zone, st)
    use_fog = state.exploration is not None
    _render_matrix_side_panel(console, side_r, matrix, state, zone, st, state.exploration, use_fog)
    _render_matrix_message_log(console, side_r, state.status_messages)
    _render_matrix_controls(console, ctrl_r, zone)
    _draw_matrix_footer(console, foot_r, state)
    _render_action_menu_overlay(console, t, state, matrix, main_r)


# ------------------------------------------------------------------
# render_matrix helpers
# ------------------------------------------------------------------


def _compute_zone_stats(zone: Any, ppl: int) -> tuple[int, Status]:
    """Return (zdr, status) for the current zone (or 0/MATCH if none)."""
    if zone is None:
        return 0, Status.MATCH
    return node_zdr(zone), node_status(zone, ppl)


def _init_matrix_shell(console: tcod.console.Console, shell: dict[RegionId, Region]) -> None:
    """Clear every region and draw the dividers once."""
    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console, shell)


def _draw_matrix_title(
    console: tcod.console.Console,
    title_r: Region,
    zone: Any,
    zdr: int,
    st: Status,
    ppl: int,
    zone_str: str,
) -> None:
    """Draw the top title strip with the current-node summary."""
    if zone is None:
        draw_title(console, title_r, title="MATRIX", subtitle="Connecting...")
        return
    ratio = ppl / zdr if zdr > 0 else float("inf")
    title_text = f"MATRIX — {zone.label} [{_short_kind(zone.kind)}]"
    status_text = (
        f"PPL: {ppl}  |  Zone: {zone_str}  |  "
        f"ZDR: {zdr}  |  Status: {st.value.upper()} ({ratio:.2f}x)"
    )
    draw_title(console, title_r, title=title_text, subtitle=status_text)


def _draw_matrix_main_content(
    console: tcod.console.Console,
    main_r: Region,
    matrix: MatrixGraph,
    layouts: dict[str, tuple[int, int]],
    state: AppState,
    ppl: int,
    zone: Any,
    st: Status,
) -> None:
    """Draw the centre column: edges, direction hints, then nodes."""
    exploration = state.exploration
    use_fog = exploration is not None
    expl: ExplorationState | None = exploration
    _render_matrix_edges(console, main_r, matrix, layouts, expl, use_fog)
    direction_hints = _compute_direction_hints(matrix, state, layouts)
    _render_matrix_nodes(
        console, main_r, matrix, layouts, state, ppl, expl, use_fog, direction_hints
    )


def _draw_matrix_footer(console: tcod.console.Console, foot_r: Region, state: AppState) -> None:
    """Draw the footer with the game-time line."""
    draw_footer(
        console,
        foot_r,
        text=f"Step {state.demo_step}  T+{state.demo_elapsed_s:.1f}s",
        status_messages=state.status_messages,
    )


def _render_action_menu_overlay(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    matrix: MatrixGraph,
    main_r: Region,
) -> None:
    """If the action menu is open, render it as a centred popup."""
    if not state.action_menu_open:
        return
    if state.current_node_id is None:
        return
    current_node = matrix.get(state.current_node_id)
    if current_node is None:
        return
    # Center popup in main area
    menu_w = 50
    menu_h = 12
    menu_x = main_r.x + (main_r.w - menu_w) // 2
    menu_y = main_r.y + (main_r.h - menu_h) // 2
    menu_region = Region(
        id=RegionId.MAIN,  # Reuse ID (not a new region)
        x=menu_x,
        y=menu_y,
        w=menu_w,
        h=menu_h,
    )
    action_menu.render_action_menu(console, t, state, current_node, menu_region)
