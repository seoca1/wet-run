"""Matrix view input handling (ADR-0141 module split).

Extracted from matrix_view.py to reduce the rendering module below
the 1000+ LOC threshold. Handles keyboard input, cursor navigation,
directional movement, and jack-out action.

Public API (preserved from matrix_view.py):
- handle_matrix_input: Main entry point for tcod KeyDown events
- get_layout: Memoized node-id to (x, y) position map

Internal helpers (private):
- _adjacent_nodes, _adjacent_nodes_list: Graph traversal
- _handle_cursor_navigation: UP/DOWN cursor-based selection
- _handle_movement: LEFT/RIGHT/arrow direction-based movement
- _jack_out: Disconnect from matrix, return to HUB
"""

from __future__ import annotations

import tcod.event
from tcod.event import KeyDown, KeySym

from ..combat.registry import IceRegistry, ProgramRegistry
from ..matrix import MatrixGraph, Node
from . import action_menu
from .input_utils import is_confirm_key
from .matrix_minimap import _short_kind
from .state import AppState, ScreenKind

# Cursor navigation keys (↑/↓ to select adjacent node, Enter to move)
_NAVIGATION_KEYS: set[KeySym] = {
    KeySym.UP,
    KeySym.DOWN,
    KeySym.KP_8,  # N (alias for UP)
    KeySym.KP_2,  # S (alias for DOWN)
    KeySym.J,  # vim: down (↑ in conventional terms, but used as ↓ here)
    KeySym.K,  # vim: up (↓ in conventional terms, but used as ↑ here)
}

# Direction unit vectors for movement (ADR-0045)
_DIRECTION_VECTORS: dict[KeySym, tuple[int, int]] = {
    KeySym.LEFT: (-1, 0),
    KeySym.RIGHT: (1, 0),
    KeySym.UP: (0, -1),
    KeySym.DOWN: (0, 1),
    # Diagonals (numpad-style)
    KeySym.KP_7: (-1, -1),  # NW
    KeySym.KP_9: (1, -1),  # NE
    KeySym.KP_1: (-1, 1),  # SW
    KeySym.KP_3: (1, 1),  # SE
    KeySym.KP_8: (0, -1),  # N (alias for UP)
    KeySym.KP_2: (0, 1),  # S (alias for DOWN)
    KeySym.KP_4: (-1, 0),  # W (alias for LEFT)
    KeySym.KP_6: (1, 0),  # E (alias for RIGHT)
    # Vim-style diagonals
    KeySym.H: (-1, 0),
    KeySym.L: (1, 0),
    KeySym.K: (0, 1),
    KeySym.J: (0, -1),
    KeySym.Y: (-1, -1),
    KeySym.U: (1, -1),
    KeySym.B: (-1, 1),
    KeySym.N: (1, 1),
}

_DIRECTION_LABELS: dict[KeySym, str] = {
    KeySym.LEFT: "← LEFT",
    KeySym.RIGHT: "→ RIGHT",
    KeySym.UP: "↑ UP",
    KeySym.DOWN: "↓ DOWN",
    KeySym.KP_7: "↖ NW",
    KeySym.KP_9: "↗ NE",
    KeySym.KP_1: "↙ SW",
    KeySym.KP_3: "↘ SE",
    KeySym.KP_8: "↑ N",
    KeySym.KP_2: "↓ S",
    KeySym.KP_4: "← W",
    KeySym.KP_6: "→ E",
    KeySym.H: "← H",
    KeySym.L: "→ L",
    KeySym.K: "↓ K",
    KeySym.J: "↑ J",
    KeySym.Y: "↖ Y",
    KeySym.U: "↗ U",
    KeySym.B: "↙ B",
    KeySym.N: "↘ N",
}

_last_layout: dict[MatrixGraph, dict[str, tuple[int, int]]] = {}


