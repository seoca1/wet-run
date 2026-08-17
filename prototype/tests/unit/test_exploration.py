"""Tests for the Exploration state (ADR-0020)."""

from __future__ import annotations

import pytest

from wet_run.matrix import ExplorationState, MatrixGenerator, Visibility
from wet_run.matrix.exploration import is_always_visible_kind
from wet_run.matrix.graph import MatrixGraph
from wet_run.matrix.node import NodeKind


@pytest.fixture
def small_graph() -> MatrixGraph:
    gen = MatrixGenerator()
    g = gen.generate(seed=42, mission_grade=1)
    return g


def test_initial_state_marks_entry_as_discovered(small_graph) -> None:
    entry_id = small_graph.entry_id
    expl = ExplorationState(current=entry_id)
    assert expl.current == entry_id
    assert entry_id in expl.discovered
    assert expl.path == [entry_id]
    assert expl.scanned == set()


def test_visit_marks_node_and_extends_path(small_graph) -> None:
    entry_id = small_graph.entry_id
    nbrs = small_graph.neighbors(entry_id)
    assert nbrs, "test graph must have at least one neighbor"
    target = nbrs[0].id

    expl = ExplorationState(current=entry_id)
    expl.visit(target)

    assert expl.current == target
    assert target in expl.discovered
    assert expl.path == [entry_id, target]


def test_visit_does_not_duplicate_path(small_graph) -> None:
    entry_id = small_graph.entry_id
    expl = ExplorationState(current=entry_id)
    expl.visit(entry_id)
    assert expl.path == [entry_id]


def test_visibility_current(small_graph) -> None:
    entry_id = small_graph.entry_id
    expl = ExplorationState(current=entry_id)
    assert expl.visibility(small_graph, entry_id) is Visibility.CURRENT


def test_visibility_discovered(small_graph) -> None:
    entry_id = small_graph.entry_id
    # Find a path of length >= 2 from entry (any two nodes reachable from entry).
    path = _find_path(small_graph, entry_id, depth=2)
    if path is None:
        pytest.skip("graph has no path of depth 2 from entry")
    target = path[1]
    expl = ExplorationState(current=entry_id)
    expl.visit(target)
    assert expl.visibility(small_graph, target) is Visibility.CURRENT
    # Move further to make target become "discovered".
    next_nbrs = small_graph.neighbors(target)
    nxt = next((n.id for n in next_nbrs if n.id != entry_id), None)
    if nxt is None:
        # target is a dead-end; it's still CURRENT but we can't go further.
        # Skip the discovered assertion in this case.
        pytest.skip("target is a dead-end; cannot advance to test DISCOVERED")
    expl.visit(nxt)
    assert expl.visibility(small_graph, target) is Visibility.DISCOVERED


def test_visibility_adjacent(small_graph) -> None:
    """After moving to a third node, the original neighbor is no longer adjacent."""
    entry_id = small_graph.entry_id
    path = _find_path(small_graph, entry_id, depth=2)
    if path is None:
        pytest.skip("graph has no path of depth 2 from entry")
    expl = ExplorationState(current=entry_id)
    expl.visit(path[1])
    expl.visit(path[2])
    # path[1] is now discovered (visited before); verify it's not CURRENT
    assert expl.visibility(small_graph, path[1]) is not Visibility.CURRENT


def test_visibility_unknown(small_graph) -> None:
    entry_id = small_graph.entry_id
    expl = ExplorationState(current=entry_id)
    # Find a node that is NOT adjacent to the entry
    adj_ids = {n.id for n in small_graph.neighbors(entry_id)}
    adj_ids.add(entry_id)
    for node in small_graph.nodes:
        if node.id not in adj_ids:
            assert expl.visibility(small_graph, node.id) is Visibility.UNKNOWN
            return
    pytest.skip("all nodes are adjacent to entry")


def test_probe_marks_node_as_scanned(small_graph) -> None:
    entry_id = small_graph.entry_id
    nbrs = small_graph.neighbors(entry_id)
    target = nbrs[0].id
    expl = ExplorationState(current=entry_id)
    expl.probe(target)
    assert target in expl.scanned
    assert expl.is_scanned(target)


def test_is_visible_true_for_adjacent_and_discovered(small_graph) -> None:
    entry_id = small_graph.entry_id
    nbrs = small_graph.neighbors(entry_id)
    target = nbrs[0].id
    expl = ExplorationState(current=entry_id)
    assert expl.is_visible(small_graph, target) is True
    assert expl.is_visible(small_graph, entry_id) is True


def test_is_visible_false_for_unknown(small_graph) -> None:
    entry_id = small_graph.entry_id
    expl = ExplorationState(current=entry_id)
    adj_ids = {n.id for n in small_graph.neighbors(entry_id)}
    adj_ids.add(entry_id)
    for node in small_graph.nodes:
        if node.id not in adj_ids:
            assert expl.is_visible(small_graph, node.id) is False
            return
    pytest.skip("all nodes are adjacent to entry")


def test_adjacent_to_current(small_graph) -> None:
    entry_id = small_graph.entry_id
    expl = ExplorationState(current=entry_id)
    adj = expl.adjacent_to_current(small_graph)
    assert set(adj) == {n.id for n in small_graph.neighbors(entry_id)}


def test_discoverable_now(small_graph) -> None:
    entry_id = small_graph.entry_id
    expl = ExplorationState(current=entry_id)
    avail = expl.discoverable_now(small_graph)
    assert entry_id not in avail
    for n in small_graph.neighbors(entry_id):
        assert n.id in avail


def test_path_tracks_movements(small_graph) -> None:
    entry_id = small_graph.entry_id
    path = _find_path(small_graph, entry_id, depth=2)
    if path is None:
        pytest.skip("graph has no path of depth 2 from entry")
    expl = ExplorationState(current=entry_id)
    expl.visit(path[1])
    assert expl.path == [entry_id, path[1]]
    if len(path) >= 3:
        expl.visit(path[2])
        assert expl.path == [entry_id, path[1], path[2]]


def _find_path(small_graph, start: str, *, depth: int) -> list[str] | None:
    """BFS to find any path of given depth from start. Returns None if no such path."""
    if depth < 1:
        return [start]
    visited = {start}
    queue: list[list[str]] = [[start]]
    while queue:
        path = queue.pop(0)
        if len(path) == depth + 1:
            return path
        for n in small_graph.neighbors(path[-1]):
            if n.id not in visited:
                visited.add(n.id)
                queue.append(path + [n.id])
    return None


def test_is_always_visible_kind() -> None:
    assert is_always_visible_kind(NodeKind.ENTRY)
    assert is_always_visible_kind(NodeKind.EXIT)
    assert not is_always_visible_kind(NodeKind.DATA)
    assert not is_always_visible_kind(NodeKind.ICE)
    assert not is_always_visible_kind(NodeKind.ROUTER)
