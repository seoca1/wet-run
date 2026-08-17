"""State-mutating tests for _defeat_current_ice_node (combat_view.py).

Tests all branches:
- Early-return when matrix or current_node_id is None
- Mark defeated node in state.defeated_nodes
- Append destroyed status message
- Remove node from matrix graph
- Update current_node_id to neighbor (or entry_id fallback)
"""

from __future__ import annotations

from wet_run.engine.combat_view import (  # type: ignore[import-untyped]
    _defeat_current_ice_node,
)
from wet_run.engine.state import AppState  # type: ignore[import-untyped]
from wet_run.matrix.graph import Edge, MatrixGraph  # type: ignore[import-untyped]
from wet_run.matrix.node import Node, NodeKind, ZoneDepth  # type: ignore[import-untyped]


def _make_node(id: str, kind: NodeKind = NodeKind.DATA) -> Node:
    return Node(
        id=id,
        kind=kind,
        label=id,
        zone=ZoneDepth.MID,
    )


def _make_state_with_matrix(
    nodes: list[Node],
    edges: list[tuple[str, str]] | tuple[tuple[str, str], ...],
    entry_id: str,
    current_id: str,
) -> AppState:
    """Construct an AppState with a populated matrix graph."""
    state = AppState()
    state.matrix = MatrixGraph(
        nodes=tuple(nodes),
        edges=tuple(Edge(src=s, dst=d) for s, d in edges),
        entry_id=entry_id,
    )
    state.current_node_id = current_id
    return state


class TestDefeatCurrentIceNodeEarlyReturns:
    """_defeat_current_ice_node — early-return branches (no mutation)."""

    def test_early_return_when_matrix_is_none(self) -> None:
        """state.matrix is None → return silently, no mutation."""
        state = AppState()
        state.current_node_id = "data_1"
        # Ensure defeated_nodes is empty
        state.defeated_nodes.clear()
        initial_status_count = len(state.status_messages)
        _defeat_current_ice_node(state)
        assert len(state.defeated_nodes) == 0
        assert len(state.status_messages) == initial_status_count
        assert state.current_node_id == "data_1"  # Unchanged

    def test_early_return_when_current_node_id_is_none(self) -> None:
        """state.current_node_id is None → return silently, no mutation."""
        state = AppState()
        nodes = [_make_node("data_1"), _make_node("data_2")]
        state.matrix = MatrixGraph(
            nodes=tuple(nodes),
            edges=(),
            entry_id="data_1",
        )
        # current_node_id defaults to empty string; set to None for explicit test
        state.current_node_id = None
        state.defeated_nodes.clear()
        initial_status_count = len(state.status_messages)
        _defeat_current_ice_node(state)
        assert len(state.defeated_nodes) == 0
        assert len(state.status_messages) == initial_status_count


class TestDefeatCurrentIceNodeMain:
    """_defeat_current_ice_node — main behavior (state mutation)."""

    def test_marks_node_as_defeated_in_defeated_nodes_set(self) -> None:
        """Defeated node_id added to state.defeated_nodes."""
        nodes = [_make_node("entry"), _make_node("data_1"), _make_node("data_2")]
        state = _make_state_with_matrix(
            nodes=nodes,
            edges=[("entry", "data_1"), ("entry", "data_2")],
            entry_id="entry",
            current_id="data_1",
        )
        state.defeated_nodes.clear()
        _defeat_current_ice_node(state)
        assert "data_1" in state.defeated_nodes

    def test_appends_destroyed_status_message(self) -> None:
        """Status message added with format '>>> ICE [{id}] destroyed'."""
        nodes = [_make_node("entry"), _make_node("data_1")]
        state = _make_state_with_matrix(
            nodes=nodes,
            edges=[("entry", "data_1")],
            entry_id="entry",
            current_id="data_1",
        )
        state.status_messages.clear()
        _defeat_current_ice_node(state)
        assert any("data_1" in m and "destroyed" in m for m in state.status_messages)

    def test_removes_node_from_matrix_graph(self) -> None:
        """Defeated node removed from state.matrix.nodes."""
        nodes = [_make_node("entry"), _make_node("data_1"), _make_node("data_2")]
        state = _make_state_with_matrix(
            nodes=nodes,
            edges=[("entry", "data_1"), ("entry", "data_2")],
            entry_id="entry",
            current_id="data_1",
        )
        _defeat_current_ice_node(state)
        assert state.matrix is not None
        assert "data_1" not in {n.id for n in state.matrix.nodes}
        # Edges involving data_1 should also be removed
        edge_pairs = {(e.src, e.dst) for e in state.matrix.edges}
        assert ("entry", "data_1") not in edge_pairs

    def test_updates_current_node_id_to_neighbor(self) -> None:
        """After defeat, current_node_id updated to first neighbor (entry)."""
        nodes = [_make_node("entry"), _make_node("data_1")]
        state = _make_state_with_matrix(
            nodes=nodes,
            edges=[("entry", "data_1")],
            entry_id="entry",
            current_id="data_1",
        )
        _defeat_current_ice_node(state)
        # After removing data_1, the only node left is 'entry', which is also current_node_id
        # The function sets current_node_id to neighbors[0] if available, else entry_id
        assert state.current_node_id == "entry"

    def test_falls_back_to_entry_id_when_no_neighbors(self) -> None:
        """When node has no neighbors AND is not in graph → fall back to entry_id."""
        # Use 2 disconnected nodes
        nodes = [_make_node("entry"), _make_node("isolated")]
        state = _make_state_with_matrix(
            nodes=nodes,
            edges=(),  # No edges
            entry_id="entry",
            current_id="isolated",
        )
        # isolated has no neighbors, but it's in the graph
        # neighbors('isolated') → empty list → falls back to entry_id
        _defeat_current_ice_node(state)
        # The function checks if defeated_id is still in the graph nodes after removal
        # 'isolated' is removed, so it won't be in nodes
        # The condition: if defeated_id in [n.id for n in state.matrix.nodes]: use neighbors, else []
        # Since 'isolated' is NOT in remaining nodes (just 'entry'), neighbors = []
        # Then current_node_id = state.matrix.entry_id = 'entry'
        assert state.current_node_id == "entry"

    def test_removes_node_and_updates_to_entry_fallback(self) -> None:
        """When current_node_id not in graph post-removal, fall back to entry_id."""
        nodes = [_make_node("entry"), _make_node("middle"), _make_node("leaf")]
        state = _make_state_with_matrix(
            nodes=nodes,
            edges=[("entry", "middle"), ("middle", "leaf")],
            entry_id="entry",
            current_id="leaf",  # leaf has neighbors (middle) but we defeat it
        )
        _defeat_current_ice_node(state)
        # 'leaf' defeated. After removal, graph has [entry, middle].
        # leaf has neighbors [middle] before removal, but after removal leaf is gone.
        # Condition: leaf in remaining nodes? No → neighbors = [] → fall back to entry_id
        # Wait — the code checks `defeated_id in [n.id for n in state.matrix.nodes]`
        # After _remove_node_from_graph, 'leaf' is removed → not in nodes → neighbors = []
        # Then: current_node_id = state.matrix.entry_id = 'entry'
        assert state.current_node_id == "entry"
