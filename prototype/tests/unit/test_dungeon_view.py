"""Tests for dungeon view rendering (ADR-0060 Phase 1 — dungeon-only mode).

Covers:
    - render_dungeon_matrix generates glyphs without errors
    - 4-directional movement inside dungeon
"""

from __future__ import annotations

import sys
from pathlib import Path

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.combat.registry import IceRegistry, ProgramRegistry  # noqa: E402
from wet_run.engine import dungeon_view  # noqa: E402
from wet_run.engine.app import AppState, ScreenKind  # noqa: E402
from wet_run.matrix import (  # noqa: E402
    Edge,
    IceKind,
    MatrixGraph,
    Node,
    NodeKind,
    ZoneDepth,
)
from wet_run.matrix.exploration import ExplorationState

# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------


def _make_branch_graph() -> MatrixGraph:
    """Build a branching graph: entry -> router (+ice / +data) -> exit."""
    nodes = (
        Node(id="entry", label="Jack-in", kind=NodeKind.ENTRY, zone=ZoneDepth.SURFACE),
        Node(id="router", label="Router", kind=NodeKind.ROUTER, zone=ZoneDepth.SURFACE),
        Node(id="ice", label="ICE", kind=NodeKind.ICE, zone=ZoneDepth.MID, ice=IceKind.STANDARD),
        Node(id="data", label="Data", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE),
        Node(id="exit", label="Exit", kind=NodeKind.EXIT, zone=ZoneDepth.CORE),
    )
    edges = (
        Edge(src="entry", dst="router"),
        Edge(src="router", dst="ice"),
        Edge(src="router", dst="data"),
        Edge(src="ice", dst="exit"),
        Edge(src="data", dst="exit"),
    )
    return MatrixGraph(nodes=nodes, edges=edges, entry_id="entry")


def _state_with_branch() -> AppState:
    s = AppState()
    s.matrix = _make_branch_graph()
    s.current_node_id = "entry"
    s.exploration = ExplorationState(current="entry")
    s.screen = ScreenKind.MATRIX
    return s


def _make_graph() -> MatrixGraph:
    """Build a 4-node graph: entry -> data -> ice -> exit."""
    nodes = (
        Node(
            id="entry",
            label="Jack-in Point",
            kind=NodeKind.ENTRY,
            zone=ZoneDepth.SURFACE,
        ),
        Node(
            id="data",
            label="Data Vault",
            kind=NodeKind.DATA,
            zone=ZoneDepth.SURFACE,
        ),
        Node(
            id="ice",
            label="Hostile ICE",
            kind=NodeKind.ICE,
            zone=ZoneDepth.MID,
            ice=IceKind.STANDARD,
        ),
        Node(
            id="exit",
            label="Extraction Gate",
            kind=NodeKind.EXIT,
            zone=ZoneDepth.CORE,
        ),
    )
    edges = (
        Edge(src="entry", dst="data"),
        Edge(src="data", dst="ice"),
        Edge(src="ice", dst="exit"),
    )
    g = MatrixGraph(nodes=nodes, edges=edges, entry_id="entry")
    return g


def _key_event(sym: KeySym, shift: bool = False) -> KeyDown:
    """Create a synthetic KeyDown event (no console needed)."""
    return KeyDown(
        sym=sym,
        mod=tcod.event.Modifier.SHIFT if shift else tcod.event.Modifier(0),
        scancode=int(sym),
    )


def _state_with_graph() -> AppState:
    s = AppState()
    s.matrix = _make_graph()
    s.current_node_id = "entry"
    s.exploration = None  # not exercising fog
    s.screen = ScreenKind.MATRIX
    return s


def _prog_registry() -> ProgramRegistry:
    # Empty registry — load() raises FileNotFoundError if file missing,
    # but passing None is acceptable for these tests.
    return None  # type: ignore[return-value]


def _ice_registry() -> IceRegistry:
    return None  # type: ignore[return-value]


# ============================================================================
# Cardinal direction movement in dungeon mode
# ============================================================================


class TestCardinalMovementDungeon:
    def test_handle_dungeon_input_right_moves_to_neighbor(self) -> None:
        s = _state_with_graph()
        dungeon_view._handle_cardinal_movement(s, KeySym.RIGHT, None, None)
        assert s.current_node_id in {"entry", "data", "ice", "exit"}

    def test_handle_dungeon_input_invalid_direction_no_op(self) -> None:
        s = _state_with_graph()
        dungeon_view._handle_cardinal_movement(s, KeySym.UP, None, None)
        assert s.current_node_id in {"entry", "data", "ice", "exit"}

    def test_backtrack_pageup_key_returns_to_previous_room(self) -> None:
        s = _state_with_branch()
        dungeon_view._handle_cardinal_movement(s, KeySym.RIGHT, None, None)
        assert s.current_node_id == "router"
        dungeon_view._handle_backtrack(s, None, None)
        assert s.current_node_id == "entry"

    def test_backtrack_via_reverse_direction_key(self) -> None:
        s = _state_with_branch()
        dungeon_view._handle_cardinal_movement(s, KeySym.RIGHT, None, None)
        assert s.current_node_id == "router"
        dungeon_view._handle_cardinal_movement(s, KeySym.RIGHT, None, None)
        assert s.current_node_id == "ice"
        dungeon_view._handle_cardinal_movement(s, KeySym.LEFT, None, None)
        assert s.current_node_id == "router"

    def test_forward_branches_via_dot_product_alignment(self) -> None:
        s = _state_with_branch()
        dungeon_view._handle_cardinal_movement(s, KeySym.RIGHT, None, None)
        assert s.current_node_id == "router"
        dungeon_view._handle_cardinal_movement(s, KeySym.UP, None, None)
        assert s.current_node_id == "data"
        dungeon_view._handle_cardinal_movement(s, KeySym.RIGHT, None, None)
        assert s.current_node_id == "exit"

    def test_trap_damage_on_high_alarm_node_entry(self) -> None:
        from wet_run.matrix.node import AlarmLevel

        nodes = (
            Node(id="e", label="Entry", kind=NodeKind.ENTRY, zone=ZoneDepth.SURFACE),
            Node(
                id="h",
                label="HighAlarm",
                kind=NodeKind.ROUTER,
                zone=ZoneDepth.MID,
                alarm=AlarmLevel.HIGH,
            ),
        )
        edges = (Edge(src="e", dst="h"),)
        g = MatrixGraph(nodes=nodes, edges=edges, entry_id="e")
        s = AppState()
        s.matrix = g
        s.current_node_id = "e"
        s.player_hp = 100
        s.exploration = ExplorationState(current="e")
        s.screen = ScreenKind.MATRIX
        dungeon_view._handle_cardinal_movement(s, KeySym.RIGHT, None, None)
        assert s.current_node_id == "h"
        assert s.player_hp == 85
        assert any("TRAP" in m for m in s.status_messages)


# ============================================================================
# Smoke render (does not assert content; just verifies it draws without error)
# ============================================================================


class TestDungeonRenderSmoke:
    def test_render_dungeon_matrix_does_not_raise(self) -> None:
        s = _state_with_graph()
        console = tcod.console.Console(80, 50, order="F")
        dungeon_view.render_dungeon_matrix(console, None, s)  # type: ignore[arg-type]