def get_layout(matrix: MatrixGraph) -> dict[str, tuple[int, int]]:
    """Return a node-id → ``(x, y)`` position map for the given matrix graph.

    Results are memoized in a module-level cache keyed by the matrix object
    itself. The cache is process-wide and never invalidated (matrices are
    typically short-lived per-run).

    Args:
        matrix: The matrix graph to lay out.

    Returns:
        Dict mapping each node id to its rendered ``(x, y)`` position.
    """
    cached = _last_layout.get(matrix)
    if cached is not None:
        return cached
    from ..matrix.graph import compute_layout

    layout = compute_layout(matrix)
    _last_layout[matrix] = layout
    return layout


def _adjacent_nodes(matrix: MatrixGraph, node_id: str) -> set[str]:
    """Return node ids connected to ``node_id`` (in or out edges)."""
    out: set[str] = set()
    for e in matrix.edges:
        if e.src == node_id:
            out.add(e.dst)
        elif e.dst == node_id:
            out.add(e.src)
    return out


def _adjacent_nodes_list(matrix: MatrixGraph, node_id: str) -> list[Node]:
    """Return list of adjacent nodes for cursor selection."""
    adj_ids = _adjacent_nodes(matrix, node_id)
    return [n for n in matrix.nodes if n.id in adj_ids]


def _handle_cursor_navigation(state: AppState, sym: KeySym) -> None:
    """Handle cursor-based node selection (↑/↓ to select, Enter to move).

    Unifies matrix navigation with combat skill selection UX.
    """
    matrix = state.matrix
    if matrix is None or state.current_node_id is None:
        return

    neighbors = _adjacent_nodes_list(matrix, state.current_node_id)
    if not neighbors:
        state.status_messages.append(">>> No adjacent nodes")
        return

    # Clamp cursor to valid range
    state.matrix_nav_index = max(0, min(state.matrix_nav_index, len(neighbors) - 1))

    # Handle key press
    if sym in (KeySym.UP, KeySym.KP_8, KeySym.K):
        # Move cursor up (previous node)
        if state.matrix_nav_index > 0:
            state.matrix_nav_index -= 1
        else:
            state.matrix_nav_index = len(neighbors) - 1  # Wrap to last
        selected = neighbors[state.matrix_nav_index]
        state.status_messages.append(
            f">>> [{state.matrix_nav_index + 1}/{len(neighbors)}] {selected.label}"
        )
    elif sym in (KeySym.DOWN, KeySym.KP_2, KeySym.J):
        # Move cursor down (next node)
        if state.matrix_nav_index < len(neighbors) - 1:
            state.matrix_nav_index += 1
        else:
            state.matrix_nav_index = 0  # Wrap to first
        selected = neighbors[state.matrix_nav_index]
        state.status_messages.append(
            f">>> [{state.matrix_nav_index + 1}/{len(neighbors)}] {selected.label}"
        )


def _handle_movement(state: AppState, sym: KeySym) -> None:
    """Move to the neighbor that best matches the pressed direction (ADR-0045).

    Algorithm:
        1. For each adjacent neighbor (in/out edges), compute the unit
           direction vector using Euclidean normalization.
        2. Score by dot product with the pressed direction (higher = better).
        3. Tie-break by total Manhattan distance (closer = better).
        4. Move to the best-scoring neighbor if score > 0.

    This naturally handles:
        - Cardinal directions (← → ↑ ↓)
        - Diagonal directions (numpad 7/9/1/3, vim Y/U/B/N)
        - Best-match fallback (when no neighbor is exactly in that direction,
          the closest diagonal neighbor wins)

    The matrix is a DAG, but for *exploration* movement we treat edges as
    bidirectional — players should be able to backtrack through visited nodes.
    """
    matrix = state.matrix
    if matrix is None or state.current_node_id is None:
        return
    if sym not in _DIRECTION_VECTORS:
        return

    layouts = _last_layout.get(matrix)
    if layouts is None:
        return
    current_pos = layouts.get(state.current_node_id)
    if current_pos is None:
        return
    cx, cy = current_pos
    press_dx, press_dy = _DIRECTION_VECTORS[sym]

    # Get all adjacent node ids (in or out edges — movement is bidirectional)
    adjacent_ids = _adjacent_nodes(matrix, state.current_node_id)

    best: tuple[float, int, Node] | None = None
    for n in matrix:
        if n.id not in adjacent_ids:
            continue
        if n.id == state.current_node_id:
            continue
        pos = layouts.get(n.id)
        if pos is None:
            continue
        nx, ny = pos
        dx, ny_dy = nx - cx, ny - cy
        # Euclidean-normalize neighbor direction so diagonals preserve angle.
        mag_sq = dx * dx + ny_dy * ny_dy
        if mag_sq == 0:
            continue
        mag = mag_sq**0.5
        ndx, ndy = dx / mag, ny_dy / mag
        # Dot product with pressed direction (1.0 = perfect, 0 = perpendicular).
        dot = ndx * press_dx + ndy * press_dy
        if dot <= 0:
            continue
        # Score: prefer high dot, then short Manhattan distance
        dist = abs(dx) + abs(ny_dy)
        if best is None or (dot, -dist) > (best[0], -best[1]):
            best = (dot, dist, n)
        elif dot == best[0] and dist == best[1]:
            if n.id < best[2].id:
                best = (dot, dist, n)

    if best is not None:
        _, _, target = best
        direction = _DIRECTION_LABELS.get(sym, "?")
        state.status_messages.append(
            f">>> Moved {direction} to {target.label} ({_short_kind(target.kind)})"
        )
        state.current_node_id = target.id
        if state.exploration is not None:
            state.exploration.visit(target.id)
    else:
        direction = _DIRECTION_LABELS.get(sym, "?")
        state.status_messages.append(f">>> No node in direction {direction}")


