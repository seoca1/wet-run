"""Cyberspace view: scrolling graph-based exploration.

Renders a large branching graph with:
- Infinite scrolling (camera follows player)
- Multiple depth levels
- Branching tree visualization
- Real-time viewport updates
"""

from __future__ import annotations

import random

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ..audio import safe_play
from ..combat.gibson_fluff import push_fluff
from ..combat.palette import (
    DAMAGE_FLASH_COLOR,
    DEFAULT_COLOR,
    GLITCH_COLOR,
    GOLIATH_PARTICLE_COLOR,
    GRAY_DARK,
    GRAY_LIGHT,
    GRAY_MID,
    GRAY_MID_LIGHT,
    GREEN_PURE,
    ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
    PURPLE_ICE,
    SHIELD_COLOR,
    TIER_GOLD,
)
from ..combat.registry import IceRegistry, ProgramRegistry
from ..i18n import Translator
from ..lore import (
    check_memory_fragment_on_node_entry,
    load_encounter_table,
)
from ..matrix import MatrixGraph, Node, NodeKind
from ..matrix.anomaly_reward import check_anomaly_reward_on_node_entry
from ..matrix.cyberspace_generator import CyberspaceLayout, DepthLevel
from ..matrix.faction_tension import check_faction_tension_on_node_entry
from ..matrix.near_miss import check_near_miss_extraction
from . import action_menu
from .config import DATA_DIR
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

_ENCOUNTER_TABLE = load_encounter_table(DATA_DIR / "lore" / "encounter_table.json")

# Camera/viewport state
_camera_x: float = 0.0
_camera_y: float = 0.0
_camera_initialized: bool = False

# Room glyphs by node type
_ROOM_GLYPHS = {
    NodeKind.ENTRY: "▶",
    NodeKind.EXIT: "■",
    NodeKind.DATA: "$",
    NodeKind.ICE: "!",
    NodeKind.CONSTRUCT: "?",
    NodeKind.ROUTER: "·",
    NodeKind.SYSTEM: "▣",
    NodeKind.CORE: "◎",
}

# Anomaly variant overrides (ADR-0140 P2.6 — Variable Reward Nodes).
# Applied to is_anomaly DATA nodes for visual distinction.
_ANOMALY_GLYPH = "◆"
_ANOMALY_COLOR = PURPLE_ICE

# Colors by node type
_NODE_COLORS = {
    NodeKind.ENTRY: GREEN_PURE,
    NodeKind.EXIT: GREEN_PURE,
    NodeKind.DATA: TIER_GOLD,
    NodeKind.ICE: DAMAGE_FLASH_COLOR,
    NodeKind.CONSTRUCT: GLITCH_COLOR,
    NodeKind.ROUTER: GRAY_MID_LIGHT,
    NodeKind.SYSTEM: SHIELD_COLOR,
    NodeKind.CORE: PURPLE_ICE,
}

# Depth level colors (for depth indicator)
_DEPTH_COLORS = {
    DepthLevel.SURFACE: GRAY_MID,
    DepthLevel.SHALLOW: GRAY_LIGHT,
    DepthLevel.MID: DEFAULT_COLOR,
    DepthLevel.DEEP: (255, 200, 100),
    DepthLevel.CORE: GOLIATH_PARTICLE_COLOR,
}


def render_cyberspace(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    prog_registry: ProgramRegistry | None = None,
    ice_registry: IceRegistry | None = None,
) -> None:
    """Render the cyberspace screen with scrolling viewport."""
    global _camera_x, _camera_y, _camera_initialized

    matrix = state.matrix
    if matrix is None or state.current_node_id is None:
        return

    # Get layouts from state
    if not hasattr(state, "cyberspace_layouts") or state.cyberspace_layouts is None:
        return

    layouts: dict[str, CyberspaceLayout] = state.cyberspace_layouts  # type: ignore

    current_node = matrix.get(state.current_node_id)
    if current_node is None:
        return

    # Initialize camera on first render
    if not _camera_initialized:
        current_layout = layouts.get(state.current_node_id)
        if current_layout:
            _camera_x = current_layout.x
            _camera_y = current_layout.y
        _camera_initialized = True

    # Smooth camera follow
    current_layout = layouts.get(state.current_node_id)
    if current_layout:
        # Interpolate camera toward player
        _camera_x += (current_layout.x - _camera_x) * 0.3
        _camera_y += (current_layout.y - _camera_y) * 0.3

    # Get shell
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
    title = f"CYBERSPACE — {current_node.label} [{current_node.kind.value.upper()}]"
    depth_name = current_layout.depth.value if current_layout else "?"
    subtitle = f"Depth: {depth_name.upper()}  |  Use ↑↓←→ to navigate the graph"
    draw_title(console, title_r, title=title, subtitle=subtitle)

    # Main area: render cyberspace
    _render_cyberspace_view(console, main_r, state, matrix, layouts)

    # Action menu overlay
    if state.action_menu_open:
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
            "↑↓←→ Move along graph branches  |  SPACE Action  |  ESC Leave",
            f"View: ({_camera_x:.0f}, {_camera_y:.0f})  |  Q Quit",
        ],
    )

    # Footer
    draw_footer(
        console,
        foot_r,
        text=f"Step {state.demo_step}  T+{state.demo_elapsed_s:.1f}s",
        status_messages=state.status_messages,
    )


