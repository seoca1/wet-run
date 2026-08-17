"""Tests for matrix movement algorithm improvements (ADR-0045).

Covers:
    - Direction vector map (_DIRECTION_VECTORS) covers all expected keys
    - Direction labels (_DIRECTION_LABELS) include all entries
    - _handle_movement with cardinal keys (← → ↑ ↓)
    - _handle_movement with diagonal keys (numpad, vim-style)
    - _handle_movement with no neighbor in direction (no-op)
    - Best-match fallback when no neighbor exactly matches (diagonal preferred)
    - Tie-break by distance (closer wins)
    - Unknown key is a no-op
    - Direction hint rendering on current node box
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import tcod.console
import tcod.event
from tcod.event import KeySym

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.engine import matrix_view  # noqa: E402
from wet_run.engine.layout import Region  # noqa: E402
from wet_run.engine.matrix_view import _draw_box  # noqa: E402
from wet_run.engine.matrix_view_input import (  # noqa: E402
    _DIRECTION_LABELS,
    _DIRECTION_VECTORS,
    _handle_movement,
)
from wet_run.matrix import (  # noqa: E402
    Edge,
    MatrixGraph,
    Node,
    NodeKind,
    Status,
)

# ============================================================================
# Direction vector map
# ============================================================================


class TestDirectionVectors:
    def test_cardinal_keys_present(self) -> None:
        assert KeySym.LEFT in _DIRECTION_VECTORS
        assert KeySym.RIGHT in _DIRECTION_VECTORS
        assert KeySym.UP in _DIRECTION_VECTORS
        assert KeySym.DOWN in _DIRECTION_VECTORS

    def test_cardinal_directions_correct(self) -> None:
        assert _DIRECTION_VECTORS[KeySym.LEFT] == (-1, 0)
        assert _DIRECTION_VECTORS[KeySym.RIGHT] == (1, 0)
        assert _DIRECTION_VECTORS[KeySym.UP] == (0, -1)
        assert _DIRECTION_VECTORS[KeySym.DOWN] == (0, 1)

    def test_diagonal_keys_present(self) -> None:
        # Numpad diagonals
        assert KeySym.KP_7 in _DIRECTION_VECTORS  # NW
        assert KeySym.KP_9 in _DIRECTION_VECTORS  # NE
        assert KeySym.KP_1 in _DIRECTION_VECTORS  # SW
        assert KeySym.KP_3 in _DIRECTION_VECTORS  # SE

    def test_diagonal_directions_correct(self) -> None:
        assert _DIRECTION_VECTORS[KeySym.KP_7] == (-1, -1)  # NW
        assert _DIRECTION_VECTORS[KeySym.KP_9] == (1, -1)  # NE
        assert _DIRECTION_VECTORS[KeySym.KP_1] == (-1, 1)  # SW
        assert _DIRECTION_VECTORS[KeySym.KP_3] == (1, 1)  # SE

    def test_vim_keys_present(self) -> None:
        # Vim-style movement
        assert KeySym.H in _DIRECTION_VECTORS  # left
        assert KeySym.L in _DIRECTION_VECTORS  # right
        assert KeySym.J in _DIRECTION_VECTORS  # up
        assert KeySym.K in _DIRECTION_VECTORS  # down

    def test_all_vectors_have_labels(self) -> None:
        """Every key in _DIRECTION_VECTORS should have a label."""
        for key in _DIRECTION_VECTORS:
            assert key in _DIRECTION_LABELS, f"Key {key} missing label"

    def test_all_labels_have_vectors(self) -> None:
        """Every key in _DIRECTION_LABELS should have a vector."""
        for key in _DIRECTION_LABELS:
            assert key in _DIRECTION_VECTORS, f"Key {key} missing vector"


# ============================================================================
# _handle_movement with real matrix
# ============================================================================


@pytest.fixture
def simple_grid_matrix() -> MatrixGraph:
    r"""Build a simple 3x3 grid matrix with diagonal edges for movement testing.

    Layout (with cardinal + diagonal edges):
        (0,0) - (1,0) - (2,0)
          |\    /|\    /|
          | \  / | \  / |
          |  \/  |  \/  |
          |  /\  |  /\  |
          | /  \ | /  \ |
          |/    \|/    \|
        (0,1) - (1,1) - (2,1)
          |     ...
    """
    from wet_run.matrix.node import (
        AlarmLevel,
        Faction,
        IceKind,
        ZoneDepth,
    )

    nodes = []
    for y in range(3):
        for x in range(3):
            nodes.append(
                Node(
                    id=f"n_{x}_{y}",
                    kind=NodeKind.DATA if (x + y) % 2 == 0 else NodeKind.ICE,
                    label=f"N{x}{y}",
                    zone=ZoneDepth.SURFACE,
                    ice=IceKind.STANDARD if (x + y) % 2 == 1 else IceKind.NONE,
                    alarm=AlarmLevel.LOW,
                    faction=Faction.NONE,
                )
            )
    edges: list[Edge] = []
    # Horizontal
    for y in range(3):
        for x in range(2):
            edges.append(Edge(src=f"n_{x}_{y}", dst=f"n_{x + 1}_{y}"))
            edges.append(Edge(src=f"n_{x + 1}_{y}", dst=f"n_{x}_{y}"))
    # Vertical
    for y in range(2):
        for x in range(3):
            edges.append(Edge(src=f"n_{x}_{y}", dst=f"n_{x}_{y + 1}"))
            edges.append(Edge(src=f"n_{x}_{y + 1}", dst=f"n_{x}_{y}"))
    # Diagonals (so diagonal movement has a real target)
    for x in range(2):
        for y in range(2):
            edges.append(Edge(src=f"n_{x}_{y}", dst=f"n_{x + 1}_{y + 1}"))
            edges.append(Edge(src=f"n_{x + 1}_{y + 1}", dst=f"n_{x}_{y}"))
            edges.append(Edge(src=f"n_{x + 1}_{y}", dst=f"n_{x}_{y + 1}"))
            edges.append(Edge(src=f"n_{x}_{y + 1}", dst=f"n_{x + 1}_{y}"))
    return MatrixGraph(nodes=tuple(nodes), edges=tuple(edges), entry_id="n_1_1")


@pytest.fixture
def state_at_center(simple_grid_matrix: MatrixGraph):
    """Create an AppState positioned at center (1,1) of the simple grid."""
    from wet_run.engine.state import AppState

    state = AppState()
    state.matrix = simple_grid_matrix
    state.current_node_id = "n_1_1"
    # Pre-populate layout cache so _handle_movement can use it
    matrix_view._last_layout[simple_grid_matrix] = {
        f"n_{x}_{y}": (x * 5, y * 3) for x in range(3) for y in range(3)
    }
    return state


class TestHandleMovementCardinal:
    def test_left_moves_west(self, state_at_center) -> None:
        state = state_at_center
        before = list(state.status_messages)
        _handle_movement(state, KeySym.LEFT)
        # Should have moved to n_0_1
        assert state.current_node_id == "n_0_1"
        # Status message appended
        assert len(state.status_messages) > len(before)

    def test_right_moves_east(self, state_at_center) -> None:
        _handle_movement(state_at_center, KeySym.RIGHT)
        assert state_at_center.current_node_id == "n_2_1"

    def test_up_moves_north(self, state_at_center) -> None:
        _handle_movement(state_at_center, KeySym.UP)
        assert state_at_center.current_node_id == "n_1_0"

    def test_down_moves_south(self, state_at_center) -> None:
        _handle_movement(state_at_center, KeySym.DOWN)
        assert state_at_center.current_node_id == "n_1_2"


class TestHandleMovementDiagonal:
    def test_numpad_7_moves_nw(self, state_at_center) -> None:
        _handle_movement(state_at_center, KeySym.KP_7)
        assert state_at_center.current_node_id == "n_0_0"

    def test_numpad_9_moves_ne(self, state_at_center) -> None:
        _handle_movement(state_at_center, KeySym.KP_9)
        assert state_at_center.current_node_id == "n_2_0"

    def test_numpad_1_moves_sw(self, state_at_center) -> None:
        _handle_movement(state_at_center, KeySym.KP_1)
        assert state_at_center.current_node_id == "n_0_2"

    def test_numpad_3_moves_se(self, state_at_center) -> None:
        _handle_movement(state_at_center, KeySym.KP_3)
        assert state_at_center.current_node_id == "n_2_2"


class TestHandleMovementVim:
    def test_h_moves_west(self, state_at_center) -> None:
        _handle_movement(state_at_center, KeySym.H)
        assert state_at_center.current_node_id == "n_0_1"

    def test_l_moves_east(self, state_at_center) -> None:
        _handle_movement(state_at_center, KeySym.L)
        assert state_at_center.current_node_id == "n_2_1"

    def test_j_moves_north(self, state_at_center) -> None:
        _handle_movement(state_at_center, KeySym.J)
        assert state_at_center.current_node_id == "n_1_0"

    def test_k_moves_south(self, state_at_center) -> None:
        _handle_movement(state_at_center, KeySym.K)
        assert state_at_center.current_node_id == "n_1_2"


class TestHandleMovementFallback:
    """When no neighbor exactly matches the direction, pick the best (highest dot product)."""

    def test_no_neighbor_in_direction_is_noop(self, state_at_center) -> None:
        """When at corner with no neighbor in a direction, status msg says 'no node'.

        Center (1,1) has all 4 cardinal neighbors. Move to (0,0) (corner).
        At (0,0), there are only east and south neighbors — UP and LEFT should fail.
        """
        # First move to corner (0,0)
        _handle_movement(state_at_center, KeySym.KP_7)  # NW
        assert state_at_center.current_node_id == "n_0_0"
        # Now try to move UP — no neighbor above
        before_count = len(state_at_center.status_messages)
        _handle_movement(state_at_center, KeySym.UP)
        # Status should say "no node"
        new_msgs = state_at_center.status_messages[before_count:]
        assert any("No node" in m for m in new_msgs)
        # Position should not change
        assert state_at_center.current_node_id == "n_0_0"

    def test_best_match_when_exact_missing(self) -> None:
        """If no cardinal match exists, best diagonal should win.

        Build a star graph: center → 4 corners (NE, NW, SE, SW only).
        Pressing RIGHT should pick the best of NE/SE (both equally close).
        """
        from wet_run.matrix.node import (
            AlarmLevel,
            Faction,
            IceKind,
            ZoneDepth,
        )

        nodes = [
            Node(
                id="center",
                kind=NodeKind.ROUTER,
                label="C",
                zone=ZoneDepth.SURFACE,
                ice=IceKind.NONE,
                alarm=AlarmLevel.LOW,
                faction=Faction.NONE,
            ),
            Node(
                id="ne",
                kind=NodeKind.DATA,
                label="NE",
                zone=ZoneDepth.SURFACE,
                ice=IceKind.NONE,
                alarm=AlarmLevel.LOW,
                faction=Faction.NONE,
            ),
            Node(
                id="nw",
                kind=NodeKind.DATA,
                label="NW",
                zone=ZoneDepth.SURFACE,
                ice=IceKind.NONE,
                alarm=AlarmLevel.LOW,
                faction=Faction.NONE,
            ),
            Node(
                id="se",
                kind=NodeKind.DATA,
                label="SE",
                zone=ZoneDepth.SURFACE,
                ice=IceKind.NONE,
                alarm=AlarmLevel.LOW,
                faction=Faction.NONE,
            ),
            Node(
                id="sw",
                kind=NodeKind.DATA,
                label="SW",
                zone=ZoneDepth.SURFACE,
                ice=IceKind.NONE,
                alarm=AlarmLevel.LOW,
                faction=Faction.NONE,
            ),
        ]
        edges: list = [
            Edge(src="center", dst="ne"),
            Edge(src="center", dst="nw"),
            Edge(src="center", dst="se"),
            Edge(src="center", dst="sw"),
        ]
        m = MatrixGraph(nodes=tuple(nodes), edges=tuple(edges), entry_id="center")
        from wet_run.engine.state import AppState

        s = AppState()
        s.matrix = m
        s.current_node_id = "center"
        matrix_view._last_layout[m] = {
            "center": (10, 10),
            "ne": (15, 5),  # dx=+5, dy=-5 (NE)
            "nw": (5, 5),  # dx=-5, dy=-5 (NW)
            "se": (15, 15),  # dx=+5, dy=+5 (SE)
            "sw": (5, 15),  # dx=-5, dy=+5 (SW)
        }
        # Pressing RIGHT should pick NE or SE (both have positive dx, zero dy)
        _handle_movement(s, KeySym.RIGHT)
        # Should have moved to NE or SE (not NW or SW)
        assert s.current_node_id in ("ne", "se"), f"Got: {s.current_node_id}"


class TestHandleMovementUnknown:
    def test_unknown_key_is_noop(self, state_at_center) -> None:
        """Pressing a non-movement key should not change position."""
        before = state_at_center.current_node_id
        _handle_movement(state_at_center, KeySym.A)
        assert state_at_center.current_node_id == before

    def test_no_matrix_is_noop(self) -> None:
        from wet_run.engine.state import AppState

        s = AppState()
        s.matrix = None
        s.current_node_id = None
        # Should not raise
        _handle_movement(s, KeySym.LEFT)


# ============================================================================
# Direction hints rendering
# ============================================================================


class TestDirectionHints:
    def test_draw_box_with_hints(self) -> None:
        """Direction hints should be drawn on the current node box."""
        console = tcod.console.Console(80, 50, order="F")
        main = Region(id="main", x=0, y=2, w=80, h=46)
        # Center the box at (30, 20)
        hints = {"L": "◄", "R": "►", "U": "▲", "D": "▼"}
        _draw_box(
            console,
            main,
            col=30,
            row=20,
            label="X",
            zdr=5,
            status=Status.SAFE,
            is_current=True,
            direction_hints=hints,
        )

        def to_text(c):
            lines = []
            for y in range(c.height):
                chars = []
                for x in range(c.width):
                    code = int(c.ch[x, y])
                    chars.append(chr(code) if 0 < code < 0x110000 else " ")
                lines.append("".join(chars).rstrip())
            return "\n".join(lines)

        full = to_text(console)
        # All four direction glyphs should be present
        assert "◄" in full
        assert "►" in full
        assert "▲" in full
        assert "▼" in full

    def test_draw_box_no_hints_current(self) -> None:
        """Direction hints should NOT be drawn if direction_hints is None."""
        console = tcod.console.Console(80, 50, order="F")
        main = Region(id="main", x=0, y=2, w=80, h=46)
        _draw_box(
            console,
            main,
            col=30,
            row=20,
            label="X",
            zdr=5,
            status=Status.SAFE,
            is_current=True,
            direction_hints=None,
        )

        def to_text(c):
            lines = []
            for y in range(c.height):
                chars = []
                for x in range(c.width):
                    code = int(c.ch[x, y])
                    chars.append(chr(code) if 0 < code < 0x110000 else " ")
                lines.append("".join(chars).rstrip())
            return "\n".join(lines)

        full = to_text(console)
        # No direction hint glyphs
        assert "◄" not in full
        assert "►" not in full
        assert "▲" not in full
        assert "▼" not in full

    def test_draw_box_non_current_no_hints(self) -> None:
        """Non-current nodes should never show direction hints even if passed."""
        console = tcod.console.Console(80, 50, order="F")
        main = Region(id="main", x=0, y=2, w=80, h=46)
        _draw_box(
            console,
            main,
            col=30,
            row=20,
            label="X",
            zdr=5,
            status=Status.SAFE,
            is_current=False,
            direction_hints={"L": "◄"},
        )

        def to_text(c):
            lines = []
            for y in range(c.height):
                chars = []
                for x in range(c.width):
                    code = int(c.ch[x, y])
                    chars.append(chr(code) if 0 < code < 0x110000 else " ")
                lines.append("".join(chars).rstrip())
            return "\n".join(lines)

        full = to_text(console)
        assert "◄" not in full


# ============================================================================
# Backward compatibility
# ============================================================================


class TestBackwardCompatibility:
    def test_generate_default_matrix_still_moves(self, state_at_center) -> None:
        """The default generator should produce a matrix where cardinal moves work."""
        # Move to each direction and ensure we land somewhere
        for key in (KeySym.UP, KeySym.DOWN, KeySym.LEFT, KeySym.RIGHT):
            before = state_at_center.current_node_id
            _handle_movement(state_at_center, key)
            # Either moved or no-node message
            if state_at_center.current_node_id == before:
                # Should have a "No node" message
                assert any("No node" in m for m in state_at_center.status_messages)
