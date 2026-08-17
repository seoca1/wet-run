"""Matrix minimap and side-panel rendering (ADR-0141 initial split).

Extracted from matrix_view.py (2026-07-27) for module-size policy
compliance (ADR-0110). Contains:
  - _draw_minimap: node visibility map in SIDE region
  - _draw_breadcrumb: path history
  - _draw_mobility_stats: movement steps and visited node count

These three functions share the SIDE region drawing concern and
are tightly coupled to ExplorationState.
"""

from __future__ import annotations

import tcod.console

from ..matrix import NodeKind
from ..matrix.exploration import ExplorationState, Visibility
from ..matrix.graph import MatrixGraph
from .layout import Region, draw_side
from .state import AppState

__all__ = [
    "_draw_breadcrumb",
    "_draw_minimap",
    "_draw_mobility_stats",
    "_short_kind",
]


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


def _short_kind(kind: NodeKind) -> str:
    """Return a short human-readable label for a NodeKind.

    Falls back to the enum value capitalized when the kind is unknown.

    Args:
        kind: Node kind to label.

    Returns:
        Short label string (e.g. "Entry", "ICE", "Construct").
    """
    return _KIND_LABEL.get(kind, kind.value.capitalize())


def _draw_minimap(
    console: tcod.console.Console,
    matrix: MatrixGraph,
    exploration: ExplorationState,
    side: Region,
) -> None:
    """Render the minimap in the SIDE region."""
    lines: list[str] = []
    for node in matrix.nodes:
        vis = exploration.visibility(matrix, node.id)
        if vis is Visibility.UNKNOWN:
            glyph, suffix = "?", ""
        elif vis is Visibility.CURRENT:
            glyph, suffix = "●", " (you)"
        elif vis is Visibility.ADJACENT:
            glyph, suffix = "○", " ?"
        else:
            glyph, suffix = "●", ""
        lines.append(f"{glyph} {_short_kind(node.kind)}{suffix}")
    draw_side(console, side, label="Map", lines=lines[: side.h - 1])


def _draw_breadcrumb(
    console: tcod.console.Console,
    matrix: MatrixGraph,
    exploration: ExplorationState,
    side: Region,
) -> None:
    """Render the breadcrumb (path) in the SIDE region, below minimap."""
    if not exploration.path:
        return
    labels: list[str] = []
    for nid in exploration.path:
        node = matrix.get(nid)
        labels.append(_short_kind(node.kind) if node is not None else "?")
    path_text = " → ".join(labels)
    console.print(
        x=side.x + 2,
        y=side.y2,
        string=f"Path: {path_text[: side.w - 10]}",
        fg=(96, 96, 96),
    )


def _draw_mobility_stats(
    console: tcod.console.Console,
    state: AppState,
    side: Region,
) -> None:
    """Render movement step count and visited-node count in the SIDE region."""
    steps = state.movement_step_count
    visited = len(state.nodes_visited)
    line = f"Steps: {steps}   Visited: {visited}"
    console.print(
        x=side.x + 2,
        y=side.y2 - 1,
        string=line[: side.w - 4],
        fg=(128, 200, 255),
    )