def _render_cyberspace_view(
    console: tcod.console.Console,
    main: Region,
    state: AppState,
    matrix: MatrixGraph,
    layouts: dict[str, CyberspaceLayout],
) -> None:
    """Render the cyberspace graph with camera viewport."""
    global _camera_x, _camera_y

    # Camera scaling (1 unit = 1 char)
    scale = 1.0
    center_x = main.x + main.w // 2
    center_y = main.y + main.h // 2

    # Viewport bounds
    view_w = main.w - 4
    view_h = main.h - 4

    # Calculate visible area
    view_w // 2
    view_h // 2

    # First, draw connections (behind nodes)
    for edge in matrix.edges:
        src_layout = layouts.get(edge.src)
        dst_layout = layouts.get(edge.dst)
        if src_layout is None or dst_layout is None:
            continue

        # World to screen coordinates
        sx = int(center_x + (src_layout.x - _camera_x) * scale)
        sy = int(center_y + (src_layout.y - _camera_y) * scale)
        dx = int(center_x + (dst_layout.x - _camera_x) * scale)
        dy = int(center_y + (dst_layout.y - _camera_y) * scale)

        # Skip if both endpoints are off-screen
        if not _is_visible(sx, sy, main) and not _is_visible(dx, dy, main):
            continue

        # Draw line (L-shaped or direct)
        _draw_line(console, main, sx, sy, dx, dy, GRAY_DARK)

    # Then draw nodes on top
    for node in matrix.nodes:
        layout = layouts.get(node.id)
        if layout is None:
            continue

        # World to screen
        sx = int(center_x + (layout.x - _camera_x) * scale)
        sy = int(center_y + (layout.y - _camera_y) * scale)

        # Skip if off-screen
        if not _is_visible(sx, sy, main):
            continue

        is_current = node.id == state.current_node_id
        _draw_node(console, main, sx, sy, node, layout, is_current)

    # Draw camera/viewport indicator
    _draw_viewport_indicator(console, main, layouts, matrix)


def _is_visible(x: int, y: int, region: Region) -> bool:
    """Check if a point is within the region."""
    return region.contains(x, y)


def _draw_node(
    console: tcod.console.Console,
    main: Region,
    x: int,
    y: int,
    node: Node,
    layout: CyberspaceLayout,
    is_current: bool,
) -> None:
    """Draw a single node at the given screen position."""
    is_anomaly = bool(getattr(node, "is_anomaly", False))
    glyph = _ANOMALY_GLYPH if is_anomaly else _ROOM_GLYPHS.get(node.kind, "?")

    if is_current:
        fg = ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR  # Yellow for current
        # Draw a border around current
        if main.contains(x - 2, y):
            console.print(x=x - 2, y=y, string="<", fg=fg)
        if main.contains(x + 2, y):
            console.print(x=x + 2, y=y, string=">", fg=fg)
        if main.contains(x, y - 1):
            console.print(x=x, y=y - 1, string="^", fg=fg)
        if main.contains(x, y + 1):
            console.print(x=x, y=y + 1, string="v", fg=fg)
        # Draw player marker
        if main.contains(x, y):
            console.print(x=x, y=y, string="◉", fg=fg)
    else:
        if is_anomaly:
            fg = _ANOMALY_COLOR
        else:
            fg = _NODE_COLORS.get(node.kind, DEFAULT_COLOR)
        if main.contains(x, y):
            console.print(x=x, y=y, string=glyph, fg=fg)

    # Label below node
    if main.contains(x, y + 2) and len(node.label) <= 6:
        label_x = x - len(node.label) // 2
        if main.contains(label_x, y + 2):
            console.print(x=label_x, y=y + 2, string=node.label, fg=fg)