def _jack_out(state: AppState) -> None:
    """Disconnect from the matrix and return the player to the Hub.

    Clears all matrix-related state (graph, current node, current mission,
    exploration tracker) and switches the screen to :class:`ScreenKind.HUB`.
    Any in-flight status message is also cleared.

    Args:
        state: Application state to mutate.
    """
    state.matrix = None
    state.current_node_id = None
    state.current_mission = None
    state.exploration = None
    state.screen = ScreenKind.HUB
    state.message = ""


def handle_matrix_input(
    event: tcod.event.Event,
    state: AppState,
    prog_registry: ProgramRegistry | None = None,
    ice_registry: IceRegistry | None = None,
) -> bool:
    """Handle input on the Matrix screen.

    If action_menu_open, delegate to action_menu.
    """
    if not isinstance(event, KeyDown):
        return True

    # If action menu is open, handle it separately
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
        # Fallback: close menu on any key
        state.action_menu_open = False
        return True

    # Normal matrix input
    if event.sym is KeySym.ESCAPE:
        state.status_messages.append(">>> Jacking out of matrix...")
        _jack_out(state)
        return True
    if event.sym is KeySym.Q:
        state.status_messages.append(">>> Quitting game...")
        return False
    if is_confirm_key(event.sym):
        # If cursor navigation has been used, confirm node selection
        matrix = state.matrix
        if matrix is not None and state.current_node_id is not None:
            neighbors = _adjacent_nodes_list(matrix, state.current_node_id)
            if neighbors and state.matrix_nav_index < len(neighbors):
                target = neighbors[state.matrix_nav_index]
                state.status_messages.append(
                    f">>> Moved to {target.label} ({_short_kind(target.kind)})"
                )
                state.current_node_id = target.id
                if state.exploration is not None:
                    state.exploration.visit(target.id)
                state.matrix_nav_index = 0  # Reset cursor
                return True
        # Otherwise open action menu (ENTER or SPACE)
        if state.matrix and state.current_node_id:
            node = state.matrix.get(state.current_node_id)
            if node:
                state.status_messages.append(f">>> Action menu opened for {node.label}")
        state.action_menu_open = True
        return True
    # LEFT/RIGHT: spatial movement (vector-based, finds neighbor in that direction)
    if event.sym in (KeySym.LEFT, KeySym.RIGHT, KeySym.KP_4, KeySym.KP_6, KeySym.H, KeySym.L):
        _handle_movement(state, event.sym)
        return True
    # UP/DOWN: cursor-based node selection
    if event.sym in _NAVIGATION_KEYS:
        _handle_cursor_navigation(state, event.sym)
        return True
    return True


__all__ = [
    "handle_matrix_input",
    "get_layout",
]
