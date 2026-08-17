"""Tests for MatrixGraph and compute_layout (ADR-0005)."""

from __future__ import annotations

import pytest

from wet_run.matrix.graph import Edge, MatrixGraph, compute_layout
from wet_run.matrix.node import (
    IceKind,
    Node,
    NodeKind,
    ZoneDepth,
)


def _entry() -> Node:
    return Node(
        id="E_0",
        kind=NodeKind.ENTRY,
        label="Entry",
        zone=ZoneDepth.SURFACE,
    )


def _router(rid: str) -> Node:
    return Node(
        id=rid,
        kind=NodeKind.ROUTER,
        label="Router",
        zone=ZoneDepth.SURFACE,
    )


def _data(did: str) -> Node:
    return Node(
        id=did,
        kind=NodeKind.DATA,
        label="Data",
        zone=ZoneDepth.SURFACE,
    )


def _ice() -> Node:
    return Node(
        id="I_0",
        kind=NodeKind.ICE,
        label="ICE",
        zone=ZoneDepth.SURFACE,
        ice=IceKind.STANDARD,
    )


def _exit() -> Node:
    return Node(
        id="X_0",
        kind=NodeKind.EXIT,
        label="Exit",
        zone=ZoneDepth.SURFACE,
    )


def _small_graph() -> MatrixGraph:
    nodes = (_entry(), _router("R_0"), _data("D_0"), _ice(), _exit())
    edges = (
        Edge("E_0", "R_0"),
        Edge("R_0", "D_0"),
        Edge("R_0", "I_0"),
        Edge("D_0", "X_0"),
        Edge("I_0", "X_0"),
    )
    return MatrixGraph(nodes=nodes, edges=edges, entry_id="E_0")


def test_graph_creation() -> None:
    g = _small_graph()
    assert len(g) == 5
    assert g.entry_id == "E_0"
    assert "E_0" in g
    assert "missing" not in g


def test_graph_get() -> None:
    g = _small_graph()
    n = g.get("R_0")
    assert n is not None
    assert n.kind is NodeKind.ROUTER
    assert g.get("missing") is None


def test_graph_neighbors() -> None:
    g = _small_graph()
    nbrs = g.neighbors("E_0")
    assert {n.id for n in nbrs} == {"R_0"}
    nbrs_r0 = g.neighbors("R_0")
    assert {n.id for n in nbrs_r0} == {"D_0", "I_0"}


def test_graph_is_connected() -> None:
    g = _small_graph()
    assert g.is_connected("E_0", "R_0")
    assert g.is_connected("R_0", "D_0")
    assert not g.is_connected("E_0", "D_0")


def test_graph_exits() -> None:
    g = _small_graph()
    exits = g.exits()
    assert len(exits) == 1
    assert exits[0].id == "X_0"


def test_graph_duplicate_ids_rejected() -> None:
    nodes = (_entry(), _entry())
    with pytest.raises(ValueError, match="duplicate"):
        MatrixGraph(nodes=nodes, edges=(), entry_id="E_0")


def test_graph_entry_must_be_in_nodes() -> None:
    with pytest.raises(ValueError, match="entry_id"):
        MatrixGraph(nodes=(_entry(),), edges=(), entry_id="missing")


def test_graph_edge_unknown_node_rejected() -> None:
    with pytest.raises(ValueError, match="src"):
        MatrixGraph(
            nodes=(_entry(),),
            edges=(Edge("missing", "E_0"),),
            entry_id="E_0",
        )


def test_edge_self_loop_rejected() -> None:
    with pytest.raises(ValueError, match="self-loop"):
        Edge("E_0", "E_0")


def test_edge_empty_endpoints_rejected() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        Edge("", "X_0")


# --- compute_layout ---


def test_compute_layout_basic() -> None:
    g = _small_graph()
    pos = compute_layout(g)
    assert set(pos.keys()) == {"E_0", "R_0", "D_0", "I_0", "X_0"}
    # Entry at layer 0 → col 2
    assert pos["E_0"][0] == 2
    # R_0 at layer 1 → col 2 + 18 = 20
    assert pos["R_0"][0] == 20
    # D_0, I_0 at layer 2 → col 38
    assert pos["D_0"][0] == 38
    assert pos["I_0"][0] == 38
    # X_0 at layer 3 → col 56
    assert pos["X_0"][0] == 56


def test_compute_layout_deterministic() -> None:
    g = _small_graph()
    pos1 = compute_layout(g)
    pos2 = compute_layout(g)
    assert pos1 == pos2


def test_compute_layout_in_screen_bounds() -> None:
    g = _small_graph()
    pos = compute_layout(g, col_step=18, row_step=8, origin_x=2, origin_y=12)
    for _nid, (col, row) in pos.items():
        # Box width 12 → col+11 must be < 80 (screen width)
        assert 0 <= col < 80
        assert 0 <= row < 50


def test_compute_layout_empty_graph() -> None:
    g = MatrixGraph(nodes=(), edges=(), entry_id="")
    assert compute_layout(g) == {}