def _draw_line(
    console: tcod.console.Console,
    main: Region,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    fg: tuple[int, int, int],
) -> None:
    """Draw a line between two points using Bresenham-like algorithm."""
    # L-shaped path: horizontal then vertical
    # First, horizontal segment
    if x1 != x2:
        step = 1 if x2 > x1 else -1
        for x in range(x1, x2 + step, step):
            if main.contains(x, y1) and x != x1 and x != x2:
                console.print(x=x, y=y1, string="─", fg=fg)

    # Then vertical segment
    if y1 != y2:
        step = 1 if y2 > y1 else -1
        for y in range(y1, y2 + step, step):
            if main.contains(x2, y) and y != y1 and y != y2:
                console.print(x=x2, y=y, string="│", fg=fg)

    # Corner
    if x1 != x2 and y1 != y2:
        # Choose corner character
        if x2 > x1 and y2 > y1:
            corner = "┐"
        elif x2 > x1 and y2 < y1:
            corner = "┌"
        elif x2 < x1 and y2 > y1:
            corner = "┘"
        else:
            corner = "└"
        if main.contains(x2, y1):
            console.print(x=x2, y=y1, string=corner, fg=fg)


def _draw_viewport_indicator(
    console: tcod.console.Console,
    main: Region,
    layouts: dict[str, CyberspaceLayout],
    matrix: MatrixGraph,
) -> None:
    """Draw a minimap in the corner showing the whole cyberspace."""
    if not layouts:
        return

    minimap_w = 20
    minimap_h = 10
    minimap_x = main.x2 - minimap_w
    minimap_y = main.y + 1

    # Find bounds
    xs = [layout.x for layout in layouts.values()]
    ys = [layout.y for layout in layouts.values()]
    if not xs or not ys:
        return

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    range_x = max(1, max_x - min_x)
    range_y = max(1, max_y - min_y)

    # Draw minimap border
    fg_border = GRAY_DARK
    console.print(x=minimap_x, y=minimap_y, string="┌" + "─" * (minimap_w - 2) + "┐", fg=fg_border)
    for yi in range(minimap_h - 2):
        console.print(x=minimap_x, y=minimap_y + 1 + yi, string="│", fg=fg_border)
        console.print(x=minimap_x + minimap_w - 1, y=minimap_y + 1 + yi, string="│", fg=fg_border)
    console.print(
        x=minimap_x,
        y=minimap_y + minimap_h - 1,
        string="└" + "─" * (minimap_w - 2) + "┘",
        fg=fg_border,
    )

    # Draw nodes on minimap
    for node in matrix.nodes:
        layout = layouts.get(node.id)
        if layout is None:
            continue
        # Scale to minimap
        mx = minimap_x + 1 + int((layout.x - min_x) / range_x * (minimap_w - 4))
        my = minimap_y + 1 + int((layout.y - min_y) / range_y * (minimap_h - 4))
        if (
            minimap_x < mx < minimap_x + minimap_w - 1
            and minimap_y < my < minimap_y + minimap_h - 1
        ):
            glyph = _ROOM_GLYPHS.get(node.kind, "·")
            color = _NODE_COLORS.get(node.kind, GRAY_MID)
            console.print(x=mx, y=my, string=glyph, fg=color)

    # Draw camera viewport on minimap
    cam_min_x = _camera_x - 15
    cam_max_x = _camera_x + 15
    cam_x1 = minimap_x + 1 + int((cam_min_x - min_x) / range_x * (minimap_w - 4))
    cam_x2 = minimap_x + 1 + int((cam_max_x - min_x) / range_x * (minimap_w - 4))

    for x in range(max(minimap_x + 1, cam_x1), min(minimap_x + minimap_w - 2, cam_x2 + 1)):
        if minimap_y < minimap_y + minimap_h - 1 and minimap_y + minimap_h - 1 < console.height:
            console.print(
                x=x, y=minimap_y + minimap_h - 2, string="─", fg=ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR
            )


# ============================================================================
# Input handling
# ============================================================================


def handle_cyberspace_input(
    event: tcod.event.Event,
    state: AppState,
    prog_registry: ProgramRegistry | None = None,
    ice_registry: IceRegistry | None = None,
) -> bool:
    """Handle input on the cyberspace screen."""
    global _camera_initialized

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
        _camera_initialized = False  # Reset for next time
        return False
    if event.sym is KeySym.ESCAPE:
        # Return to cyberspace browser (not hub) to allow server selection
        if hasattr(state, "world_map") and state.world_map is not None:
            state.screen = ScreenKind.CYBERSPACE_BROWSER
            state.status_messages.append(">>> Returned to server browser")
        else:
            state.screen = ScreenKind.HUB
        _camera_initialized = False
        return True
    if is_confirm_key(event.sym):
        if state.matrix and state.current_node_id:
            node = state.matrix.get(state.current_node_id)
            if node:
                # Check if NPC
                if node.kind is NodeKind.CONSTRUCT and "dixie" in node.id.lower():
                    state.npc_state = NPCState(event=DIXIE_FLATLINE_EVENT)
                    state.screen = ScreenKind.NPC
                    state.status_messages.append(">>> Started NPC encounter: Dixie Flatline")
                    return True
                # Normal action menu
                state.status_messages.append(f">>> Action menu opened for {node.label}")
                state.action_menu_open = True
        return True

    # Cardinal direction movement
    if event.sym in (KeySym.UP, KeySym.DOWN, KeySym.LEFT, KeySym.RIGHT):
        _handle_cyberspace_movement(state, event.sym)
        return True

    return True


def _handle_cyberspace_movement(state: AppState, sym: KeySym) -> None:
    """Handle movement along graph branches in cyberspace."""
    matrix = state.matrix
    if matrix is None or state.current_node_id is None:
        return

    if not hasattr(state, "cyberspace_layouts") or state.cyberspace_layouts is None:
        return

    layouts: dict[str, CyberspaceLayout] = state.cyberspace_layouts  # type: ignore[assignment]

    current_layout = layouts.get(state.current_node_id)
    if current_layout is None:
        return
    # Play movement sound at start of movement
    safe_play("movement/nav_step")

    cx, cy = current_layout.x, current_layout.y

    # Find the neighbor that best matches the direction
    best_neighbor = None
    best_score: tuple[float, float] = (float("inf"), float("inf"))

    direction_vectors = {
        KeySym.UP: (0, -1),  # Up = less depth (closer to surface)
        KeySym.DOWN: (0, 1),  # Down = more depth (deeper)
        KeySym.LEFT: (-1, 0),  # Left = left branch
        KeySym.RIGHT: (1, 0),  # Right = right branch
    }

    dx, dy = direction_vectors[sym]
    direction_name = {
        KeySym.UP: "UP (shallower)",
        KeySym.DOWN: "DOWN (deeper)",
        KeySym.LEFT: "LEFT",
        KeySym.RIGHT: "RIGHT",
    }[sym]

    # Look at neighbors
    for neighbor in matrix.neighbors(state.current_node_id):
        n_layout = layouts.get(neighbor.id)
        if n_layout is None:
            continue
        nx, ny = n_layout.x, n_layout.y

        # Compute direction from current to neighbor
        ndx = float(nx - cx)
        ndy = float(ny - cy)

        # Check if this neighbor is in the desired direction
        if dx != 0:
            if (dx > 0 and ndx <= 0) or (dx < 0 and ndx >= 0):
                continue
        if dy != 0:
            if (dy > 0 and ndy <= 0) or (dy < 0 and ndy >= 0):
                continue

        # Score: prefer the primary direction
        primary = abs(ndx) if dx != 0 else abs(ndy)
        secondary = abs(ndy) if dx != 0 else abs(ndx)
        score = (primary, secondary)

        if score < best_score:
            best_score = score
            best_neighbor = neighbor

    if best_neighbor is not None:
        state.current_node_id = best_neighbor.id
        if state.exploration is not None:
            state.exploration.visit(best_neighbor.id)
        state.status_messages.append(
            f">>> Moved {direction_name} to {best_neighbor.label} ({best_neighbor.kind.value})"
        )
        push_fluff(state, "zone_transition")
        faction_value = best_neighbor.faction.value
        faction_str = None if faction_value == "none" else faction_value
        check_memory_fragment_on_node_entry(
            state,
            _ENCOUNTER_TABLE,
            state.memory_fragment_tracker,
            random.Random(),
            current_zone=best_neighbor.zone.value,
            current_grade=state.player_grade,
            faction=faction_str,
        )
        # ADR-0140 P2.6 — Variable Reward Nodes. Anomaly DATA nodes
        # grant a one-shot bonus reward on entry (Pillar 4 safe).
        check_anomaly_reward_on_node_entry(
            state,
            best_neighbor,
            random.Random(),
            already_triggered=state.anomaly_triggered,
        )
        # ADR-0140 P2.7 — Faction Tension Events. Per-faction DATA node
        # entry has 25% chance of triggering +ve (high rep) or -ve (low rep)
        # event based on FactionReputation (Pillar 4 safe, one-shot).
        if best_neighbor.kind is NodeKind.DATA:
            check_faction_tension_on_node_entry(
                state,
                best_neighbor.faction,
                random.Random(),
                already_triggered=state.faction_tension_triggered,
            )
        # ADR-0140 P3.6 — Near-Miss Extraction. Exit node entry with
        # HP > 80% grants bonus reward (Pillar 4 safe, one-shot).
        if best_neighbor.kind is NodeKind.EXIT:
            check_near_miss_extraction(
                state,
                already_triggered=state.near_miss_triggered,
            )
            state.near_miss_triggered = True
    else:
        state.status_messages.append(f">>> No node in direction {direction_name}")
        safe_play("movement/nav_block")
